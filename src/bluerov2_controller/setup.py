from setuptools import find_packages, setup

package_name = 'bluerov2_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "controller = bluerov2_controller.controller:main",
            "depth_controller = bluerov2_controller.depth_controller:main",
            "depth_nav = bluerov2_controller.depth_nav:main",
            "pitch_controller = bluerov2_controller.pitch_controller:main",
            "roll_controller = bluerov2_controller.roll_controller:main",
            "yaw_controller = bluerov2_controller.yaw_controller:main",
            "input_controller = bluerov2_controller.input_controller:main",
            "video = bluerov2_controller.video:main",
            "video_modified = bluerov2_controller.video_modified:main",
            "position_controller = bluerov2_controller.position_controller:main",
            "hybrid_localizer = bluerov2_controller.hybrid_localizer:main",
            'cmd_vel_to_pwm = bluerov2_controller.cmd_vel_to_pwm:main',
            'camera_map_odom = sonar_pipeline.camera_map_odom:main'
        ],
    },
)
