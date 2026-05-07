# #!/usr/bin/env python3
# import rclpy
# import json
# from rclpy.node import Node
# import bluerov2_controller.pid as pid

# from bluerov2_interfaces.msg import Bar30, PID
# from std_msgs.msg import UInt16, Float64, Bool, String

# class Controller(Node):

#     g   = 9.81      # m.s^-2 gravitational acceleration 
#     p0  = 103425    # Surface pressure in Pascal
#     rho = 1000      # kg/m^3  water density
    
#     def __init__(self):
#         super().__init__("depth_controller")    

#         # Setup default parameters
#         self.declare_parameter("depth_desired", 0.5) 
#         self.declare_parameter("pwm_max", 1900)
#         self.declare_parameter("pwm_neutral", 1500)
#         self.declare_parameter("ki", 100)      
#         self.declare_parameter("kp", 600)    
#         self.declare_parameter("kd", 50)    
#         self.declare_parameter("enable", True)        

#         self.depth_desired  = self.get_parameter("depth_desired").value     # Desired depth setpoint
#         self.bar30_data     = [0, 0, 0, 0]                                  # List to store Bar30 sensor data: [time_boot_ms, press_abs, press_diff, temperature]
#         self.pwm_max        = self.get_parameter("pwm_max").value           # Maximum PWM value
#         self.pwm_neutral    = self.get_parameter("pwm_neutral").value       # Neutral PWM value
#         self.KI             = self.get_parameter("ki").value                # Integral gain constant
#         self.KP             = self.get_parameter("kp").value                # Proportional gain constant
#         self.KD             = self.get_parameter("kd").value                # Derivative gain constant

#         self.time           = 0
#         self.depth          = 0
#         self.I_depth        = 0

#         self.enable         = self.get_parameter("enable").value

#         # Create subscriber
#         self.bar30_sub      = self.create_subscription(Bar30, "/bluerov2/bar30", self.callback_bar30, 10) 
#         self.setDepth_sub   = self.create_subscription(Float64, "/settings/depth/set_depth", self.callback_set_depth, 10)
#         self.setPID_sub     = self.create_subscription(PID, "/settings/depth/set_pid", self.callback_set_pid, 10) 
#         self.setEnable_sub  = self.create_subscription(Bool, "/settings/depth/set_enable", self.callback_set_enable, 10) 

#         # Create publisher
#         self.throttle_pub   = self.create_publisher(UInt16, "/bluerov2/rc/throttle", 10) 
#         self.depth_pub      = self.create_publisher(Float64, "/bluerov2/depth", 10)  
#         self.status_pub     = self.create_publisher(String, '/settings/depth/status', 10)

#         self.get_logger().info('controller has been successfully configured!')        

#         # Start update loop
#         self.create_timer(0.04, self.calculate_pwm)        

#     def callback_bar30(self, msg):
#         """Read data from '/BlueRov2/bar30'

#         ROS message:
#         Header header
#         uint32 time_boot_ms
#         float64 press_abs
#         float64 press_diff
#         int16 temperature
#         """
#         self.bar30_data = [ msg.time_boot_ms,
#                             msg.press_abs,
#                             msg.press_diff,
#                             msg.temperature ]
        
#     def callback_set_pid(self, msg):
#         """Read data from '/settings/depth/set_pid'

#         ROS message:
#         ------------        
#         uint16 pwm_max 
#         uint32 KI
#         uint32 KP
#         uint32 KD
#         """
#         if msg.pwm_max != 65535:
#             if msg.pwm_max < 1500:
#                 self.pwm_max = 1500
#             else:
#                 self.pwm_max = msg.pwm_max

#         self.KP = msg.kp if not msg.kp == 65535 else self.KP
#         self.KI = msg.ki if not msg.ki == 65535 else self.KI       
#         self.KD = msg.kd if not msg.kd == 65535 else self.KD

#     def callback_set_depth(self, msg): 
#         """Read data from '/settings/depth/set_depth'

#         ROS message:
#         ------------        
#         float64 data
#         """          
        
#         self.depth_desired = msg.data

#     def callback_set_enable(self, msg):
#         """Read data from '/settings/depth/set_enable'

#         ROS message:
#         ------------        
#         bool data
#         """             
#         self.enable = msg.data

