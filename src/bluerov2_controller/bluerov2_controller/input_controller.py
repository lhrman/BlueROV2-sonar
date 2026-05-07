# #!/usr/bin/env python3
# import rclpy
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # Setup default parameters        
#         self.declare_parameter("pwm_max", 1900)
#         self.declare_parameter("pwm_min", 1100)
#         self.declare_parameter("pwm_neutral", 1500)        
#         self.declare_parameter("pwm_camera_max", 1900)
#         self.declare_parameter("pwm_camera_min", 1100)
#         self.declare_parameter("pwm_lights_max", 1900)
#         self.declare_parameter("pwm_lights_min", 1100)
#         self.declare_parameter("gain_pwm_cam", 400)     
#         self.declare_parameter("gain_pwm_lights", 50)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("gain_yaw", 3)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)

#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 

#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 

#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    

#         self.debug                  = self.get_parameter("debug").value   

#         # Node status
#         self.depth_status           = None
#         self.yaw_status             = None

#         # Create publisher
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              

#         # Create subscriber
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               

#         # Clear BlueRov status
#         lights = UInt16()
#         lights.data = self.pwm_lights_min
#         self.lights_pub.publish(lights)

#         arm_msg = Bool()
#         arm_msg.data = self.arm
#         self.arm_pub.publish(arm_msg)

#         cam_pwm = UInt16()
#         cam_pwm.data = self.pwm_neutral
#         self.camera_tilt_pub.publish(cam_pwm)        

#         # Init Gamepad
#         pygame.init()        
#         self.joysticks = []

#         for i in range(0, pygame.joystick.get_count()):
#             # create an Joystick object in our list
#             self.joysticks.append(pygame.joystick.Joystick(i))
#             # initialize the appended joystick (-1 means last array item)
#             self.joysticks[-1].init()
#             # print a statement telling what the name of the controller is
#             self.get_logger().info("Detected joystick")        

#         # Start update loop
#         self.create_timer(0.04, self.update_input)
        

#     def update_input(self):
#         if (self.depth_status is not None and self.yaw_status is not None) or self.debug:
#             for event in pygame.event.get():            
#                 # Check if a joystick button was pressed
#                 if event.type == JOYBUTTONDOWN:
#                     if event.button == 4:       # Left Bumper (LB)
#                         self.adjust_lights("down")  
#                     elif event.button == 5:     # Right Bumper (RB)
#                         self.adjust_lights("up")  
#                     elif event.button == 7:     # Start Button
#                         self.arm_disarm()   
#                     elif event.button == 3:     # Y Button
#                         self.dive_up()  
#                     elif event.button == 0:     # A Button
#                         self.dive_down()  

#                  # Check if a joystick axis motion event occurs
#                 elif event.type == JOYAXISMOTION:                     
#                     if event.axis == 0 or event.axis == 1:    # Left Joystick motion
#                         self.move_event(event)  

#                 # Check if a joystick hat motion event occurs
#                 elif event.type == JOYHATMOTION:
#                     self.camera_tilt_event(event.value)         # D-Pad Up-Down motion

#             # Update rotation event with right joystick motion data
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))    
#         else:
#             self.get_logger().error("Attempt to establish a connection to the controllers failed.")     

#     def adjust_lights(self, direction):
#         msg = UInt16()
        
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = max(target_value, self.pwm_lights_min)
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = min(target_value, self.pwm_lights_max)            
        
#         self.lights_value = msg.data
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16()
#         value = value[1]

#         if value == 1:
#             msg.data = int(self.pwm_camera_max)
#         elif value == -1:
#             msg.data = int(self.pwm_camera_min)
#         else:
#             msg.data = int(self.pwm_neutral)
        
#         self.camera_tilt_pub.publish(msg)

#     def rotation_event(self, value):
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16()        
#         msg.data = round(new_yaw) 
#         self.yaw_controller_pub.publish(msg)            

#     def move_event(self, event):
#         u = event.value
#         pwm = UInt16(data=self.calculate_pwm(u))        

#         if event.axis == 0:
#             self.forward_pub.publish(pwm)
#         else:
#            self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         value = max(-1, min(1, value))
#         return int(self.pwm_neutral + value * (self.pwm_max - self.pwm_neutral))
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool()
#         msg.data = self.arm
#         self.arm_pub.publish(msg)
#         if self.arm:
#             self.get_logger().info("The ROV ist now armed!")
#         else:
#             self.get_logger().info("The ROV ist now disarmed!")

#     def dive_up(self):
#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
        
#         if new_depth <= 0:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")


#     def dive_down(self):
#         new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
        
#         if new_depth > -200:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def callback_node_status(self, msg):        
#         data = json.loads(msg.data)
        
#         match data["type"]:
#             case "depth_controller": self.depth_status = data   
#             case "yaw_controller": self.yaw_status = data     
            
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
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # Setup default parameters        
#         self.declare_parameter("pwm_max", 1900)
#         self.declare_parameter("pwm_min", 1100)
#         self.declare_parameter("pwm_neutral", 1500)        
#         self.declare_parameter("pwm_camera_max", 1900)
#         self.declare_parameter("pwm_camera_min", 1100)
#         self.declare_parameter("pwm_lights_max", 1900)
#         self.declare_parameter("pwm_lights_min", 1100)
#         self.declare_parameter("gain_pwm_cam", 400)     
#         self.declare_parameter("gain_pwm_lights", 50)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("gain_yaw", 3)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)

#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 

#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 

#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    

#         self.debug                  = self.get_parameter("debug").value   

#         # Node status
#         self.depth_status           = None
#         self.yaw_status             = None

#         # Create publisher
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              

#         # Create subscriber
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               

#         # Clear BlueRov status
#         lights = UInt16()
#         lights.data = self.pwm_lights_min
#         self.lights_pub.publish(lights)

#         arm_msg = Bool()
#         arm_msg.data = self.arm
#         self.arm_pub.publish(arm_msg)

#         cam_pwm = UInt16()
#         cam_pwm.data = self.pwm_neutral
#         self.camera_tilt_pub.publish(cam_pwm)        

#         # Init Gamepad
#         pygame.init()        
#         self.joysticks = []

#         for i in range(0, pygame.joystick.get_count()):
#             self.joysticks.append(pygame.joystick.Joystick(i))
#             self.joysticks[-1].init()
#             self.get_logger().info("Detected joystick")        

#         # Start update loop
#         self.create_timer(0.04, self.update_input)
        
