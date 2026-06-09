#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

    pkg_bluerov2_bringup = get_package_share_directory('bluerov2_bringup')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    
    nav2_config_path = os.path.join(pkg_bluerov2_bringup, 'config', 'nav2_params.yaml')
    map_path = os.path.join(pkg_bluerov2_bringup, 'config', 'moja_mapa.yaml')

    return LaunchDescription([

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['--x', '0.15', '--y', '0.10', '--z', '0.10',
                      '--roll', '0', '--pitch', '0', '--yaw', '0',
                      '--frame-id', 'base_link', '--child-frame-id', 'sonar_frame'],
            output='screen',
        ),

        Node(
            package='robot_localization',
            executable='ekf_node',
            output='screen',
            parameters=[
                '/root/ros2_ws/src/bluerov2_bringup/config/ekf.yaml'
            ]
        ),

        Node(
            package='sonar_pipeline',
            executable='pose_remap',
            output='screen',
        ),

        Node(
            package='sonar_pipeline',
            executable='camera_map_odom',
            output='screen',
        ),

        Node(
            package='bluerov2_controller',     
            executable='cmd_vel_to_pwm',   
            name='cmd_vel_to_pwm',
            output='screen',
        ),

        IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',
            'params_file': '/root/ros2_ws/src/bluerov2_bringup/config/nav2_params.yaml',
        }.items()
    )
    ])