#     def update_status(self):         
#         msg = String()
#         data = {}
#         data["type"]            = "depth_controller"
#         data["enable"]          = self.enable
#         data["kp"]              = self.KP
#         data["ki"]              = self.KI
#         data["kd"]              = self.KD
#         data["pwm_max"]         = self.pwm_max
#         data["pwm_neutral"]     = self.pwm_neutral
#         data["depth_desired"]   = self.depth_desired
        
#         msg.data = json.dumps(data)
#         self.status_pub.publish(msg)
        

#     def control_pid(self, p):
#         """PID controller
#         Transform pressure to depth value
#         Calulate the integrate value with euler method

#         Input:
#         ------
#         p: absolute presssure in Pa

#         Return:
#         -------
#         command calculated to reach the depth desired

#         """
#         depth       = -(p-self.p0)/(self.rho*self.g)
#         delta_depth = depth - self.depth
#         self.depth  = depth #current depth
#         delta_t     = (self.bar30_data[0] - self.time)/1000.
#         self.time   = self.bar30_data[0]
#         msg = Float64()
#         msg.data = self.depth
#         self.depth_pub.publish(msg)  
#         if delta_t == 0:
#             D_depth = 0
#         else:
#             D_depth = delta_depth/delta_t #derivative term 

#         self.I_depth = (self.depth_desired-depth)*delta_t #integrate term
#         u = self.KI*self.I_depth + self.KP*(self.depth_desired-depth) - self.KD*D_depth
#         return u   

#     def calculate_pwm(self):  
#         msg = UInt16()

#         if self.enable:
#             mesured_pressure = self.bar30_data[1]*100 #to convert pressure from hPa to Pa
#             u = self.control_pid(mesured_pressure)
#             pwm = self.pwm_neutral + u
#             pwm = pid.saturation(pwm, self.pwm_neutral, self.pwm_max)
            
#             msg.data = pwm
#         else:
#             msg.data = self.pwm_neutral        
            
#         self.throttle_pub.publish(msg)     
#         self.update_status()   

# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()
#     rclpy.spin(node)      
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

# #!/usr/bin/env python3
# import rclpy
# import json
# from rclpy.node import Node
# import bluerov2_controller.pid as pid

# from bluerov2_interfaces.msg import Bar30, PID
# from std_msgs.msg import UInt16, Float64, Bool, String

# class Controller(Node):

#     g   = 9.81      # m.s^-2 gravitational acceleration 
#     p0  = 103425    # Surface pressure in Pascal
#     rho = 1000      # kg/m^3  water density
    
#     def __init__(self):
#         super().__init__("depth_controller")    

#         # --- MODIFICATION START: Changed default values to floats by adding .0 ---
#         self.declare_parameter("depth_desired", 0.5) 
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_neutral", 1500.0)
#         self.declare_parameter("ki", 100.0)      
#         self.declare_parameter("kp", 600.0)    
#         self.declare_parameter("kd", 50.0)    
#         self.declare_parameter("enable", True)
#         # --- MODIFICATION END ---        

#         self.depth_desired  = self.get_parameter("depth_desired").value
#         self.bar30_data     = [0, 0, 0, 0]
#         self.pwm_max        = self.get_parameter("pwm_max").value
#         self.pwm_neutral    = self.get_parameter("pwm_neutral").value
#         self.KI             = self.get_parameter("ki").value
#         self.KP             = self.get_parameter("kp").value
#         self.KD             = self.get_parameter("kd").value

#         self.time           = 0
#         self.depth          = 0
#         self.I_depth        = 0

#         self.enable         = self.get_parameter("enable").value

#         # Create subscriber
#         self.bar30_sub      = self.create_subscription(Bar30, "/bluerov2/bar30", self.callback_bar30, 10) 
#         self.setDepth_sub   = self.create_subscription(Float64, "/settings/depth/set_depth", self.callback_set_depth, 10)
#         self.setPID_sub     = self.create_subscription(PID, "/settings/depth/set_pid", self.callback_set_pid, 10) 
#         self.setEnable_sub  = self.create_subscription(Bool, "/settings/depth/set_enable", self.callback_set_enable, 10) 

