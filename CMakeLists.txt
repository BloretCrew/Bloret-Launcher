cmake_minimum_required(VERSION 3.5)
project(Bloret-Launcher)

set(CMAKE_CXX_STANDARD 11)

find_package(Qt5 REQUIRED COMPONENTS Core Gui Widgets Network Json)

add_executable(Bloret-Launcher main.cpp)

target_link_libraries(Bloret-Launcher Qt5::Core Qt5::Gui Qt5::Widgets Qt5::Network Qt5::Json)