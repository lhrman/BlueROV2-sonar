import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'sonar_pipeline'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),

        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
    ],
    install_requires=['setuptools', 'rclpy', 'sensor_msgs', 'std_msgs', 'numpy', 'tf2_ros_py', 'tf2_sensor_msgs', 'sonar_pipeline_interfaces'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='matejbozac1@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pc_converter = sonar_pipeline.pc_to_pc2_converter:main',
            'sonar_chunker = sonar_pipeline.sonar_chunker_node:main',
            'sonar_continous = sonar_pipeline.sonar_continous_map:main',
            'sonar_wall_mapper = sonar_pipeline.sonar_wall_mapper:main',
            'sonar_scan_assembler = sonar_pipeline.sonar_scan_assembler:main',
            'pointcloud_to_laserscan = sonar_pipeline.pointcloud_to_laserscan_node:main',
            'pointcloud_to_laserscan_2 = sonar_pipeline.pointcloud_to_laserscan_node_2:main',
            'pointcloud_to_laserscan_full_circle = sonar_pipeline.pointcloud_to_laserscan_full_circle:main',
            'pose_to_tf = sonar_pipeline.pose_to_tf:main',
            'pose_remap = sonar_pipeline.pose_remap:main'
        ],
    },
)
