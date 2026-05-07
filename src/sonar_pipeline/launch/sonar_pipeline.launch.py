from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Optional RViz config (if you have it). If you don't, RViz will still start.
 
    pc_converter = Node(
        package='sonar_pipeline',
        executable='pc_converter',
        name='pointcloud_converter',
        output='screen',
        emulate_tty=True,
        parameters=[]
    )

    

    sonar_chunker = Node(
        package='sonar_pipeline',
        executable='sonar_chunker',
        name='chunking_wall_detector',
        output='screen',
        emulate_tty=True,
        parameters=[
            {'fixed_frame': 'sonar_frame'},

            # Static minimum gate (dynamic gate can raise it per sweep)
            {'intensity_threshold': 200.0},
            {'use_dynamic_intensity_gate': True},
            {'dynamic_gate_percentile': 95.0},

            # Strict range + intensity pre-filter before buffering
                        
            {'intensity_floor': 10.0},
            {'min_range_m': 0.4},
            {'max_range_m': 2.5},

            # Sweep/turn robustness
            {'turn_threshold_deg': 1.0},
            {'min_points_per_sweep': 20},

            # Wall detection stability
            {'min_strong_points': 5},
            {'distance_quantile': 15.0},
        ]
    )

    return LaunchDescription([
        pc_converter,
        sonar_chunker,
    ])