#     # --- MODIFICATION START: Removed the faulty if/else check ---
#     def update_input(self):
#         # Always process pygame events
#         for event in pygame.event.get():            
#             # Check if a joystick button was pressed
#             if event.type == JOYBUTTONDOWN:
#                 if event.button == 4:       # Left Bumper (LB)
#                     self.adjust_lights("down")  
#                 elif event.button == 5:     # Right Bumper (RB)
#                     self.adjust_lights("up")  
#                 elif event.button == 7:     # Start Button
#                     self.arm_disarm()   
#                 elif event.button == 3:     # Y Button
#                     self.dive_up()  
#                 elif event.button == 0:     # A Button
#                     self.dive_down()  

#              # Check if a joystick axis motion event occurs
#             elif event.type == JOYAXISMOTION:                     
#                 if event.axis == 0 or event.axis == 1:    # Left Joystick motion
#                     self.move_event(event)  

#             # Check if a joystick hat motion event occurs
#             elif event.type == JOYHATMOTION:
#                 self.camera_tilt_event(event.value)         # D-Pad Up-Down motion

#         # Update rotation event with right joystick motion data
#         # Check if joystick is available before getting axis
#         if pygame.joystick.get_count() > 0:
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))
#     # --- MODIFICATION END ---   

#     def adjust_lights(self, direction):
#         msg = UInt16()
        
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = max(target_value, self.pwm_lights_min)
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = min(target_value, self.pwm_lights_max)            
        
#         self.lights_value = msg.data
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16()
#         value = value[1]

#         if value == 1:
#             msg.data = int(self.pwm_camera_max)
#         elif value == -1:
#             msg.data = int(self.pwm_camera_min)
#         else:
#             msg.data = int(self.pwm_neutral)
        
#         self.camera_tilt_pub.publish(msg)

#     # --- MODIFICATION START: Added a check for yaw_status ---
#     def rotation_event(self, value):
#         # Only adjust yaw setpoint if the yaw controller is active
#         if self.yaw_status is None:
#             return
            
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16()        
#         msg.data = round(new_yaw) 
#         self.yaw_controller_pub.publish(msg)            
#     # --- MODIFICATION END ---

#     def move_event(self, event):
#         u = event.value
#         # Invert the vertical axis for standard joystick behavior (up is forward)
#         if event.axis == 1:
#             u = -u
        
#         pwm = UInt16(data=self.calculate_pwm(u))

#         if event.axis == 1: # Vertical axis now controls forward/backward
#             self.forward_pub.publish(pwm)
#         elif event.axis == 0: # Horizontal axis now controls lateral
#            self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         value = max(-1, min(1, value))
#         return int(self.pwm_neutral + value * (self.pwm_max - self.pwm_neutral))
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool()
#         msg.data = self.arm
#         self.arm_pub.publish(msg)
#         if self.arm:
#             self.get_logger().info("The ROV is now armed!")
#         else:
#             self.get_logger().info("The ROV is now disarmed!")

#     # --- MODIFICATION START: Added a check for depth_status ---
#     def dive_up(self):
#         # Only adjust depth setpoint if the depth controller is active
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return

#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
        
#         if new_depth <= 0:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")
#     # --- MODIFICATION END ---

#     # --- MODIFICATION START: Added a check for depth_status ---
#     def dive_down(self):
#         # Only adjust depth setpoint if the depth controller is active
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return

#         new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
        
#         if new_depth > -200:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")
#     # --- MODIFICATION END ---

#     def callback_node_status(self, msg):        
#         data = json.loads(msg.data)
        
#         match data["type"]:
#             case "depth_controller": self.depth_status = data   
#             case "yaw_controller": self.yaw_status = data     
            
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
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # --- MODIFICATION START: Changed default values to floats by adding .0 ---
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_min", 1100.0)
#         self.declare_parameter("pwm_neutral", 1500.0)        
#         self.declare_parameter("pwm_camera_max", 1900.0)
#         self.declare_parameter("pwm_camera_min", 1100.0)
#         self.declare_parameter("pwm_lights_max", 1900.0)
#         self.declare_parameter("pwm_lights_min", 1100.0)
#         self.declare_parameter("gain_pwm_cam", 400.0)     
#         self.declare_parameter("gain_pwm_lights", 50.0)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("gain_yaw", 3.0)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)
#         # --- MODIFICATION END ---

#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 

#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 

#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    

#         self.debug                  = self.get_parameter("debug").value   

#         # Node status
#         self.depth_status           = None
#         self.yaw_status             = None

#         # Create publisher
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              

#         # Create subscriber
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               

#         # Clear BlueRov status
#         lights = UInt16()
#         lights.data = int(self.pwm_lights_min)
#         self.lights_pub.publish(lights)

#         arm_msg = Bool()
#         arm_msg.data = self.arm
#         self.arm_pub.publish(arm_msg)

#         cam_pwm = UInt16()
#         cam_pwm.data = int(self.pwm_neutral)
#         self.camera_tilt_pub.publish(cam_pwm)        

#         # Init Gamepad
#         pygame.init()        
#         self.joysticks = []

#         for i in range(0, pygame.joystick.get_count()):
#             self.joysticks.append(pygame.joystick.Joystick(i))
#             self.joysticks[-1].init()
#             self.get_logger().info("Detected joystick")        

#         # Start update loop
#         self.create_timer(0.04, self.update_input)
        
#     def update_input(self):
#         # Always process pygame events
#         for event in pygame.event.get():            
#             # Check if a joystick button was pressed
#             if event.type == JOYBUTTONDOWN:
#                 if event.button == 4:       # Left Bumper (LB)
#                     self.adjust_lights("down")  
#                 elif event.button == 5:     # Right Bumper (RB)
#                     self.adjust_lights("up")  
#                 elif event.button == 7:     # Start Button
#                     self.arm_disarm()   
#                 elif event.button == 3:     # Y Button
#                     self.dive_up()  
#                 elif event.button == 0:     # A Button
#                     self.dive_down()  

#              # Check if a joystick axis motion event occurs
#             elif event.type == JOYAXISMOTION:                     
#                 if event.axis == 0 or event.axis == 1:    # Left Joystick motion
#                     self.move_event(event)  

#             # Check if a joystick hat motion event occurs
#             elif event.type == JOYHATMOTION:
#                 self.camera_tilt_event(event.value)         # D-Pad Up-Down motion

#         # Update rotation event with right joystick motion data
#         # Check if joystick is available before getting axis
#         if pygame.joystick.get_count() > 0:
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))

#     def adjust_lights(self, direction):
#         msg = UInt16()
        
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = int(max(target_value, self.pwm_lights_min))
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = int(min(target_value, self.pwm_lights_max))          
        
#         self.lights_value = float(msg.data)
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16()
#         value = value[1]

#         if value == 1:
#             msg.data = int(self.pwm_camera_max)
#         elif value == -1:
#             msg.data = int(self.pwm_camera_min)
#         else:
#             msg.data = int(self.pwm_neutral)
        
#         self.camera_tilt_pub.publish(msg)

