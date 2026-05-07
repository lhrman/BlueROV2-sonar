# #!/usr/bin/env python3
# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_launch_description():
#     ld = LaunchDescription()
#     pwm_max = 1530
#     pwm_min = 1470

#     controller_node = Node(
#         package="bluerov2_controller",
#         executable="controller",
#     )

#     video_node = Node(
#         package="bluerov2_controller",
#         executable="video",
#     )

#     input_node = Node(
#         package="bluerov2_controller",
#         executable="input_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},                    
#         ],
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#         parameters=[
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},     
#             {"enable": True},          
#         ],
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},   
#             {"enable": False},           
#         ],
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#         parameters=[
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": False},              
#         ],
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",
#         parameters=[
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": True},              
#         ],
#     )

#     ld.add_action(controller_node)
#     #ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     #ld.add_action(pitch_node)
#     #ld.add_action(roll_node)
#     ld.add_action(yaw_node)

#     return ld


# #!/usr/bin/env python3
# # --- MODIFICATION START: Added necessary imports ---
# import os
# from ament_index_python.packages import get_package_share_directory
# # --- MODIFICATION END ---
# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_launch_description():
#     ld = LaunchDescription()
    
#     # --- MODIFICATION START: Get the full path to your pid.yaml file ---
#     config = os.path.join(
#         get_package_share_directory('bluerov2_bringup'),
#         'config',
#         'pid.yaml'
#     )
#     # --- MODIFICATION END ---

#     pwm_max = 1530
#     pwm_min = 1470

#     controller_node = Node(
#         package="bluerov2_controller",
#         executable="controller",
#     )

#     video_node = Node(
#         package="bluerov2_controller",
#         executable="video",
#     )

#     input_node = Node(
#         package="bluerov2_controller",
#         executable="input_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},                    
#         ],
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#         parameters=[
#             config, # <-- MODIFICATION: Loads PID values from the YAML file
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},     
#             {"enable": True},          
#         ],
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},   
#             {"enable": False},           
#         ],
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#         parameters=[
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": False},              
#         ],
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",
#         parameters=[
#             config, # <-- MODIFICATION: Loads PID values from the YAML file
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": True},              
#         ],
#     )

#     ld.add_action(controller_node)
#     #ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     #ld.add_action(pitch_node)
#     #ld.add_action(roll_node)
#     ld.add_action(yaw_node)

#     return ld


# #!/usr/bin/env python3
# import os
# from ament_index_python.packages import get_package_share_directory
# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_launch_description():
#     ld = LaunchDescription()
    
#     config = os.path.join(
#         get_package_share_directory('bluerov2_bringup'),
#         'config',
#         'pid.yaml'
#     )

#     # --- MODIFICATION START: Changed power caps to floats ---
#     pwm_max = 1530.0
#     pwm_min = 1470.0
#     # --- MODIFICATION END ---

#     controller_node = Node(
#         package="bluerov2_controller",
#         executable="controller",
#     )

#     video_node = Node(
#         package="bluerov2_controller",
#         executable="video",
#     )

#     input_node = Node(
#         package="bluerov2_controller",
#         executable="input_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},                    
#         ],
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#         parameters=[
#             config,
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},     
#             {"enable": True},          
#         ],
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},   
#             {"enable": False},           
#         ],
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#         parameters=[
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": False},              
#         ],
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",
#         parameters=[
#             config,
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": True},              
#         ],
#     )

#     ld.add_action(controller_node)
#     #ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     #ld.add_action(pitch_node)
#     #ld.add_action(roll_node)
#     ld.add_action(yaw_node)

#     return ld

# #!/usr/bin/env python3
# import os
# from ament_index_python.packages import get_package_share_directory
# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_launch_description():
#     ld = LaunchDescription()
    
#     config = os.path.join(
#         get_package_share_directory('bluerov2_bringup'),
#         'config',
#         'pid.yaml'
#     )

#     pwm_max = 1530.0
#     pwm_min = 1470.0

#     controller_node = Node(
#         package="bluerov2_controller",
#         executable="controller",
#     )

#     # ... (video_node, input_node are the same) ...
#     input_node = Node(
#         package="bluerov2_controller",
#         executable="input_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},                    
#         ],
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#         parameters=[
#             config,
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},     
#             {"enable": False}, # <-- MODIFICATION: Starts DISABLED
#         ],
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#         parameters=[
#             {"pwm_max": pwm_max}, 
#             {"pwm_min": pwm_min},   
#             {"enable": False},           
#         ],
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#         parameters=[
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": False},              
#         ],
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",
#         parameters=[
#             config,
#             {"pwm_max": pwm_max},
#             {"pwm_min": pwm_min},    
#             {"enable": False}, # <-- MODIFICATION: Starts DISABLED
#         ],
#     )

#     ld.add_action(controller_node)
#     #ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     #ld.add_action(pitch_node)
#     #ld.add_action(roll_node)
#     ld.add_action(yaw_node)

#     return ld

#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()
    config = os.path.join(
        get_package_share_directory('bluerov2_bringup'), 'config', 'pid.yaml'
    )
    pwm_max = 1530.0
    pwm_min = 1470.0

    controller_node = Node(package="bluerov2_controller", executable="controller")
    video_node = Node(package="bluerov2_controller", executable="video")
    input_node = Node(
        package="bluerov2_controller",
        executable="input_controller",
        parameters=[
            config, # <-- MODIFICATION: Added config
            {"pwm_max": pwm_max}, 
            {"pwm_min": pwm_min},                    
        ],
    )
    depth_node = Node(
        package="bluerov2_controller", executable="depth_controller",
        parameters=[config, {"pwm_max": pwm_max}, {"pwm_min": pwm_min}, {"enable": False}],
    )
    pitch_node = Node(
        package="bluerov2_controller", executable="pitch_controller",
        parameters=[{"pwm_max": pwm_max}, {"pwm_min": pwm_min}, {"enable": False}],
    )
    roll_node = Node(
        package="bluerov2_controller", executable="roll_controller",
        parameters=[{"pwm_max": pwm_max}, {"pwm_min": pwm_min}, {"enable": False}],
    )
    yaw_node = Node(
        package="bluerov2_controller", executable="yaw_controller",
        parameters=[config, {"pwm_max": pwm_max}, {"pwm_min": pwm_min}, {"enable": False}],
    )

    ld.add_action(controller_node)
    ld.add_action(input_node)
    ld.add_action(depth_node)
    ld.add_action(pitch_node)
    ld.add_action(roll_node)
    ld.add_action(yaw_node)
    return ld