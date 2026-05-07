import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    # -------------------------------------------------------------------------

    ekf_yaml = os.path.join(
        get_package_share_directory('bluerov2_bringup'),  # stavi u bringup paket
        'config', 'ekf.yaml'
    )

    slam_yaml = os.path.join(
        get_package_share_directory('bluerov2_bringup'),
        'config', 'mapper_params_online_async.yaml'
    )

    sonar_yaml = os.path.join(
        get_package_share_directory('drivers_sonar_tritech'),
        'config', 'micron_sonar_node_params.yaml'
    )

    # =========================================================================
    # 1. STATIC TRANSFORMS
    # =========================================================================

    # sonar_frame je 15cm naprijed, 10cm lijevo, 10cm gore od base_linka
    # args: x y z roll pitch yaw parent child
    static_tf_sonar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='sonar_tf',
        arguments=['0.15', '0.10', '0.10',
                   '0', '0', '0',
                   'base_link', 'sonar_frame'],
        output='screen'
    )

    # =========================================================================
    # 2. SONAR DRIVER — hardver
    # =========================================================================
    sonar_driver = Node(
        package='drivers_sonar_tritech',
        executable='micron_sonar_node',
        name='micron_sonar_node',
        output='screen',
        parameters=[sonar_yaml],
    )

    # =========================================================================
    # 3. SONAR PIPELINE — point cloud → LaserScan (full circle, kad robot stoji)
    # =========================================================================
    sonar_to_laserscan = Node(
        package='sonar_pipeline',
        executable='pointcloud_to_laserscan_full_circle',
        name='pointcloud_to_laserscan_full_circle',
        output='screen',
        # publishe na /scan automatski kad detektira punu rotaciju
    )

    # =========================================================================
    # 4. EKF — fuzira IMU → publishe TF: odom → base_link
    # =========================================================================
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_yaml],
        remappings=[
            ('/odometry/filtered', '/odom_ekf'),   # output topic (info)
        ]
    )

    # =========================================================================
    # 5. SLAM TOOLBOX — gradi mapu, publishe TF: map → odom
    # =========================================================================
    # Malo odgodimo start slam_toolboxa da EKF i TF budu stabilni
    slam_toolbox = TimerAction(
        period=3.0,  # čekaj 3 sekunde
        actions=[
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                output='screen',
                parameters=[slam_yaml],
            )
        ]
    )

    # =========================================================================
    return LaunchDescription([
        static_tf_sonar,
        sonar_driver,
        sonar_to_laserscan,
        ekf_node,
        slam_toolbox,
    ])