#     def rotation_event(self, value):
#         # Only adjust yaw setpoint if the yaw controller is active
#         if self.yaw_status is None:
#             return
            
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16()        
#         msg.data = round(new_yaw) 
#         self.yaw_controller_pub.publish(msg)            

#     def move_event(self, event):
#         u = event.value
#         # Invert the vertical axis for standard joystick behavior (up is forward)
#         if event.axis == 1:
#             u = -u
        
#         pwm = UInt16(data=self.calculate_pwm(u))

#         if event.axis == 1: # Vertical axis now controls forward/backward
#             self.forward_pub.publish(pwm)
#         elif event.axis == 0: # Horizontal axis now controls lateral
#            self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         value = max(-1, min(1, value))
#         return int(self.pwm_neutral + value * (self.pwm_max - self.pwm_neutral))
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool()
#         msg.data = self.arm
#         self.arm_pub.publish(msg)
#         if self.arm:
#             self.get_logger().info("The ROV is now armed!")
#         else:
#             self.get_logger().info("The ROV is now disarmed!")

#     def dive_up(self):
#         # Only adjust depth setpoint if the depth controller is active
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return

#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
        
#         if new_depth <= 0:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def dive_down(self):
#         # Only adjust depth setpoint if the depth controller is active
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return

#         new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
        
#         if new_depth > -200:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def callback_node_status(self, msg):        
#         data = json.loads(msg.data)
        
#         match data["type"]:
#             case "depth_controller": self.depth_status = data   
#             case "yaw_controller": self.yaw_status = data     
            
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
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # --- MODIFICATION START: Increased yaw gain for better response ---
#         self.declare_parameter("gain_yaw", 40.0)
#         # --- MODIFICATION END ---
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_min", 1100.0)
#         self.declare_parameter("pwm_neutral", 1500.0)        
#         self.declare_parameter("pwm_camera_max", 1900.0)
#         self.declare_parameter("pwm_camera_min", 1100.0)
#         self.declare_parameter("pwm_lights_max", 1900.0)
#         self.declare_parameter("pwm_lights_min", 1100.0)
#         self.declare_parameter("gain_pwm_cam", 400.0)     
#         self.declare_parameter("gain_pwm_lights", 50.0)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)

#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 

#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 

#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    

#         self.debug                  = self.get_parameter("debug").value   

#         # Node status
#         self.depth_status           = None
#         self.yaw_status             = None

#         # ... (the rest of __init__ is unchanged) ...
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               
#         lights = UInt16()
#         lights.data = int(self.pwm_lights_min)
#         self.lights_pub.publish(lights)
#         arm_msg = Bool()
#         arm_msg.data = self.arm
#         self.arm_pub.publish(arm_msg)
#         cam_pwm = UInt16()
#         cam_pwm.data = int(self.pwm_neutral)
#         self.camera_tilt_pub.publish(cam_pwm)        
#         pygame.init()        
#         self.joysticks = []
#         for i in range(0, pygame.joystick.get_count()):
#             self.joysticks.append(pygame.joystick.Joystick(i))
#             self.joysticks[-1].init()
#             self.get_logger().info("Detected joystick")        
#         self.create_timer(0.04, self.update_input)
        
#     def update_input(self):
#         for event in pygame.event.get():            
#             if event.type == JOYBUTTONDOWN:
#                 if event.button == 4:
#                     self.adjust_lights("down")  
#                 elif event.button == 5:
#                     self.adjust_lights("up")  
#                 elif event.button == 7:
#                     self.arm_disarm()   
#                 elif event.button == 3:
#                     self.dive_up()  
#                 elif event.button == 0:
#                     self.dive_down()  
#             elif event.type == JOYAXISMOTION:                     
#                 if event.axis == 0 or event.axis == 1:
#                     self.move_event(event)  
#             elif event.type == JOYHATMOTION:
#                 self.camera_tilt_event(event.value)
#         if pygame.joystick.get_count() > 0:
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))

#     def adjust_lights(self, direction):
#         msg = UInt16()
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = int(max(target_value, self.pwm_lights_min))
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = int(min(target_value, self.pwm_lights_max))          
#         self.lights_value = float(msg.data)
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16()
#         value = value[1]
#         if value == 1:
#             msg.data = int(self.pwm_camera_max)
#         elif value == -1:
#             msg.data = int(self.pwm_camera_min)
#         else:
#             msg.data = int(self.pwm_neutral)
#         self.camera_tilt_pub.publish(msg)

#     def rotation_event(self, value):
#         if self.yaw_status is None:
#             return
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16()        
#         msg.data = round(new_yaw) 
#         self.yaw_controller_pub.publish(msg)            

#     def move_event(self, event):
#         u = event.value
#         if event.axis == 1:
#             u = -u
#         pwm = UInt16(data=self.calculate_pwm(u))
#         if event.axis == 1:
#             self.forward_pub.publish(pwm)
#         elif event.axis == 0:
#            self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         value = max(-1, min(1, value))
#         return int(self.pwm_neutral + value * (self.pwm_max - self.pwm_neutral))
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool()
#         msg.data = self.arm
#         self.arm_pub.publish(msg)
#         if self.arm:
#             self.get_logger().info("The ROV is now armed!")
#         else:
#             self.get_logger().info("The ROV is now disarmed!")

#     # --- MODIFICATION START: Removed the faulty if statement ---
#     def dive_up(self):
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return

#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
        
#         # The faulty "if new_depth <= 0:" check has been removed.
#         # We add a new safety check to prevent setting depth too far above the surface.
#         if new_depth > 0.5:
#             self.get_logger().warn(f"Cannot set depth above 0.5m. Capping at {self.depth_status['depth_desired']:.2f}m.")
#             return

#         msg = Float64()
#         msg.data = new_depth
#         self.depth_controller_pub.publish(msg)
#         self.get_logger().info(f"Desired depth is now {new_depth}")
#     # --- MODIFICATION END ---

#     def dive_down(self):
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return
#         new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
#         if new_depth > -200:            
#             msg = Float64()
#             msg.data = new_depth
#             self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def callback_node_status(self, msg):        
#         data = json.loads(msg.data)
#         match data["type"]:
#             case "depth_controller": self.depth_status = data   
#             case "yaw_controller": self.yaw_status = data     
            
# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()    
#     rclpy.spin(node)      
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

# #!/usr/bin/env python3
# # --- THIS IS THE FINAL CORRECTED VERSION ---

# import rclpy
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # Declare all parameters with correct float types
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_min", 1100.0)
#         self.declare_parameter("pwm_neutral", 1500.0)        
#         self.declare_parameter("pwm_camera_max", 1900.0)
#         self.declare_parameter("pwm_camera_min", 1100.0)
#         self.declare_parameter("pwm_lights_max", 1900.0)
#         self.declare_parameter("pwm_lights_min", 1100.0)
#         self.declare_parameter("gain_pwm_cam", 400.0)     
#         self.declare_parameter("gain_pwm_lights", 50.0)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("gain_yaw", 40.0)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)
#         # --- THIS IS THE NEW PARAMETER ---
#         self.declare_parameter("max_rise", 0.5) # Default max rise of 0.5m