#         # Create publisher
#         self.throttle_pub   = self.create_publisher(UInt16, "/bluerov2/rc/throttle", 10) 
#         self.depth_pub      = self.create_publisher(Float64, "/bluerov2/depth", 10)  
#         self.status_pub     = self.create_publisher(String, '/settings/depth/status', 10)

#         self.get_logger().info('controller has been successfully configured!')        

#         # Start update loop
#         self.create_timer(0.04, self.calculate_pwm)        

#     def callback_bar30(self, msg):
#         self.bar30_data = [ msg.time_boot_ms,
#                             msg.press_abs,
#                             msg.press_diff,
#                             msg.temperature ]
        
#     def callback_set_pid(self, msg):
#         if msg.pwm_max != 65535:
#             if msg.pwm_max < 1500:
#                 self.pwm_max = 1500.0
#             else:
#                 self.pwm_max = float(msg.pwm_max)

#         self.KP = float(msg.kp) if not msg.kp == 65535 else self.KP
#         self.KI = float(msg.ki) if not msg.ki == 65535 else self.KI       
#         self.KD = float(msg.kd) if not msg.kd == 65535 else self.KD

#     def callback_set_depth(self, msg): 
#         self.depth_desired = msg.data

#     def callback_set_enable(self, msg):
#         self.enable = msg.data

#     def update_status(self):         
#         msg = String()
#         data = {}
#         data["type"]            = "depth_controller"
#         data["enable"]          = self.enable
#         data["kp"]              = self.KP
#         data["ki"]              = self.KI
#         data["kd"]              = self.KD
#         data["pwm_max"]         = self.pwm_max
#         data["pwm_neutral"]     = self.pwm_neutral
#         data["depth_desired"]   = self.depth_desired
        
#         msg.data = json.dumps(data)
#         self.status_pub.publish(msg)
        
#     def control_pid(self, p):
#         depth       = -(p-self.p0)/(self.rho*self.g)
#         delta_depth = depth - self.depth
#         self.depth  = depth #current depth
#         delta_t     = (self.bar30_data[0] - self.time)/1000.
#         self.time   = self.bar30_data[0]
#         msg = Float64()
#         msg.data = self.depth
#         self.depth_pub.publish(msg)  
#         if delta_t == 0:
#             D_depth = 0
#         else:
#             D_depth = delta_depth/delta_t #derivative term 

#         self.I_depth += (self.depth_desired-depth)*delta_t #integrate term
#         u = self.KI*self.I_depth + self.KP*(self.depth_desired-depth) - self.KD*D_depth
#         return u   

#     def calculate_pwm(self):  
#         msg = UInt16()

#         if self.enable:
#             mesured_pressure = self.bar30_data[1]*100 #to convert pressure from hPa to Pa
#             u = self.control_pid(mesured_pressure)
#             pwm = self.pwm_neutral + u
#             pwm = pid.saturation(pwm, self.pwm_neutral, self.pwm_max)
            
#             msg.data = int(pwm)
#         else:
#             self.I_depth = 0.0 # Reset integral term when disabled
#             msg.data = int(self.pwm_neutral)
            
#         self.throttle_pub.publish(msg)     
#         self.update_status()   

# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()
#     rclpy.spin(node)      
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

# #!/usr/bin/env python3
# import rclpy
# import json
# from rclpy.node import Node
# import bluerov2_controller.pid as pid

# from bluerov2_interfaces.msg import Bar30, PID
# from std_msgs.msg import UInt16, Float64, Bool, String

# class Controller(Node):

#     g   = 9.81      # m.s^-2 gravitational acceleration 
#     p0  = 103425    # Surface pressure in Pascal
#     rho = 1000      # kg/m^3  water density
    
#     def __init__(self):
#         super().__init__("depth_controller")    

#         # --- MODIFICATION START: Changed default depth to a safe 0.0 ---
#         self.declare_parameter("depth_desired", 0.0) 
#         # --- MODIFICATION END ---
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_neutral", 1500.0)
#         self.declare_parameter("ki", 100.0)      
#         self.declare_parameter("kp", 600.0)    
#         self.declare_parameter("kd", 50.0)    
#         self.declare_parameter("enable", True)

