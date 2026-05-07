#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from pymavlink import mavutil
import pymavlink.dialects.v20.ardupilotmega as mavlink

from std_msgs.msg import UInt16, Bool
from sensor_msgs.msg import BatteryState, Imu
from bluerov2_interfaces.msg import Attitude, Bar30
import math

class Controller(Node):
    
    def __init__(self):
        super().__init__("controller")              

        self.type               = mavlink.MAV_TYPE_GCS
        self.autopilot          = mavlink.MAV_AUTOPILOT_INVALID
        self.base_mode          = mavlink.MAV_MODE_PREFLIGHT
        self.custom_mode        = 0
        self.mavlink_version    = 0
        self.heartbeat_period   = 0.02

        self.pitch              = 1500
        self.roll               = 1500
        self.throttle           = 1500
        self.yaw                = 1500
        self.forward            = 1500
        self.lateral            = 1500
        self.camera_pan         = 1500
        self.camera_tilt        = 1500
        self.lights             = 1100

        self.data               = {}

        self.last_sys_status    = None
        self.last_battery_status= None
        self.last_bar30_data    = None
        
        # Create subscriber
        self.rc_pitch_sub       = self.create_subscription(UInt16, "/bluerov2/rc/pitch", lambda msg: self.rc_callback(msg, 1), 10)
        self.rc_roll_sub        = self.create_subscription(UInt16, "/bluerov2/rc/roll", lambda msg: self.rc_callback(msg, 2), 10)
        self.rc_throttle_sub    = self.create_subscription(UInt16, "/bluerov2/rc/throttle", lambda msg:  self.rc_callback(msg, 3), 10)
        self.rc_yaw_sub         = self.create_subscription(UInt16, "/bluerov2/rc/yaw", lambda msg: self.rc_callback(msg, 4), 10)
        self.rc_forward_sub     = self.create_subscription(UInt16, "/bluerov2/rc/forward", lambda msg: self.rc_callback(msg, 5), 10)
        self.rc_lateral_sub     = self.create_subscription(UInt16, "/bluerov2/rc/lateral", lambda msg: self.rc_callback(msg, 6), 10)
        self.rc_camera_pan_sub  = self.create_subscription(UInt16, "/bluerov2/rc/camera_pan", lambda msg: self.rc_callback(msg, 7), 10)
        self.rc_camera_tilt_sub = self.create_subscription(UInt16, "/bluerov2/rc/camera_tilt", lambda msg: self.rc_callback(msg, 8), 10)
        self.rc_lights_sub      = self.create_subscription(UInt16, "/bluerov2/rc/lights", lambda msg: self.rc_callback(msg, 9), 10)

        self.arm_sub            = self.create_subscription(Bool, "/bluerov2/arm", self.arm_callback, 10)
        
        # Create publisher
        self.battery_pub        = self.create_publisher(BatteryState, "/bluerov2/battery", 10)
        self.arm_pub            = self.create_publisher(Bool, "/bluerov2/arm_status", 10)  
        self.attitude_pub       = self.create_publisher(Attitude, "/bluerov2/attitude", 10)   
        self.bar30_pub          = self.create_publisher(Bar30, "/bluerov2/bar30", 10)
        self.imu_pub            = self.create_publisher(Imu, '/imu/data', 10)
        
        # Setup connection parameters
        self.declare_parameter("ip", "0.0.0.0") 
        self.declare_parameter("port", 14550)
        self.declare_parameter("baudrate", 115200)         

        self.bluerov_ip = self.get_parameter("ip").value
        self.bluerov_port = self.get_parameter("port").value  
        self.bluerov_baudrate = self.get_parameter("baudrate").value

        self.get_logger().info("Controller for bluerov2 was started successfully!")

        self.connection = mavutil.mavlink_connection("udpin:" + self.bluerov_ip + ":" + str(self.bluerov_port), baudrate=self.bluerov_baudrate)        
        
        self.get_logger().info("Connecting to BlueRov2...")
        self.connection.wait_heartbeat()
        self.get_logger().info("BlueRov2 connection successful!")       

        self.mav        = self.connection.mav
        self.recv_match = self.connection.recv_match
        self.target     = (self.connection.target_system,
                           self.connection.target_component)
        
        self.get_logger().info("Request data stream...") 
        self.mav.request_data_stream_send(self.connection.target_system, self.connection.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)
        
        self.arm()

        self.get_logger().info("Start sending heartbeat messages...")
        self.create_timer(self.heartbeat_period, self.send_bluerov_commands)
        

    def send_bluerov_commands(self):
        self.connection.mav.heartbeat_send(self.type, 
                                           self.autopilot, 
                                           self.base_mode, 
                                           self.custom_mode, 
                                           self.mavlink_version)
        
        rc_channel_values = (self.pitch, self.roll, self.throttle, self.yaw,
                             self.forward, self.lateral, self.camera_pan,
                             self.camera_tilt, self.lights)
        self.mav.rc_channels_override_send(*self.target, *rc_channel_values)

        # Read incoming MAVLink messages
        self.read_param()

        # Publish sensor data
        if len(self.data) != 0:
            self.decode_param()    

    def read_param(self):        
        msgs = []
        while True:
            msg = self.recv_match()
            if msg is not None:
                msgs.append(msg)
            else:
                break
        for msg in msgs:
            self.data[msg.get_type()] = msg.to_dict()        
            


    def decode_param(self):
        def get_data_from_cycle(key):
            if key not in self.data:
                return None
            return self.data[key]

        new_sys_status = get_data_from_cycle('SYS_STATUS')
        if new_sys_status:
            self.last_sys_status = new_sys_status

        new_battery_status = get_data_from_cycle('BATTERY_STATUS')
        if new_battery_status:
            self.last_battery_status = new_battery_status

        new_bar30_data = get_data_from_cycle('SCALED_PRESSURE2')
        if new_bar30_data:
            self.last_bar30_data = new_bar30_data

        # Publish Attitude
        attitude_data = get_data_from_cycle('ATTITUDE')
        if attitude_data is not None:
            msg = Attitude()
            msg.time_boot_ms = attitude_data['time_boot_ms']
            msg.roll, msg.pitch, msg.yaw = attitude_data['roll'], attitude_data['pitch'], attitude_data['yaw']
            msg.rollspeed, msg.pitchspeed, msg.yawspeed = attitude_data['rollspeed'], attitude_data['pitchspeed'], attitude_data['yawspeed']
            self.attitude_pub.publish(msg)

        # Publish IMU
        new_imu_data = get_data_from_cycle('RAW_IMU')
        if new_imu_data is not None:
            imu_msg = Imu()
            imu_msg.header.stamp = self.get_clock().now().to_msg()
            imu_msg.header.frame_id = 'base_link'

            imu_msg.linear_acceleration.x = new_imu_data['xacc'] * 9.81 / 1000.0
            imu_msg.linear_acceleration.y = new_imu_data['yacc'] * 9.81 / 1000.0
            imu_msg.linear_acceleration.z = new_imu_data['zacc'] * 9.81 / 1000.0

            imu_msg.angular_velocity.x = new_imu_data['xgyro'] / 1000.0
            imu_msg.angular_velocity.y = new_imu_data['ygyro'] / 1000.0
            imu_msg.angular_velocity.z = new_imu_data['zgyro'] / 1000.0

            if attitude_data is not None:
                cr = math.cos(attitude_data['roll']  * 0.5)
                sr = math.sin(attitude_data['roll']  * 0.5)
                cp = math.cos(attitude_data['pitch'] * 0.5)
                sp = math.sin(attitude_data['pitch'] * 0.5)
                cy = math.cos(attitude_data['yaw']   * 0.5)
                sy = math.sin(attitude_data['yaw']   * 0.5)

                imu_msg.orientation.w = cr * cp * cy + sr * sp * sy
                imu_msg.orientation.x = sr * cp * cy - cr * sp * sy
                imu_msg.orientation.y = cr * sp * cy + sr * cp * sy
                imu_msg.orientation.z = cr * cp * sy - sr * sp * cy

            self.imu_pub.publish(imu_msg)

        # Publish Bar30
        if self.last_bar30_data is not None:
            msg = Bar30()
            msg.time_boot_ms = self.last_bar30_data['time_boot_ms']
            msg.press_abs, msg.press_diff, msg.temperature = self.last_bar30_data['press_abs'], self.last_bar30_data['press_diff'], self.last_bar30_data['temperature']
            self.bar30_pub.publish(msg)

        # Publish Battery
        if self.last_sys_status is not None and self.last_battery_status is not None:
            bat = BatteryState()
            bat.voltage = self.last_sys_status['voltage_battery'] / 1000.0
            bat.current = self.last_sys_status['current_battery'] / 100.0
            bat.percentage = self.last_battery_status['battery_remaining'] / 100.0
            self.battery_pub.publish(bat)

    def arm(self):
        self.connection.arducopter_arm()
        self.get_logger().info('Arm requested, waiting...')
        self.connection.motors_armed_wait()
        self.get_logger().info('Thrusters armed!')

    def disarm(self):
        self.connection.arducopter_disarm()
        self.get_logger().info('Disarm requested, waiting...')
        self.connection.motors_disarmed_wait()
        self.get_logger().info('Thrusters disarmed')    

  
    def clear_motion(self):
        self.get_logger().info('Clearing motion...')
        self.pitch      = 1500
        self.roll       = 1500
        self.throttle   = 1500
        self.yaw        = 1500
        self.forward    = 1500
        self.lateral    = 1500
        self.camera_pan = 1500
        self.camera_tilt= 1500
        rc_channel_values = (self.pitch, self.roll, self.throttle, self.yaw,
                             self.forward, self.lateral, self.camera_pan,
                             self.camera_tilt, self.lights)
        self.mav.rc_channels_override_send(*self.target, *rc_channel_values)        

    def rc_callback(self, msg, topic):
        if topic == 1: self.pitch       = msg.data
        elif topic == 2: self.roll      = msg.data
        elif topic == 3: self.throttle  = msg.data
        elif topic == 4: self.yaw       = msg.data
        elif topic == 5: self.forward   = msg.data
        elif topic == 6: self.lateral   = msg.data
        elif topic == 7: self.camera_pan= msg.data
        elif topic == 8: self.camera_tilt= msg.data
        elif topic == 9: self.lights    = msg.data

    def arm_callback(self, msg):
        if msg.data:
            self.arm()
        else:
            self.disarm()


def main(args=None):
    rclpy.init(args=args)    
    node = Controller()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.clear_motion()
        node.disarm()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()