#         # Get all parameter values
#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 
#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 
#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    
#         self.debug                  = self.get_parameter("debug").value
#         # --- THIS IS THE NEW PARAMETER VALUE ---
#         self.max_rise               = self.get_parameter("max_rise").value
        
#         # --- THIS IS THE DEBUG LINE ---
#         self.get_logger().info(f"--- MAX RISE PARAMETER LOADED: {self.max_rise} ---")

#         # Node status
#         self.depth_status           = None
#         self.yaw_status             = None

#         # Create publishers and subscribers
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               

#         # ... (rest of __init__ is unchanged) ...
#         lights = UInt16(); lights.data = int(self.pwm_lights_min); self.lights_pub.publish(lights)
#         arm_msg = Bool(); arm_msg.data = self.arm; self.arm_pub.publish(arm_msg)
#         cam_pwm = UInt16(); cam_pwm.data = int(self.pwm_neutral); self.camera_tilt_pub.publish(cam_pwm)        
#         pygame.init(); self.joysticks = []
#         for i in range(0, pygame.joystick.get_count()):
#             self.joysticks.append(pygame.joystick.Joystick(i)); self.joysticks[-1].init()
#             self.get_logger().info("Detected joystick")        
#         self.create_timer(0.04, self.update_input)
        
#     def update_input(self):
#         # ... (this function is unchanged from the last good version) ...
#         for event in pygame.event.get():            
#             if event.type == JOYBUTTONDOWN:
#                 if event.button == 4: self.adjust_lights("down")  
#                 elif event.button == 5: self.adjust_lights("up")  
#                 elif event.button == 7: self.arm_disarm()   
#                 elif event.button == 3: self.dive_up()  
#                 elif event.button == 0: self.dive_down()  
#             elif event.type == JOYAXISMOTION:                     
#                 if event.axis == 0 or event.axis == 1: self.move_event(event)  
#             elif event.type == JOYHATMOTION:
#                 self.camera_tilt_event(event.value)
#         if pygame.joystick.get_count() > 0:
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))

#     # --- THIS IS THE CORRECTED dive_up FUNCTION ---
#     def dive_up(self):
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return

#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
        
#         # Use the configurable max_rise parameter for the safety check
#         if new_depth > self.max_rise:
#             self.get_logger().warn(f"Cannot set depth above {self.max_rise}m. Capping at {self.depth_status['depth_desired']:.2f}m.")
#             return

#         msg = Float64()
#         msg.data = new_depth
#         self.depth_controller_pub.publish(msg)
#         self.get_logger().info(f"Desired depth is now {new_depth}")

#     # ... (all other functions are unchanged from the last good version) ...
#     def adjust_lights(self, direction):
#         msg = UInt16()
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = int(max(target_value, self.pwm_lights_min))
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = int(min(target_value, self.pwm_lights_max))          
#         self.lights_value = float(msg.data)
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16(); value = value[1]
#         if value == 1: msg.data = int(self.pwm_camera_max)
#         elif value == -1: msg.data = int(self.pwm_camera_min)
#         else: msg.data = int(self.pwm_neutral)
#         self.camera_tilt_pub.publish(msg)

#     def rotation_event(self, value):
#         if self.yaw_status is None: return
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16(); msg.data = round(new_yaw); self.yaw_controller_pub.publish(msg)            

#     def move_event(self, event):
#         u = event.value
#         if event.axis == 1: u = -u
#         pwm = UInt16(data=self.calculate_pwm(u))
#         if event.axis == 1: self.forward_pub.publish(pwm)
#         elif event.axis == 0: self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         value = max(-1, min(1, value))
#         return int(self.pwm_neutral + value * (self.pwm_max - self.pwm_neutral))
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool(); msg.data = self.arm; self.arm_pub.publish(msg)
#         if self.arm: self.get_logger().info("The ROV is now armed!")
#         else: self.get_logger().info("The ROV is now disarmed!")

#     def dive_down(self):
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return
#         new_depth = round(self.depth_status["desired_depth"] - self.gain_depth, 2)
#         if new_depth > -200:            
#             msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def callback_node_status(self, msg):        
#         data = json.loads(msg.data)
#         if data["type"] == "depth_controller": self.depth_status = data   
#         elif data["type"] == "yaw_controller": self.yaw_status = data     
            
# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()    
#     rclpy.spin(node)      
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()

# #!/usr/bin/env python3
# # --- THIS IS THE FINAL, COMPLETE AND CORRECTED VERSION ---

# import rclpy
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # Declare all parameters with correct float types
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_min", 1100.0)
#         self.declare_parameter("pwm_neutral", 1500.0)        
#         self.declare_parameter("pwm_camera_max", 1900.0)
#         self.declare_parameter("pwm_camera_min", 1100.0)
#         self.declare_parameter("pwm_lights_max", 1900.0)
#         self.declare_parameter("pwm_lights_min", 1100.0)
#         self.declare_parameter("gain_pwm_cam", 400.0)     
#         self.declare_parameter("gain_pwm_lights", 50.0)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("gain_yaw", 40.0)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)
#         self.declare_parameter("max_rise", 0.5) # Default max rise of 0.5m

#         # Get all parameter values
#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 
#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 
#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    
#         self.debug                  = self.get_parameter("debug").value
#         self.max_rise               = self.get_parameter("max_rise").value
        
#         self.get_logger().info(f"--- MAX RISE PARAMETER LOADED: {self.max_rise} ---")

#         # Node status
#         self.depth_status           = None
#         self.yaw_status             = None

#         # Create publishers and subscribers
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               

#         # Clear BlueRov status
#         lights = UInt16(); lights.data = int(self.pwm_lights_min); self.lights_pub.publish(lights)
#         arm_msg = Bool(); arm_msg.data = self.arm; self.arm_pub.publish(arm_msg)
#         cam_pwm = UInt16(); cam_pwm.data = int(self.pwm_neutral); self.camera_tilt_pub.publish(cam_pwm)        
        
#         # Init Gamepad
#         pygame.init()        
#         self.joysticks = []
#         for i in range(0, pygame.joystick.get_count()):
#             self.joysticks.append(pygame.joystick.Joystick(i)); self.joysticks[-1].init()
#             self.get_logger().info("Detected joystick")        
#         self.create_timer(0.04, self.update_input)
        
