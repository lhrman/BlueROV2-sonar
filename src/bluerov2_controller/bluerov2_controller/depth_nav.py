#!/usr/bin/env python3
import math

import time

import rclpy
import json
from rclpy.node import Node
import bluerov2_controller.pid as pid

from bluerov2_interfaces.msg import Attitude, Bar30, PID
from bluerov2_interfaces.srv import CaptureImage


from std_msgs.msg import UInt16, Float64, Bool, String
from time import sleep

class Controller(Node):

    g   = 9.81      # m.s^-2 gravitational acceleration 
    p0  = 103425    # Surface pressure in Pascal
    rho = 1000      # kg/m^3  water density
    
    
    def __init__(self):
        super().__init__("depth_nav")    

        # Setup default parameters
        self.declare_parameter("depth_desired", 0.0)
        self.declare_parameter("depth_threshold", 0.1) 
        self.declare_parameter("depth_idle_time", 2.0) 
        self.declare_parameter("pwm_max", 1900)
        self.declare_parameter("pwm_neutral", 1500)

        self.declare_parameter("ki", 100)      
        self.declare_parameter("kp", 650)    
        self.declare_parameter("kd", 50)

        self.declare_parameter("roll_threshold", 0.3)
        self.declare_parameter("kp_r", 35)    
        self.declare_parameter("kd_r", 7.5)
        self.declare_parameter("roll_desired", 0) 
        self.declare_parameter("roll_pwm_max", 1750)
        

        self.declare_parameter("pitch_threshold", 0.2)
        self.declare_parameter("kp_p", 350)    
        self.declare_parameter("kd_p", 50)
        self.declare_parameter("pitch_desired", 0)

        self.declare_parameter("yaw_threshold", 0.25)
        self.declare_parameter("kp_y", 100)    
        self.declare_parameter("kd_y", 7)
        self.declare_parameter("yaw_desired", 270.0)
        self.declare_parameter("yaw_pwm_max", 1750)


        self.declare_parameter("enable", True) 

        self.attitude       = [0, 0, 0, 0, 0, 0] 
        self.depth_threshold= self.get_parameter("depth_threshold").value   # Threshold to consider desired depth reached       
        self.depth_desired  = self.get_parameter("depth_desired").value     # Desired depth setpoint
        self.bar30_data     = [0, 0, 0, 0]                                  # List to store Bar30 sensor data: [time_boot_ms, press_abs, press_diff, temperature]
        self.pwm_max        = self.get_parameter("pwm_max").value           # Maximum PWM value
        self.pwm_neutral    = self.get_parameter("pwm_neutral").value       # Neutral PWM value
        self.depth_idle_time= self.get_parameter("depth_idle_time").value   # Time in idle depth

        self.KI             = self.get_parameter("ki").value                # Integral gain constant
        self.KP             = self.get_parameter("kp").value                # Proportional gain constant
        self.KD             = self.get_parameter("kd").value                # Derivative gain constant
        
        self.roll_threshold = self.get_parameter("roll_threshold").value   # Threshold to consider desired roll reached       
        self.roll_desired       = pid.deg2rad(self.get_parameter("roll_desired").value)      # Desired roll setpoint
        self.KP_r           = self.get_parameter("kp_r").value              # Roll Proportional gain constant        
        self.KD_r           = self.get_parameter("kd_r").value              # Roll Derivative gain constant
        self.roll_pwm_max        = self.get_parameter("roll_pwm_max").value           # Maximum PWM value

        self.pitch_threshold = self.get_parameter("pitch_threshold").value   # Threshold to consider desired pitch reached
        self.pitch_desired      = pid.deg2rad(self.get_parameter("pitch_desired").value)     # Desired pitch setpoint       
        self.KP_p           = self.get_parameter("kp_p").value              # Pitch Proportional gain constant        
        self.KD_p           = self.get_parameter("kd_p").value              # Pitch Derivative gain constant

        self.yaw_threshold = self.get_parameter("yaw_threshold").value   # Threshold to consider desired yaw reached       
        self.yaw_desired       = pid.deg2rad(self.get_parameter("yaw_desired").value)     # Desired yaw setpoint
        self.KP_y           = self.get_parameter("kp_y").value              # Yaw Proportional gain constant        
        self.KD_y           = self.get_parameter("kd_y").value              # Yaw Derivative gain constant
        self.yaw_pwm_max        = self.get_parameter("yaw_pwm_max").value           # Maximum PWM value

        self.lateral_move = 100
        self.time_lateral_move = 2
        
        self.condition_met_time = None

        self.reverse = 1

        self.first_activation_r = False
        self.first_activation_p = False
        self.first_activation_y = False
        self.first_activation_d = False

        self.get_logger().info(f'self.KP: {self.KP:.2f}, self.KI: {self.KI:.2f}, self.KD: {self.KD:.2f},')

        self.time           = 0
        self.depth          = 0
        self.I_depth        = 0

        self.enable         = self.get_parameter("enable").value

        # Create subscriber
        self.attitude_sub       = self.create_subscription(Attitude, "/bluerov2/attitude", self.callback_att, 10)
        self.bar30_sub      = self.create_subscription(Bar30, "/bluerov2/bar30", self.callback_bar30, 10) 
        self.setDepth_sub   = self.create_subscription(Float64, "/settings/depth/set_depth", self.callback_set_depth, 10)
        self.setPID_sub     = self.create_subscription(PID, "/settings/depth/set_pid", self.callback_set_pid, 10) 
        self.setEnable_sub  = self.create_subscription(Bool, "/settings/depth/set_enable", self.callback_set_enable, 10) 

        # Create publisher
        self.throttle_pub   = self.create_publisher(UInt16, "/bluerov2/rc/throttle", 10) 
        self.depth_pub      = self.create_publisher(Float64, "/bluerov2/depth", 10)  
        self.status_pub     = self.create_publisher(String, '/settings/depth/status', 10)
        self.roll_pub           = self.create_publisher(UInt16, "/bluerov2/rc/roll", 10)
        self.pitch_pub          = self.create_publisher(UInt16, "/bluerov2/rc/pitch", 10)
        self.yaw_pub           = self.create_publisher(UInt16, "/bluerov2/rc/yaw", 10)

        self.lateral_pub           = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)

        # Create Service Client
        self.capture_image_client = self.create_client(CaptureImage, 'capture_image')
        while not self.capture_image_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service capture_image not available, waiting again...')
        self.req_capture_image = CaptureImage.Request()

        self.layer = 1 # tmp variable, waiting for underwater coordinates to be available: what layer depth was covered
        self.get_logger().info('controller has been successfully configured!')   
         

        # Start update loop
        self.create_timer(0.04, self.calculate_pwm)
        
        # Start depth adjustment loop
        # self.create_timer(5.0, self.adjust_depth)  # Timer to adjust depth every 3 seconds
    
    def send_capture_image_request(self, image_name):
        self.req_capture_image.image_name = image_name
        self.future = self.capture_image_client.call_async(self.req_capture_image)

    def callback_att(self, msg):       
        self.attitude = [msg.roll,
                         msg.pitch,
                         msg.yaw,
                         msg.rollspeed,
                         msg.pitchspeed,
                         msg.yawspeed]

    def callback_bar30(self, msg):
        """Read data from '/BlueRov2/bar30'

        ROS message:
        Header header
        uint32 time_boot_ms
        float64 press_abs
        float64 press_diff
        int16 temperature
        """
        self.bar30_data = [ msg.time_boot_ms,
                            msg.press_abs,
                            msg.press_diff,
                            msg.temperature ]
        
    def callback_set_pid(self, msg):
        """Read data from '/settings/depth/set_pid'

        ROS message:
        ------------        
        uint16 pwm_max 
        uint32 KI
        uint32 KP
        uint32 KD
        """
        if msg.pwm_max != 65535:
            if msg.pwm_max < 1500:
                self.pwm_max = 1500
            else:
                self.pwm_max = msg.pwm_max

        self.KP = msg.kp if not msg.kp == 65535 else self.KP
        self.KI = msg.ki if not msg.ki == 65535 else self.KI       
        self.KD = msg.kd if not msg.kd == 65535 else self.KD

    def callback_set_depth(self, msg): 
        """Read data from '/settings/depth/set_depth'

        ROS message:
        ------------        
        float64 data
        """          
        
        self.depth_desired = msg.data

    def callback_set_enable(self, msg):
        """Read data from '/settings/depth/set_enable'

        ROS message:
        ------------        
        bool data
        """             
        self.enable = msg.data

    def update_status(self):         
        msg = String()
        data = {}
        data["type"]            = "depth_nav"
        data["enable"]          = self.enable
        data["kp"]              = self.KP
        data["ki"]              = self.KI
        data["kd"]              = self.KD
        data["pwm_max"]         = self.pwm_max
        data["pwm_neutral"]     = self.pwm_neutral
        data["depth_desired"]   = self.depth_desired
        
        msg.data = json.dumps(data)
        self.status_pub.publish(msg)
        

    def control_depth(self, p):
        """PID controller
        Transform pressure to depth value
        Calulate the integrate value with euler method

        Input:
        ------
        p: absolute presssure in Pa

        Return:
        -------
        command calculated to reach the depth desired

        """
        depth       = -(p-self.p0)/(self.rho*self.g)
        delta_depth = depth - self.depth
        self.depth  = depth #current depth
        # self.get_logger().info(f'depth: {depth} desired: {self.depth_desired:.2f}, abs diff: {abs(self.depth_desired - depth):.2f}, thr: {self.depth_threshold}')
        if abs(self.depth_desired - depth) <= self.depth_threshold:
            self.get_logger().info(f'Reached {self.depth_desired:.2f}, (currently at {depth:.2f}) - hovering...')
            if (abs(self.attitude[0]-self.roll_desired)>self.roll_threshold) or (abs(self.attitude[1]-self.pitch_desired)>self.pitch_threshold):
                self.get_logger().info("roll and/or pitch control needed")
                # if hasattr(self, 'future') and self.future and not self.future.done():
                #     self.future.cancel()
            elif abs(self.attitude[2]-self.yaw_desired)>self.yaw_threshold:
                self.get_logger().info("yaw control needed")
                # if hasattr(self, 'future') and self.future and not self.future.done():
                #     self.future.cancel()
            else:
                if not hasattr(self, 'future') or self.future is None:
                    self.get_logger().info("Requesting image capture")
                    self.send_capture_image_request(f'layer_{self.layer:.2f}_depth_{depth:.2f}({self.depth_desired:.2f}+-{self.depth_threshold:.2f})')
                elif self.future.done():           
                    self.get_logger().info("future answer obtained")
                    response = self.future.result()
                    if response is not None:
                        self.get_logger().info(f'Response: {response}')
                        if response:
                            self.adjust_depth()
                        else:
                          self.get_logger().info('Negative Response: need to repeat it')  
                        self.future = None
                    else:
                        self.get_logger().info('Service call failed')
                        self.future = None
                else:
                    self.get_logger().info("waiting for an answer...")

        else:
            self.get_logger().info(f'Reaching {self.depth_desired:.2f}, currently at {depth:.2f}')
            # if hasattr(self, 'future') and self.future and not self.future.done():
                # self.future.cancel()
        # else:
        #     self.condition_met_time = None  

        delta_t     = (self.bar30_data[0] - self.time)/1000.
        self.time   = self.bar30_data[0]
        msg = Float64()
        msg.data = self.depth
        self.depth_pub.publish(msg)  
        if delta_t == 0:
            D_depth = 0
        else:
            D_depth = delta_depth/delta_t #derivative term 

        self.I_depth = (self.depth_desired-depth)*delta_t #integrate term
        u = self.KI*self.I_depth + self.KP*(self.depth_desired-depth) - self.KD*D_depth
        return u
    
    def control_roll(self, roll, rollspeed):
        roll_error = math.atan2(math.sin(roll - self.roll_desired), math.cos(roll - self.roll_desired))   
        self.get_logger().info(f'r_e: {roll_error:.2f}, kP_r*r_e: {self.KP_r*pid.sawtooth(roll_error):.2f}, KD_r*rs: {self.KD_r*rollspeed:.2f}')
        return self.KP_r*pid.sawtooth(roll_error) + self.KD_r*rollspeed  
    
    def control_pitch(self, pitch, pitchspeed):        
        return self.KP_p*pid.sawtooth(pitch-self.pitch_desired) + self.KD_p*pitchspeed 
    
    def control_yaw(self, yaw, yawspeed):
        yaw_error = math.atan2(math.sin(yaw - self.yaw_desired), math.cos(yaw - self.yaw_desired))
        # self.get_logger().info(f'y_e: {yaw_error:.2f}, kP_y*y_e: {self.KP_y*pid.sawtooth(yaw_error):.2f}, KD_y*ys: {self.KD_y*yawspeed:.2f}')
        
        return self.KP_y*pid.sawtooth(yaw_error) + self.KD_y*yawspeed 

    def calculate_pwm(self):  

        neutr_msg = UInt16()
        neutr_msg.data = self.pwm_neutral
        depth_msg = neutr_msg
        yaw_msg = neutr_msg
        pitch_msg = neutr_msg
        roll_msg = neutr_msg
        roll_msg.data = self.pwm_neutral # FIXME: why is this here?

        y_pwm = self.pwm_neutral # FIXME: understand why this needs to be initialized


        if self.enable:
            # mesured_pressure = self.bar30_data[1]*100 #to convert pressure from hPa to Pa
            # u = self.control_depth(mesured_pressure)
            # pwm = self.pwm_neutral + u
            # pwm = pid.saturation(pwm, self.pwm_neutral, self.pwm_max)
            # msg.data = pwm
            # self.throttle_pub.publish(msg)
            # self.roll_pub.publish(neutr_msg)
            # self.pitch_pub.publish(neutr_msg) 
            # self.update_status() 
            if (abs(self.attitude[0]-self.roll_desired)>self.roll_threshold) or (abs(self.attitude[1]-self.pitch_desired)>self.pitch_threshold):
                self.get_logger().info(f'roll or pitch')
                if abs(self.attitude[0]-self.roll_desired)>self.roll_threshold:
                    roll = self.attitude[0]
                    rollspeed = self.attitude[3]
                    r_u = self.control_roll(roll, rollspeed)
                    r_pwm = self.pwm_neutral - r_u
                    r_pwm = pid.saturation(r_pwm, self.pwm_neutral, self.roll_pwm_max)
                    roll_msg.data = r_pwm
                    self.first_activation_r = True
                    
                    self.get_logger().info(f'Adjusting roll: {roll:.2f}')
                else:
                    roll_msg.data = self.pwm_neutral 

                # if abs(self.attitude[1]-self.pitch_desired)>self.pitch_threshold:
                #     pitch = self.attitude[1]
                #     pitchspeed = self.attitude[4]
                #     p_u = self.control_pitch(pitch, pitchspeed)
                #     p_pwm = self.pwm_neutral - p_u
                #     p_pwm = pid.saturation(p_pwm, self.pwm_neutral, self.pwm_max)
                #     pitch_msg.data = p_pwm
                    
                #     self.get_logger().info(f'Adjusting pitch: {pitch:.2f}')
        
                if self.first_activation_r:
                    self.roll_pub.publish(roll_msg) 
                
                if self.first_activation_y:
                    self.yaw_pub.publish(neutr_msg)
                    self.first_activation_y = False
                
                self.throttle_pub.publish(neutr_msg)
            else:
                mesured_pressure = self.bar30_data[1]*100 #to convert pressure from hPa to Pa
                d_u = self.control_depth(mesured_pressure)
                d_pwm = self.pwm_neutral + d_u
                d_pwm = pid.saturation(d_pwm, self.pwm_neutral, self.pwm_max)
                depth_msg.data = d_pwm

                # self.get_logger().info(f'depth_msg.data: {depth_msg.data:.2f}')
                self.throttle_pub.publish(depth_msg)

                if abs(self.attitude[2]-self.yaw_desired)>self.yaw_threshold:
                    yaw = self.attitude[2]
                    yawspeed = self.attitude[5]
                    y_u = self.control_yaw(yaw, yawspeed)
                    y_pwm = self.pwm_neutral - y_u            
                    y_pwm = pid.saturation(y_pwm, self.pwm_neutral, self.yaw_pwm_max)
                    yaw_msg.data = y_pwm
                    self.first_activation_y = True
                    self.get_logger().info(f'Adjusting yaw: {yaw:.2f}, desired: {self.yaw_desired:.2f}')
                else:
                    yaw_msg.data = y_pwm 

                if self.first_activation_r:
                    self.roll_pub.publish(neutr_msg)
                    self.first_activation_r = False

                if self.first_activation_y:
                    self.yaw_pub.publish(yaw_msg)

        self.update_status()


    def adjust_depth(self):
        if(abs(self.depth - self.depth_desired) < self.depth_threshold): # useless check?
            min_depth = -1.5
            max_depth = 0
            depth_step = 0.15
            if self.reverse > 0:
                self.get_logger().info(f'reverse adjusting')
                if self.depth_desired > min_depth:
                    self.depth_desired -= depth_step
                    self.get_logger().info(f'Adjusting depth to {self.depth_desired:.2f} meters')
                else:
                    self.get_logger().info(f'Reached the minimum desired depth of {min_depth:.2f} meters, shifting right')
                    self.shift_right()
            else:
                self.get_logger().info(f'NOT reverse adjusting')
                if self.depth_desired < max_depth:
                    self.depth_desired += depth_step
                    self.get_logger().info(f'Adjusting depth to {self.depth_desired:.2f} meters')
                else:
                    self.get_logger().info(f'Reached the minimum desired depth of {max_depth:.2f} meters, shifting right')
                    self.shift_right()

        else:
            self.get_logger().info(f'Reaching {self.depth_desired:.2f}')

    def shift_right(self):
        lateral_msg = UInt16()
        lateral_msg.data = self.pwm_neutral + self.lateral_move
        start_time = time.time()
        while time.time() - start_time < self.time_lateral_move:
            self.lateral_pub.publish(lateral_msg)
            self.get_logger().info(f'moving right')
            time.sleep(0.1)
        
        lateral_msg.data = self.pwm_neutral
        self.lateral_pub.publish(lateral_msg)
        
        self.reverse = -self.reverse
        self.get_logger().info(f'self.reverse: {self.reverse}')
        if self.reverse > 0:
            self.get_logger().info(f'self.reverse(trrue): {self.reverse}')
            self.depth_desired = 0
        else:
            self.get_logger().info(f'self.reverse(false): {self.reverse}')
            self.depth_desired = -1.5
        
        self.get_logger().info(f'self.depth_desired: {self.depth_desired}')
        self.adjust_depth()
        self.layer +=1


        

def main(args=None):
    rclpy.init(args=args)    
    node = Controller()
    rclpy.spin(node)      
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