#         # ... (the rest of the file is unchanged) ...
#         self.depth_desired  = self.get_parameter("depth_desired").value
#         self.bar30_data     = [0, 0, 0, 0]
#         self.pwm_max        = self.get_parameter("pwm_max").value
#         self.pwm_neutral    = self.get_parameter("pwm_neutral").value
#         self.KI             = self.get_parameter("ki").value
#         self.KP             = self.get_parameter("kp").value
#         self.KD             = self.get_parameter("kd").value

#         self.time           = 0
#         self.depth          = 0
#         self.I_depth        = 0

#         self.enable         = self.get_parameter("enable").value

#         # Create subscriber
#         self.bar30_sub      = self.create_subscription(Bar30, "/bluerov2/bar30", self.callback_bar30, 10) 
#         self.setDepth_sub   = self.create_subscription(Float64, "/settings/depth/set_depth", self.callback_set_depth, 10)
#         self.setPID_sub     = self.create_subscription(PID, "/settings/depth/set_pid", self.callback_set_pid, 10) 
#         self.setEnable_sub  = self.create_subscription(Bool, "/settings/depth/set_enable", self.callback_set_enable, 10) 

#         # Create publisher
#         self.throttle_pub   = self.create_publisher(UInt16, "/bluerov2/rc/throttle", 10) 
#         self.depth_pub      = self.create_publisher(Float64, "/bluerov2/depth", 10)  
#         self.status_pub     = self.create_publisher(String, '/settings/depth/status', 10)

#         self.get_logger().info('controller has been successfully configured!')        

#         # Start update loop
#         self.create_timer(0.04, self.calculate_pwm)        

#     def callback_bar30(self, msg):
#         self.bar30_data = [ msg.time_boot_ms,
#                             msg.press_abs,
#                             msg.press_diff,
#                             msg.temperature ]
        
#     def callback_set_pid(self, msg):
#         if msg.pwm_max != 65535:
#             if msg.pwm_max < 1500:
#                 self.pwm_max = 1500.0
#             else:
#                 self.pwm_max = float(msg.pwm_max)

#         self.KP = float(msg.kp) if not msg.kp == 65535 else self.KP
#         self.KI = float(msg.ki) if not msg.ki == 65535 else self.KI       
#         self.KD = float(msg.kd) if not msg.kd == 65535 else self.KD

#     def callback_set_depth(self, msg): 
#         self.depth_desired = msg.data

#     def callback_set_enable(self, msg):
#         self.enable = msg.data

#     def update_status(self):         
#         msg = String()
#         data = {}
#         data["type"]            = "depth_controller"
#         data["enable"]          = self.enable
#         data["kp"]              = self.KP
#         data["ki"]              = self.KI
#         data["kd"]              = self.KD
#         data["pwm_max"]         = self.pwm_max
#         data["pwm_neutral"]     = self.pwm_neutral
#         data["depth_desired"]   = self.depth_desired
        
#         msg.data = json.dumps(data)
#         self.status_pub.publish(msg)
        
#     def control_pid(self, p):
#         depth       = -(p-self.p0)/(self.rho*self.g)
#         delta_depth = depth - self.depth
#         self.depth  = depth #current depth
#         delta_t     = (self.bar30_data[0] - self.time)/1000.
#         self.time   = self.bar30_data[0]
#         msg = Float64()
#         msg.data = self.depth
#         self.depth_pub.publish(msg)  
#         if delta_t == 0:
#             D_depth = 0
#         else:
#             D_depth = delta_depth/delta_t #derivative term 

#         self.I_depth += (self.depth_desired-depth)*delta_t #integrate term
#         u = self.KI*self.I_depth + self.KP*(self.depth_desired-depth) - self.KD*D_depth
#         return u   

#     def calculate_pwm(self):  
#         msg = UInt16()

#         if self.enable:
#             mesured_pressure = self.bar30_data[1]*100 #to convert pressure from hPa to Pa
#             u = self.control_pid(mesured_pressure)
#             pwm = self.pwm_neutral + u
#             pwm = pid.saturation(pwm, self.pwm_neutral, self.pwm_max)
            
#             msg.data = int(pwm)
#         else:
#             self.I_depth = 0.0 # Reset integral term when disabled
#             msg.data = int(self.pwm_neutral)
            
#         self.throttle_pub.publish(msg)     
#         self.update_status()   

# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()
#     rclpy.spin(node)      
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

# #!/usr/bin/env python3
# import rclpy
# import json
# from rclpy.node import Node
# import bluerov2_controller.pid as pid

