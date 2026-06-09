#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

#launch za mapping mode kada se crta mapa
def generate_launch_description():
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
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            output='screen',
            parameters=[
                '/root/ros2_ws/src/bluerov2_bringup/config/slam_params.yaml'
            ]
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
            executable='pointcloud_to_laserscan_full_circle',
            output='screen',
        ),

    ])