cmake_minimum_required(VERSION 3.8)
project(airlab_navigation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch maps rviz DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/explore_waypoints.py scripts/nav_goal_test.py scripts/frontier_explorer.py
  DESTINATION lib/${PROJECT_NAME})

ament_package()