# from bluerov2_interfaces.msg import Bar30, PID
# from std_msgs.msg import UInt16, Float64, Bool, String

# class Controller(Node):

#     g   = 9.81      # m.s^-2 gravitational acceleration 
#     p0  = 103425    # Surface pressure in Pascal
#     rho = 1000      # kg/m^3  water density
    
#     def __init__(self):
#         super().__init__("depth_controller")    

#         self.declare_parameter("depth_desired", 0.0) 
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_neutral", 1500.0)
#         self.declare_parameter("ki", 100.0)      
#         self.declare_parameter("kp", 600.0)    
#         self.declare_parameter("kd", 50.0)    
#         self.declare_parameter("enable", True)

#         self.depth_desired  = self.get_parameter("depth_desired").value
#         self.bar30_data     = [0, 0, 0, 0]
#         self.pwm_max        = self.get_parameter("pwm_max").value
#         self.pwm_neutral    = self.get_parameter("pwm_neutral").value
#         self.KI             = self.get_parameter("ki").value
#         self.KP             = self.get_parameter("kp").value
#         self.KD             = self.get_parameter("kd").value

#         self.time           = 0
#         self.depth          = 0
#         self.I_depth        = 0

#         self.enable         = self.get_parameter("enable").value
        
#         # --- MODIFICATION START: Add a flag to track if we have received sensor data ---
#         self.has_received_bar30 = False
#         # --- MODIFICATION END ---

#         # Create subscriber
#         self.bar30_sub      = self.create_subscription(Bar30, "/bluerov2/bar30", self.callback_bar30, 10) 
#         self.setDepth_sub   = self.create_subscription(Float64, "/settings/depth/set_depth", self.callback_set_depth, 10)
#         self.setPID_sub     = self.create_subscription(PID, "/settings/depth/set_pid", self.callback_set_pid, 10) 
#         self.setEnable_sub  = self.create_subscription(Bool, "/settings/depth/set_enable", self.callback_set_enable, 10) 

#         # Create publisher
#         self.throttle_pub   = self.create_publisher(UInt16, "/bluerov2/rc/throttle", 10) 
#         self.depth_pub      = self.create_publisher(Float64, "/bluerov2/depth", 10)  
#         self.status_pub     = self.create_publisher(String, '/settings/depth/status', 10)

#         self.get_logger().info('controller has been successfully configured!')        

#         # Start update loop
#         self.create_timer(0.04, self.calculate_pwm)        

#     def callback_bar30(self, msg):
#         self.bar30_data = [ msg.time_boot_ms,
#                             msg.press_abs,
#                             msg.press_diff,
#                             msg.temperature ]
#         # --- MODIFICATION START: Set the flag to True once we get the first message ---
#         if not self.has_received_bar30:
#             self.has_received_bar30 = True
#         # --- MODIFICATION END ---
        
#     def callback_set_pid(self, msg):
#         if msg.pwm_max != 65535:
#             if msg.pwm_max < 1500:
#                 self.pwm_max = 1500.0
#             else:
#                 self.pwm_max = float(msg.pwm_max)

#         self.KP = float(msg.kp) if not msg.kp == 65535 else self.KP
#         self.KI = float(msg.ki) if not msg.ki == 65535 else self.KI       
#         self.KD = float(msg.kd) if not msg.kd == 65535 else self.KD

#     def callback_set_depth(self, msg): 
#         self.depth_desired = msg.data

#     def callback_set_enable(self, msg):
#         # When enabling, reset the integral term to avoid sudden jumps
#         if msg.data is True and self.enable is False:
#              self.I_depth = 0.0
#         self.enable = msg.data

#     def update_status(self):         
#         msg = String()
#         data = {}
#         data["type"]            = "depth_controller"
#         data["enable"]          = self.enable
#         data["kp"]              = self.KP
#         data["ki"]              = self.KI
#         data["kd"]              = self.KD
#         data["pwm_max"]         = self.pwm_max
#         data["pwm_neutral"]     = self.pwm_neutral
#         data["depth_desired"]   = self.depth_desired
        
#         msg.data = json.dumps(data)
#         self.status_pub.publish(msg)
        
