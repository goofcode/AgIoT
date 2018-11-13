cmake_minimum_required(VERSION 2.8.4)
set(CMAKE_TOOLCHAIN_FILE ${CMAKE_SOURCE_DIR}/cmake/ArduinoToolchain.cmake)
set(PROJECT_NAME LoRa_Client)
project(${PROJECT_NAME})

#===========================================#
#  generate RadioHead Lib                   #
#===========================================#
set(RH_PATH ${CMAKE_SOURCE_DIR}/RadioHead)
include_directories(${RH_PATH})
file(GLOB RH_HDRS ${RH_PATH}/*.h)
file(GLOB RH_SRCS ${RH_PATH}/*.cpp)
generate_arduino_library(RadioHead SRCS ${RH_SRCS} HDRS ${RH_HDRS})

#===========================================#
#  generate arduino firmware                #
#===========================================#
set(${CMAKE_PROJECT_NAME}_BOARD uno)
set(${CMAKE_PROJECT_NAME}_PORT /dev/cu.wchusbserial1420)
set(${CMAKE_PROJECT_NAME}_SKETCH LoRa_Client.ino)
# set(mega.build.mcu atmega2560)
# set(mega.upload.protocol wiring)
set(mega.upload.speed 115200)
generate_arduino_firmware(${CMAKE_PROJECT_NAME} LIBS RadioHead)
