from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    config_dir = os.path.join(
        get_package_share_directory('bluerov2_bringup'),
        'config'
    )

    ekf_local_config  = os.path.join(config_dir, 'ekf_local.yaml')
    ekf_global_config = os.path.join(config_dir, 'ekf_global.yaml')

    # ------------------------------------------------------------------ #
    # Static transforms                                                    #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # EKF local  ->  publishes odom -> base_link                          #
    #   Input: IMU angular velocity only                                   #
    #   Keeps short-term orientation stable without position drift         #
    # ------------------------------------------------------------------ #
    ekf_local = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_local',
        output='screen',
        parameters=[ekf_local_config],
        remappings=[('odometry/filtered', 'odometry/local')],
    )

    # ------------------------------------------------------------------ #
    # EKF global  ->  publishes map -> odom                               #
    #   Input: IMU linear accel + /tag_3/position (in map frame)          #
    #   Corrects drift using absolute tag position                         #
    # ------------------------------------------------------------------ #
    ekf_global = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_global',
        output='screen',
        parameters=[ekf_global_config],
        remappings=[('odometry/filtered', 'odometry/global')],
    )

    return LaunchDescription([
        ekf_local,
        ekf_global,
    ])