#     def control_pid(self, p):
#         depth       = -(p-self.p0)/(self.rho*self.g)
#         delta_depth = depth - self.depth
#         self.depth  = depth #current depth
#         delta_t     = (self.bar30_data[0] - self.time)/1000.
#         self.time   = self.bar30_data[0]
#         msg = Float64()
#         msg.data = self.depth
#         self.depth_pub.publish(msg)  
#         if delta_t == 0:
#             D_depth = 0
#         else:
#             D_depth = delta_depth/delta_t #derivative term 

#         self.I_depth += (self.depth_desired-depth)*delta_t #integrate term
#         u = self.KI*self.I_depth + self.KP*(self.depth_desired-depth) - self.KD*D_depth
#         return u   

#     def calculate_pwm(self):  
#         msg = UInt16()

#         # --- MODIFICATION START: Add has_received_bar30 to the safety check ---
#         if self.enable and self.has_received_bar30:
#         # --- MODIFICATION END ---
#             mesured_pressure = self.bar30_data[1]*100 #to convert pressure from hPa to Pa
#             u = self.control_pid(mesured_pressure)
#             pwm = self.pwm_neutral + u
#             pwm = pid.saturation(pwm, self.pwm_neutral, self.pwm_max)
            
#             msg.data = int(pwm)
#         else:
#             self.I_depth = 0.0 # Reset integral term when disabled
#             msg.data = int(self.pwm_neutral)
            
#         self.throttle_pub.publish(msg)     
#         self.update_status()   

# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()
#     rclpy.spin(node)      
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

#!/usr/bin/env python3
# --- FINAL VERSION WITH ROBUST p0 HANDLING ---
import rclpy
import json
from rclpy.node import Node
import bluerov2_controller.pid as pid

from bluerov2_interfaces.msg import Bar30, PID
from std_msgs.msg import UInt16, Float64, Bool, String
from std_srvs.srv import Trigger 

