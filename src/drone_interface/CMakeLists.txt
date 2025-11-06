cmake_minimum_required(VERSION 3.8)
project(drone_interface)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)


find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/DroneAltitude.msg"
  "msg/DroneBattery.msg"
  "msg/DronePidAltitudeStatus.msg"
  "msg/DronePidData.msg"
  "msg/DroneSpeed.msg"
  "msg/DroneStatus.msg"
  "msg/DroneFlying.msg"
  "srv/DroneAction.srv"
  "srv/DroneStartPid.srv"
)

ament_export_dependencies(rosidl_default_runtime)


ament_package()