#     def update_input(self):
#         for event in pygame.event.get():            
#             if event.type == JOYBUTTONDOWN:
#                 if event.button == 4: self.adjust_lights("down")  
#                 elif event.button == 5: self.adjust_lights("up")  
#                 elif event.button == 7: self.arm_disarm()   
#                 elif event.button == 3: self.dive_up()  
#                 elif event.button == 0: self.dive_down()  
#             elif event.type == JOYAXISMOTION:                     
#                 if event.axis == 0 or event.axis == 1: self.move_event(event)  
#             elif event.type == JOYHATMOTION:
#                 self.camera_tilt_event(event.value)
#         if pygame.joystick.get_count() > 0:
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))

#     def dive_up(self):
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return
#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
#         if new_depth > self.max_rise:
#             self.get_logger().warn(f"Cannot set depth above {self.max_rise}m. Capping at {self.depth_status['depth_desired']:.2f}m.")
#             return
#         msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
#         self.get_logger().info(f"Desired depth is now {new_depth}")

#     def dive_down(self):
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller is not active. Cannot set depth.")
#             return
#         # This line is corrected from "desired_depth" to "depth_desired"
#         new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
#         if new_depth > -200:            
#             msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def adjust_lights(self, direction):
#         msg = UInt16()
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = int(max(target_value, self.pwm_lights_min))
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = int(min(target_value, self.pwm_lights_max))          
#         self.lights_value = float(msg.data)
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16(); value = value[1]
#         if value == 1: msg.data = int(self.pwm_camera_max)
#         elif value == -1: msg.data = int(self.pwm_camera_min)
#         else: msg.data = int(self.pwm_neutral)
#         self.camera_tilt_pub.publish(msg)

#     def rotation_event(self, value):
#         if self.yaw_status is None: return
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16(); msg.data = round(new_yaw); self.yaw_controller_pub.publish(msg)            

#     def move_event(self, event):
#         u = event.value
#         if event.axis == 1: u = -u
#         pwm = UInt16(data=self.calculate_pwm(u))
#         if event.axis == 1: self.forward_pub.publish(pwm)
#         elif event.axis == 0: self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         value = max(-1, min(1, value))
#         return int(self.pwm_neutral + value * (self.pwm_max - self.pwm_neutral))
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool(); msg.data = self.arm; self.arm_pub.publish(msg)
#         if self.arm: self.get_logger().info("The ROV is now armed!")
#         else: self.get_logger().info("The ROV is now disarmed!")

#     def callback_node_status(self, msg):        
#         data = json.loads(msg.data)
#         if data["type"] == "depth_controller": self.depth_status = data   
#         elif data["type"] == "yaw_controller": self.yaw_status = data     
            
# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()    
#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()
# #!/usr/bin/env python3
# # --- FINAL VERSION WITH JOYSTICK MODE CONTROLS ---

# import rclpy
# import pygame
# import json
# from pygame.locals import *
# from rclpy.node import Node, Client
# import traceback

# from std_msgs.msg import UInt16, Float64, Bool, String
# from std_srvs.srv import Trigger

# class Controller(Node):    
    
#     def __init__(self):
#         super().__init__("input_controller")  

#         # Declare all parameters with correct float types
#         self.declare_parameter("pwm_max", 1900.0)
#         self.declare_parameter("pwm_min", 1100.0)
#         self.declare_parameter("pwm_neutral", 1500.0)        
#         self.declare_parameter("pwm_camera_max", 1900.0)
#         self.declare_parameter("pwm_camera_min", 1100.0)
#         self.declare_parameter("pwm_lights_max", 1900.0)
#         self.declare_parameter("pwm_lights_min", 1100.0)
#         self.declare_parameter("gain_pwm_cam", 400.0)     
#         self.declare_parameter("gain_pwm_lights", 50.0)
#         self.declare_parameter("gain_depth", 0.2)
#         self.declare_parameter("gain_yaw", 40.0)
#         self.declare_parameter("arm_status", True)
#         self.declare_parameter("debug", False)
#         self.declare_parameter("max_rise", 0.5) # Default max rise of 0.5m
#         self.declare_parameter("move_pwm_range", 400.0) # Default from pid.yaml

#         # Get all parameter values
#         self.pwm_min                = self.get_parameter("pwm_min").value 
#         self.pwm_max                = self.get_parameter("pwm_max").value
#         self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
#         self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
#         self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
#         self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
#         self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 
#         self.gain_depth             = self.get_parameter("gain_depth").value     
#         self.gain_yaw               = self.get_parameter("gain_yaw").value          
#         self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
#         self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 
#         self.lights_value           = self.get_parameter("pwm_lights_min").value
#         self.arm                    = self.get_parameter("arm_status").value    
#         self.debug                  = self.get_parameter("debug").value
#         self.max_rise               = self.get_parameter("max_rise").value
#         self.move_pwm_range         = self.get_parameter("move_pwm_range").value
        
#         self.get_logger().info(f"--- MAX RISE PARAMETER LOADED: {self.max_rise} ---")
#         self.get_logger().info(f"--- MOVE PWM RANGE LOADED: +/- {self.move_pwm_range} ---")

#         # --- State Variables for Auto Modes ---
#         self.depth_hold_enabled = False
#         self.yaw_hold_enabled = False
#         self.position_hold_enabled = False
#         # Master mode state
#         self.master_auto_enabled = False 
        
#         # --- Store status data from other nodes ---
#         self.depth_status = None
#         self.yaw_status = None
#         self.position_status = None

#         # --- Publishers ---
#         self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
#         self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
#         self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
#         self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
#         self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
#         self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
#         self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              
        
#         # --- Publishers for Enabling/Disabling Auto Modes ---
#         self.depth_enable_pub = self.create_publisher(Bool, "/settings/depth/set_enable", 10)
#         self.yaw_enable_pub = self.create_publisher(Bool, "/settings/yaw/set_enable", 10)
#         self.pos_enable_pub = self.create_publisher(Bool, "/settings/position/set_enable", 10)

#         # --- Subscribers for Auto Mode Status ---
#         self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
#         self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               
#         self.position_status_sub    = self.create_subscription(String, "/settings/position/status", self.callback_node_status, 10)

#         # Clear BlueRov status
#         lights = UInt16(); lights.data = int(self.pwm_lights_min); self.lights_pub.publish(lights)
#         arm_msg = Bool(); arm_msg.data = self.arm; self.arm_pub.publish(arm_msg)
#         cam_pwm = UInt16(); cam_pwm.data = int(self.pwm_neutral); self.camera_tilt_pub.publish(cam_pwm)        
        
#         # Init Gamepad
#         pygame.init()        
#         self.joysticks = []
#         for i in range(0, pygame.joystick.get_count()):
#             self.joysticks.append(pygame.joystick.Joystick(i)); self.joysticks[-1].init()
#             self.get_logger().info("Detected joystick")        
#         self.create_timer(0.04, self.update_input)
        
