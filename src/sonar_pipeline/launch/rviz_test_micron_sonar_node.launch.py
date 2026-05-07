import os

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # putanja do rviz konfiguracije
    config_rviz2 = os.path.join(
        get_package_share_directory("sonar_pipeline"),
        "rviz",
        "micron_test.rviz"
    )

    # transformacija map → sonar_frame
    map_transform_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="map_transform",
        output="screen",
        arguments=[
            "0", "0", "0", "0", "0", "0",
            "map", "sonar_frame"
        ]
    )

    # rviz node s konfiguracijom
    rviz2_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2_tritech_conf",
        output="screen",
        arguments=["-d", config_rviz2],
    )

    ld = LaunchDescription()
    ld.add_action(map_transform_node)
    ld.add_action(rviz2_node)

    return ld
