cmake_minimum_required(VERSION 3.8)
project(sonar_pipeline_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

# This finds and builds your .msg file
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/WallDetection.msg"
  DEPENDENCIES std_msgs
)

# This makes your message findable by other packages
ament_export_dependencies(rosidl_default_runtime)

ament_package()