#     def update_input(self):
#         for event in pygame.event.get():            
#             if event.type == JOYBUTTONDOWN:
#                 if event.button == 0: self.dive_down()  # A Button
#                 if event.button == 1: self.toggle_depth_hold() # B Button
#                 if event.button == 2: self.toggle_yaw_hold() # X Button
#                 if event.button == 3: self.dive_up()    # Y Button
#                 if event.button == 4: self.adjust_lights("down") # Left Bumper
#                 if event.button == 5: self.adjust_lights("up")   # Right Bumper
#                 if event.button == 6: self.toggle_master_auto_mode() # Back Button
#                 if event.button == 7: self.arm_disarm()   # Start Button
                
#             elif event.type == JOYAXISMOTION:                     
#                 if event.axis == 0 or event.axis == 1: self.move_event(event)  # Left Stick
#             elif event.type == JOYHATMOTION:
#                 self.camera_tilt_event(event.value) # D-Pad
        
#         if pygame.joystick.get_count() > 0:
#             # Right Stick (Axis 3)
#             self.rotation_event(pygame.joystick.Joystick(0).get_axis(3)) 

#     # --- NEW: Function to toggle depth hold ---
#     def toggle_depth_hold(self):
#         # Invert the current state
#         new_state = not self.depth_hold_enabled
#         self.get_logger().info(f"Toggling Depth Hold to: {new_state}")
        
#         # Publish the new state to the depth controller
#         msg = Bool(); msg.data = new_state
#         self.depth_enable_pub.publish(msg)

#     # --- NEW: Function to toggle yaw hold ---
#     def toggle_yaw_hold(self):
#         # Invert the current state
#         new_state = not self.yaw_hold_enabled
#         self.get_logger().info(f"Toggling Yaw Hold to: {new_state}")
        
#         # Publish the new state to the yaw controller
#         msg = Bool(); msg.data = new_state
#         self.yaw_enable_pub.publish(msg)

#     # --- NEW: Function to toggle master auto mode ---
#     def toggle_master_auto_mode(self):
#         # Invert the master state
#         self.master_auto_enabled = not self.master_auto_enabled
#         new_state = self.master_auto_enabled
        
#         if new_state:
#             self.get_logger().info("--- MASTER AUTONOMOUS MODE ENGAGED ---")
#         else:
#             self.get_logger().info("--- MASTER MANUAL MODE ENGAGED ---")

#         # Publish the new state to ALL autonomous controllers
#         msg = Bool(); msg.data = new_state
#         self.pos_enable_pub.publish(msg)
#         self.yaw_enable_pub.publish(msg)
#         self.depth_enable_pub.publish(msg)

#     def dive_up(self):
#         # Only send command if depth hold is enabled
#         if not self.depth_hold_enabled:
#             self.get_logger().warn("Depth Hold is OFF. Press 'B' to enable before setting depth.")
#             return
        
#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller status not received. Cannot set depth.")
#             return
            
#         new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
#         if new_depth > self.max_rise:
#             self.get_logger().warn(f"Cannot set depth above {self.max_rise}m. Capping at {self.depth_status['depth_desired']:.2f}m.")
#             return
#         msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
#         self.get_logger().info(f"Desired depth is now {new_depth}")

#     def dive_down(self):
#         # Only send command if depth hold is enabled
#         if not self.depth_hold_enabled:
#             self.get_logger().warn("Depth Hold is OFF. Press 'B' to enable before setting depth.")
#             return

#         if self.depth_status is None:
#             self.get_logger().warn("Depth controller status not received. Cannot set depth.")
#             return
        
#         new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
#         if new_depth > -200:            
#             msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
#             self.get_logger().info(f"Desired depth is now {new_depth}")

#     def adjust_lights(self, direction):
#         msg = UInt16()
#         if direction == "down":
#             target_value = self.lights_value - self.gain_pwm_lights
#             msg.data = int(max(target_value, self.pwm_lights_min))
#         elif direction == "up":
#             target_value = self.lights_value + self.gain_pwm_lights
#             msg.data = int(min(target_value, self.pwm_lights_max))          
#         self.lights_value = float(msg.data)
#         self.lights_pub.publish(msg)    

#     def camera_tilt_event(self, value):
#         msg = UInt16(); value = value[1]
#         if value == 1: msg.data = int(self.pwm_camera_max)
#         elif value == -1: msg.data = int(self.pwm_camera_min)
#         else: msg.data = int(self.pwm_neutral)
#         self.camera_tilt_pub.publish(msg)

#     def rotation_event(self, value):
#         # Only send command if yaw hold is enabled
#         if not self.yaw_hold_enabled:
#             # self.get_logger().warn("Yaw Hold is OFF. Press 'X' to enable before setting heading.")
#             return # Don't send target if yaw hold is off

#         if self.yaw_status is None:
#             self.get_logger().warn("Yaw controller status not received. Cannot set heading.")
#             return 
            
#         value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
#         new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
#         msg = UInt16(); msg.data = round(new_yaw); self.yaw_controller_pub.publish(msg)            

#     def move_event(self, event):
#         # If position control is enabled, do nothing (don't send manual commands)
#         if self.position_hold_enabled:
#             return 

#         # Position control is disabled, proceed with manual control
#         u = event.value
#         if event.axis == 1: u = -u
#         pwm = UInt16(data=self.calculate_pwm(u))
#         if event.axis == 1: self.forward_pub.publish(pwm)
#         elif event.axis == 0: self.lateral_pub.publish(pwm)        

#     def calculate_pwm(self, value):
#         deviation = value * self.move_pwm_range
#         pwm_command = self.pwm_neutral + deviation
#         pwm_clamped = max(self.pwm_min, min(self.pwm_max, pwm_command)) 
#         return int(pwm_clamped)
    
#     def arm_disarm(self):
#         self.arm = not self.arm
#         msg = Bool(); msg.data = self.arm; self.arm_pub.publish(msg)
#         if self.arm: self.get_logger().info("The ROV is now armed!")
#         else: self.get_logger().info("The ROV is now disarmed!")

#     # This callback now updates the internal state variables
#     def callback_node_status(self, msg):        
#         try:
#             data = json.loads(msg.data)
#             controller_type = data.get("type")
            
#             if controller_type == "depth_controller": 
#                 self.depth_status = data
#                 self.depth_hold_enabled = data.get("enable", False)
#             elif controller_type == "yaw_controller": 
#                 self.yaw_status = data
#                 self.yaw_hold_enabled = data.get("enable", False)
#             elif controller_type == "position_controller":
#                 self.position_status = data
#                 self.position_hold_enabled = data.get("enable", False)
#         except json.JSONDecodeError:
#             self.get_logger().error(f"Failed to decode status JSON: {msg.data}")
#         except Exception as e:
#              self.get_logger().error(f"Error in callback_node_status: {e}\n{traceback.format_exc()}")
            
