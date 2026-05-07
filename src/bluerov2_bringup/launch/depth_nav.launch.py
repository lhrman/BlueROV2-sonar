#!/usr/bin/env python3
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LoadComposableNodes

def generate_launch_description():
    ld = LaunchDescription()

    pid_path = os.path.join(
        get_package_share_directory("bluerov2_bringup"), "config", "pid.yaml"
    )

    pid_config = DeclareLaunchArgument(
        'pid_config_file',
        default_value=pid_path,
        description='Path to the config file for PID parameters'
    )

    controller_node = Node(
        package="bluerov2_controller",
        executable="controller",
    )   

    depth_node = Node(
        package="bluerov2_controller",
        executable="depth_nav",
        parameters=[LaunchConfiguration('pid_config_file')]
    )    

    video_node = Node(
        package="bluerov2_controller",
        executable="video",
    )

    ld.add_action(pid_config)
    ld.add_action(controller_node)    
    ld.add_action(depth_node)
    ld.add_action(video_node)

    return ld