class Controller(Node):
    g = 9.81; rho = 1000
    
    def __init__(self):
        super().__init__("depth_controller")    
        self.declare_parameter("depth_desired", 0.0); self.declare_parameter("pwm_max", 1900.0)
        self.declare_parameter("pwm_neutral", 1500.0); self.declare_parameter("ki", 100.0)      
        self.declare_parameter("kp", 600.0); self.declare_parameter("kd", 50.0); self.declare_parameter("enable", True)
        self.depth_desired = self.get_parameter("depth_desired").value; self.bar30_data = [0, 0, 0, 0]
        self.pwm_max = self.get_parameter("pwm_max").value; self.pwm_neutral = self.get_parameter("pwm_neutral").value
        self.KI = self.get_parameter("ki").value; self.KP = self.get_parameter("kp").value; self.KD = self.get_parameter("kd").value
        self.time = 0; self.depth = 0; self.I_depth = 0; self.enable = self.get_parameter("enable").value
        self.p0 = None; self.has_received_bar30 = False

        self.bar30_sub = self.create_subscription(Bar30, "/bluerov2/bar30", self.callback_bar30, 10) 
        self.setDepth_sub = self.create_subscription(Float64, "/settings/depth/set_depth", self.callback_set_depth, 10)
        self.setPID_sub = self.create_subscription(PID, "/settings/depth/set_pid", self.callback_set_pid, 10) 
        self.setEnable_sub = self.create_subscription(Bool, "/settings/depth/set_enable", self.callback_set_enable, 10) 
        self.zero_depth_service = self.create_service(Trigger, '~/zero_depth', self.zero_depth_callback)
        self.throttle_pub = self.create_publisher(UInt16, "/bluerov2/rc/throttle", 10) 
        self.depth_pub = self.create_publisher(Float64, "/bluerov2/depth", 10)  
        self.status_pub = self.create_publisher(String, '/settings/depth/status', 10)
        self.get_logger().info('controller has been successfully configured!')        
        self.create_timer(0.04, self.calculate_pwm)        

    def zero_depth_callback(self, request, response):
        if self.has_received_bar30:
            current_pressure_pa = self.bar30_data[1] * 100.0
            self.p0 = current_pressure_pa 
            self.I_depth = 0.0
            self.get_logger().info(f"Depth zeroed. New surface pressure set to {self.p0:.2f} Pa.")
            response.success = True; response.message = "Depth zeroed successfully."
        else:
            self.get_logger().warn("Cannot zero depth, no pressure data received yet."); response.success = False; response.message = "No pressure data received."
        return response

    def callback_bar30(self, msg):
        self.bar30_data = [msg.time_boot_ms, msg.press_abs, msg.press_diff, msg.temperature]
        if not self.has_received_bar30:
            # --- MODIFICATION: Set p0 ONLY if it hasn't been set by the service call yet ---
            if self.p0 is None:
                self.p0 = self.bar30_data[1] * 100.0
                self.get_logger().info(f"Initial surface pressure calibrated to: {self.p0:.2f} Pa")
            # --- END MODIFICATION ---
            self.has_received_bar30 = True
    
    def callback_set_pid(self, msg):
        if msg.pwm_max != 65535: self.pwm_max = float(msg.pwm_max) if msg.pwm_max >= 1500 else 1500.0
        if not msg.kp == 65535: self.KP = float(msg.kp)
        if not msg.ki == 65535: self.KI = float(msg.ki)
        if not msg.kd == 65535: self.KD = float(msg.kd)

    def callback_set_depth(self, msg): 
        self.depth_desired = msg.data

    def callback_set_enable(self, msg):
        if msg.data is True and self.enable is False: self.I_depth = 0.0
        self.enable = msg.data

    def update_status(self):         
        # ... (unchanged) ...
        msg = String(); data = {}; data["type"] = "depth_controller"; data["enable"] = self.enable; data["kp"] = self.KP; data["ki"] = self.KI; data["kd"] = self.KD
        data["pwm_max"] = self.pwm_max; data["pwm_neutral"] = self.pwm_neutral; data["depth_desired"] = self.depth_desired; msg.data = json.dumps(data); self.status_pub.publish(msg)
        
    def control_pid(self, p, current_p0): # <-- Pass p0 in
        # --- MODIFICATION START: Use the passed-in p0, handle potential division by zero ---
        if self.rho * self.g == 0: return 0 # Avoid division by zero
        depth = -(p - current_p0) / (self.rho * self.g) 
        # --- MODIFICATION END ---
        
        delta_depth = depth - self.depth
        self.depth = depth
        delta_t = (self.bar30_data[0] - self.time) / 1000. if self.time != 0 else 0.04 # Estimate dt if first loop
        self.time = self.bar30_data[0]
        
        msg = Float64(); msg.data = self.depth; self.depth_pub.publish(msg)  
        D_depth = delta_depth / delta_t if delta_t != 0 else 0
        
        # Prevent integral windup when saturated or disabled
        error = self.depth_desired - depth
        if abs(self.KI * self.I_depth + self.KP * error - self.KD * D_depth) < (self.pwm_max - self.pwm_neutral):
             self.I_depth += error * delta_t
        
        # Clamp integral term to prevent extreme values (optional but good practice)
        max_integral = 100.0 # Adjust as needed
        self.I_depth = max(-max_integral, min(max_integral, self.I_depth))

        u = self.KI * self.I_depth + self.KP * error - self.KD * D_depth
        return u   

    def calculate_pwm(self):  
        msg = UInt16()
        # --- MODIFICATION START: Check p0 is valid HERE ---
        local_p0 = self.p0 # Capture current p0 value
        if self.enable and self.has_received_bar30 and local_p0 is not None:
        # --- MODIFICATION END ---
            mesured_pressure = self.bar30_data[1] * 100
            u = self.control_pid(mesured_pressure, local_p0) # <-- Pass p0
            pwm = self.pwm_neutral + u
            msg.data = int(pid.saturation(pwm, self.pwm_neutral, self.pwm_max))
        else:
            # If not enabled OR haven't received data OR p0 not set, send neutral and reset integral
            self.I_depth = 0.0 
            msg.data = int(self.pwm_neutral)
            if self.enable and not self.has_received_bar30:
                self.get_logger().debug("Depth control enabled but waiting for first Bar30 message.")
            elif self.enable and local_p0 is None:
                 self.get_logger().debug("Depth control enabled but surface pressure (p0) not calibrated yet.")

        self.throttle_pub.publish(msg)     
        self.update_status()   

def main(args=None):
    rclpy.init(args=args)    
    node = Controller()
    try: rclpy.spin(node)      
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()