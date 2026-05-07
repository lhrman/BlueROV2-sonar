# #!/usr/bin/env python3
# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_launch_description():
#     ld = LaunchDescription()

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
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",       
#     )

#     ld.add_action(controller_node)
#     ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     ld.add_action(pitch_node)
#     ld.add_action(roll_node)
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
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#         # --- MODIFICATION START: Load PID values and enable the node ---
#         parameters=[
#             config,
#             {"enable": True}
#         ]
#         # --- MODIFICATION END ---
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#         # --- MODIFICATION START: Disable the node for safety ---
#         parameters=[{"enable": False}]
#         # --- MODIFICATION END ---
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#         # --- MODIFICATION START: Disable the node for safety ---
#         parameters=[{"enable": False}]
#         # --- MODIFICATION END ---
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",
#         # --- MODIFICATION START: Load PID values and enable the node ---
#         parameters=[
#             config,
#             {"enable": True}
#         ]
#         # --- MODIFICATION END ---
#     )

#     ld.add_action(controller_node)
#     ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     ld.add_action(pitch_node)
#     ld.add_action(roll_node)
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
#     )

#     depth_node = Node(
#         package="bluerov2_controller",
#         executable="depth_controller",
#         parameters=[
#             config,
#             {"enable": False}  # <-- MODIFICATION: Starts DISABLED
#         ]
#     )

#     pitch_node = Node(
#         package="bluerov2_controller",
#         executable="pitch_controller",
#         parameters=[{"enable": False}]
#     )

#     roll_node = Node(
#         package="bluerov2_controller",
#         executable="roll_controller",
#         parameters=[{"enable": False}]
#     )

#     yaw_node = Node(
#         package="bluerov2_controller",
#         executable="yaw_controller",
#         parameters=[
#             config,
#             {"enable": False}  # <-- MODIFICATION: Starts DISABLED
#         ]
#     )

#     ld.add_action(controller_node)
#     ld.add_action(video_node)
#     ld.add_action(input_node)
#     ld.add_action(depth_node)
#     ld.add_action(pitch_node)
#     ld.add_action(roll_node)
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

    pwm_max = 1600.0  # cap
    pwm_min = 1400.0  


    # #novi node 
    position_node = Node(
        package="bluerov2_controller",
        executable="position_controller",
        parameters=[
            config, # Load Kp, Ki, Kd values from pid.yaml
            {"enable": False} # Start disabled for safety
        ]
    )

    controller_node = Node(package="bluerov2_controller", executable="controller")
    video_node = Node(package="bluerov2_controller", executable="video")
    input_node = Node(
        package="bluerov2_controller",
        executable="input_controller",
        parameters=[config, # <-- MODIFICATION: Added config
            {"pwm_max": pwm_max}, 
            {"pwm_min": pwm_min}] 
    )
    depth_node = Node(
        package="bluerov2_controller", executable="depth_controller",
        parameters=[config, {"enable": False}]
    )
    pitch_node = Node(
        package="bluerov2_controller", executable="pitch_controller",
        parameters=[{"enable": False}]
    )
    roll_node = Node(
        package="bluerov2_controller", executable="roll_controller",
        parameters=[{"enable": False}]
    )
    yaw_node = Node(
        package="bluerov2_controller", executable="yaw_controller",
        parameters=[config, {"enable": False}]
    )
    ld.add_action(controller_node)
    ld.add_action(video_node)
    ld.add_action(input_node)
    ld.add_action(depth_node)
    ld.add_action(pitch_node)
    ld.add_action(roll_node)
    ld.add_action(yaw_node)
    #novi node
    ld.add_action(position_node)
    return ld


    