# def main(args=None):
#     rclpy.init(args=args)    
#     node = Controller()    
#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()

#!/usr/bin/env python3
# --- VERSION WITH SMART MASTER MODE ---

import rclpy
import pygame
import json
from pygame.locals import *
from rclpy.node import Node, Client
import traceback

from std_msgs.msg import UInt16, Float64, Bool, String
from std_srvs.srv import Trigger

class Controller(Node):    
    
    def __init__(self):
        super().__init__("input_controller")  

        # Declare all parameters
        self.declare_parameter("pwm_max", 1900.0)
        self.declare_parameter("pwm_min", 1100.0)
        self.declare_parameter("pwm_neutral", 1500.0)        
        self.declare_parameter("pwm_camera_max", 1900.0)
        self.declare_parameter("pwm_camera_min", 1100.0)
        self.declare_parameter("pwm_lights_max", 1900.0)
        self.declare_parameter("pwm_lights_min", 1100.0)
        self.declare_parameter("gain_pwm_cam", 400.0)     
        self.declare_parameter("gain_pwm_lights", 50.0)
        self.declare_parameter("gain_depth", 0.2)
        self.declare_parameter("gain_yaw", 40.0)
        self.declare_parameter("arm_status", True)
        self.declare_parameter("debug", False)
        self.declare_parameter("max_rise", 0.5)
        self.declare_parameter("move_pwm_range", 400.0)

        # Get all parameter values
        self.pwm_min                = self.get_parameter("pwm_min").value 
        self.pwm_max                = self.get_parameter("pwm_max").value
        self.pwm_neutral            = self.get_parameter("pwm_neutral").value        
        self.pwm_camera_max         = self.get_parameter("pwm_camera_max").value 
        self.pwm_camera_min         = self.get_parameter("pwm_camera_min").value 
        self.pwm_lights_max         = self.get_parameter("pwm_lights_max").value 
        self.pwm_lights_min         = self.get_parameter("pwm_lights_min").value 
        self.gain_depth             = self.get_parameter("gain_depth").value     
        self.gain_yaw               = self.get_parameter("gain_yaw").value          
        self.gain_pwm_cam           = self.get_parameter("gain_pwm_cam").value 
        self.gain_pwm_lights        = self.get_parameter("gain_pwm_lights").value 
        self.lights_value           = self.get_parameter("pwm_lights_min").value
        self.arm                    = self.get_parameter("arm_status").value    
        self.debug                  = self.get_parameter("debug").value
        self.max_rise               = self.get_parameter("max_rise").value
        self.move_pwm_range         = self.get_parameter("move_pwm_range").value
        
        self.get_logger().info(f"--- MAX RISE PARAMETER LOADED: {self.max_rise} ---")
        self.get_logger().info(f"--- MOVE PWM RANGE LOADED: +/- {self.move_pwm_range} ---")

        # --- State Variables for Auto Modes ---
        self.depth_hold_enabled = False
        self.yaw_hold_enabled = False
        self.position_hold_enabled = False
        self.master_auto_enabled = False 
        
        # --- MODIFICATION: Add "shadow" variables to save state ---
        self.saved_depth_hold = False
        self.saved_yaw_hold = False
        # --- END MODIFICATION ---
        
        # --- Store status data from other nodes ---
        self.depth_status = None
        self.yaw_status = None
        self.position_status = None

        # --- Publishers ---
        self.lights_pub             = self.create_publisher(UInt16, "/bluerov2/rc/lights", 10)
        self.camera_tilt_pub        = self.create_publisher(UInt16, "/bluerov2/rc/camera_tilt", 10)
        self.forward_pub            = self.create_publisher(UInt16, "/bluerov2/rc/forward", 10)
        self.lateral_pub            = self.create_publisher(UInt16, "/bluerov2/rc/lateral", 10)        
        self.arm_pub                = self.create_publisher(Bool, "/bluerov2/arm", 10)
        self.depth_controller_pub   = self.create_publisher(Float64, "/settings/depth/set_depth", 10)
        self.yaw_controller_pub     = self.create_publisher(UInt16, "/settings/yaw/set_yaw", 10)              
        
        # --- Publishers for Enabling/Disabling Auto Modes ---
        self.depth_enable_pub = self.create_publisher(Bool, "/settings/depth/set_enable", 10)
        self.yaw_enable_pub = self.create_publisher(Bool, "/settings/yaw/set_enable", 10)
        self.pos_enable_pub = self.create_publisher(Bool, "/settings/position/set_enable", 10)

        # --- Subscribers for Auto Mode Status ---
        self.depth_status_sub       = self.create_subscription(String, "/settings/depth/status", self.callback_node_status, 10)   
        self.yaw_status_sub         = self.create_subscription(String, "/settings/yaw/status", self.callback_node_status, 10)               
        self.position_status_sub    = self.create_subscription(String, "/settings/position/status", self.callback_node_status, 10)

        # Clear BlueRov status
        lights = UInt16(); lights.data = int(self.pwm_lights_min); self.lights_pub.publish(lights)
        arm_msg = Bool(); arm_msg.data = self.arm; self.arm_pub.publish(arm_msg)
        cam_pwm = UInt16(); cam_pwm.data = int(self.pwm_neutral); self.camera_tilt_pub.publish(cam_pwm)        
        
        # Init Gamepad
        pygame.init()        
        self.joysticks = []
        for i in range(0, pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(i)); self.joysticks[-1].init()
            self.get_logger().info("Detected joystick")        
        self.create_timer(0.04, self.update_input)
        
    def update_input(self):
        for event in pygame.event.get():            
            if event.type == JOYBUTTONDOWN:
                if event.button == 1: self.dive_down()  # A Button
                if event.button == 2: self.toggle_depth_hold() # B Button
                if event.button == 0: self.toggle_yaw_hold() # X Button
                if event.button == 3: self.dive_up()    # Y Button
                if event.button == 4: self.adjust_lights("down") # Left Bumper
                if event.button == 5: self.adjust_lights("up")   # Right Bumper
                if event.button == 8: self.toggle_master_auto_mode() # Back Button
                if event.button == 9: self.arm_disarm()   # Start Button
                
            elif event.type == JOYAXISMOTION:                     
                if event.axis == 0 or event.axis == 1: self.move_event(event)  # Left Stick
            elif event.type == JOYHATMOTION:
                self.camera_tilt_event(event.value) # D-Pad
        
        if pygame.joystick.get_count() > 0:
            # Right Stick (Axis 3)
            #self.rotation_event(pygame.joystick.Joystick(0).get_axis(3))
            # New code (Axis 2 is Right Stick Horizontal on your NEW controller)
            self.rotation_event(pygame.joystick.Joystick(0).get_axis(2)) 

    def toggle_depth_hold(self):
        # --- MODIFICATION: Prevent individual toggle if master auto is on ---
        if self.master_auto_enabled:
            self.get_logger().warn("Cannot change individual holds while Master Auto Mode is engaged.")
            return
        # --- END MODIFICATION ---
            
        new_state = not self.depth_hold_enabled
        self.get_logger().info(f"Toggling Depth Hold to: {new_state}")
        msg = Bool(); msg.data = new_state
        self.depth_enable_pub.publish(msg)

    def toggle_yaw_hold(self):
        # --- MODIFICATION: Prevent individual toggle if master auto is on ---
        if self.master_auto_enabled:
            self.get_logger().warn("Cannot change individual holds while Master Auto Mode is engaged.")
            return
        # --- END MODIFICATION ---

        new_state = not self.yaw_hold_enabled
        self.get_logger().info(f"Toggling Yaw Hold to: {new_state}")
        msg = Bool(); msg.data = new_state
        self.yaw_enable_pub.publish(msg)

    # --- MODIFICATION: Re-written toggle_master_auto_mode function ---
    def toggle_master_auto_mode(self):
        # Invert the master state
        self.master_auto_enabled = not self.master_auto_enabled
        
        if self.master_auto_enabled:
            # --- ENGAGING AUTO MODE ---
            self.get_logger().info("--- MASTER AUTONOMOUS MODE ENGAGED ---")
            
            # 1. Save the current states of depth and yaw
            self.saved_depth_hold = self.depth_hold_enabled
            self.saved_yaw_hold = self.yaw_hold_enabled
            
            # 2. Force all three controllers ON
            enable_msg = Bool(); enable_msg.data = True
            self.pos_enable_pub.publish(enable_msg)
            self.yaw_enable_pub.publish(enable_msg)
            self.depth_enable_pub.publish(enable_msg)
            
        else:
            # --- DISENGAGING AUTO MODE ---
            self.get_logger().info("--- MASTER MANUAL MODE ENGAGED ---")


            # 1. Force Position Hold OFF (this is the master auto mode)
            pos_msg = Bool(); pos_msg.data = False
            self.pos_enable_pub.publish(pos_msg)
            
            # 2. Restore Depth and Yaw to their saved states
            depth_msg = Bool(); depth_msg.data = self.saved_depth_hold
            yaw_msg = Bool(); yaw_msg.data = self.saved_yaw_hold
            
            self.depth_enable_pub.publish(depth_msg)
            self.yaw_enable_pub.publish(yaw_msg)
    # --- END MODIFICATION ---

    def dive_up(self):
        if not self.depth_hold_enabled:
            self.get_logger().warn("Depth Hold is OFF. Press 'B' to enable before setting depth.")
            return
        if self.depth_status is None:
            self.get_logger().warn("Depth controller status not received. Cannot set depth.")
            return
        new_depth = round(self.depth_status["depth_desired"] + self.gain_depth, 2)
        if new_depth > self.max_rise:
            self.get_logger().warn(f"Cannot set depth above {self.max_rise}m. Capping at {self.depth_status['depth_desired']:.2f}m.")
            return
        msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
        self.get_logger().info(f"Desired depth is now {new_depth}")

    def dive_down(self):
        if not self.depth_hold_enabled:
            self.get_logger().warn("Depth Hold is OFF. Press 'B' to enable before setting depth.")
            return
        if self.depth_status is None:
            self.get_logger().warn("Depth controller status not received. Cannot set depth.")
            return
        new_depth = round(self.depth_status["depth_desired"] - self.gain_depth, 2)
        if new_depth > -200:            
            msg = Float64(); msg.data = new_depth; self.depth_controller_pub.publish(msg)
            self.get_logger().info(f"Desired depth is now {new_depth}")

    def adjust_lights(self, direction):
        msg = UInt16()
        if direction == "down":
            target_value = self.lights_value - self.gain_pwm_lights
            msg.data = int(max(target_value, self.pwm_lights_min))
        elif direction == "up":
            target_value = self.lights_value + self.gain_pwm_lights
            msg.data = int(min(target_value, self.pwm_lights_max))          
        self.lights_value = float(msg.data)
        self.lights_pub.publish(msg)    

    def camera_tilt_event(self, value):
        msg = UInt16(); value = value[1]
        if value == 1: msg.data = int(self.pwm_camera_max)
        elif value == -1: msg.data = int(self.pwm_camera_min)
        else: msg.data = int(self.pwm_neutral)
        self.camera_tilt_pub.publish(msg)

    def rotation_event(self, value):
        if not self.yaw_hold_enabled:
            return 
        if self.yaw_status is None:
            self.get_logger().warn("Yaw controller status not received. Cannot set heading.")
            return 
        value = max(-1, min(1, round(value, 1) * self.gain_yaw))        
        new_yaw = (self.yaw_status["yaw_desired"] + value) % 360
        msg = UInt16(); msg.data = round(new_yaw); self.yaw_controller_pub.publish(msg)            

    def move_event(self, event):
        if self.position_hold_enabled:
            return 
        u = event.value
        if event.axis == 1: u = -u
        pwm = UInt16(data=self.calculate_pwm(u))
        if event.axis == 1: self.forward_pub.publish(pwm)
        elif event.axis == 0: self.lateral_pub.publish(pwm)        

    def calculate_pwm(self, value):
        deviation = value * self.move_pwm_range
        pwm_command = self.pwm_neutral + deviation
        pwm_clamped = max(self.pwm_min, min(self.pwm_max, pwm_command)) 
        return int(pwm_clamped)
    
    def arm_disarm(self):
        self.arm = not self.arm
        msg = Bool(); msg.data = self.arm; self.arm_pub.publish(msg)
        if self.arm: self.get_logger().info("The ROV is now armed!")
        else: self.get_logger().info("The ROV is now disarmed!")

    def callback_node_status(self, msg):        
        try:
            data = json.loads(msg.data)
            controller_type = data.get("type")
            
            if controller_type == "depth_controller": 
                self.depth_status = data
                # Only update state if master auto is OFF
                if not self.master_auto_enabled:
                    self.depth_hold_enabled = data.get("enable", False)
            elif controller_type == "yaw_controller": 
                self.yaw_status = data
                # Only update state if master auto is OFF
                if not self.master_auto_enabled:
                    self.yaw_hold_enabled = data.get("enable", False)
            elif controller_type == "position_controller":
                self.position_status = data
                self.position_hold_enabled = data.get("enable", False)
        except json.JSONDecodeError:
            self.get_logger().error(f"Failed to decode status JSON: {msg.data}")
        except Exception as e:
             self.get_logger().error(f"Error in callback_node_status: {e}\n{traceback.format_exc()}")
            
def main(args=None):
    rclpy.init(args=args)    
    node = Controller()    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()