from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            parameters=[{
            'target_frame': 'sonar_frame',
            'min_height': -0.1,
            'max_height':  0.1,
            'angle_min': -3.14159,   # -180°
            'angle_max':  3.14159,   # +180° — puni krug
            'angle_increment': 0.01745,  # 1.0° u radijanima (tvoja angular_resolution)
            'range_min': 0.9,        # tvoj min_distance
            'range_max': 5.0,        # tvoj max_distance
        }],
            remappings=[
                ('cloud_in', '/micron_sonar/point_cloud'),
                ('scan', '/scan'),
            ]
        )
    ])