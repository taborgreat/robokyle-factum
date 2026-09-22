cmake_minimum_required(VERSION 3.13)
set(PICO_BOARD pico_w)                 # original Pico W
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(emg_band C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

add_executable(emg_band
  src/main.c src/config.c src/io.c src/emg.c src/imu.c src/net.c src/factum.c src/hand.c src/modes.c src/ble_mouse.c src/wheel.c src/wire.c src/cfgsrv.c)

target_include_directories(emg_band PRIVATE src ${CMAKE_CURRENT_LIST_DIR})
# BLE HID needs a compiled GATT database
pico_btstack_make_gatt_header(emg_band PRIVATE "${CMAKE_CURRENT_LIST_DIR}/src/hog_mouse.gatt")

target_link_libraries(emg_band
  pico_stdlib hardware_adc hardware_i2c hardware_uart hardware_watchdog hardware_flash pico_multicore
  pico_cyw43_arch_lwip_threadsafe_background
  pico_btstack_ble pico_btstack_cyw43)

target_compile_definitions(emg_band PRIVATE CYW43_LWIP=1 PICO_CYW43_ARCH_THREADSAFE_BACKGROUND=1)
pico_enable_stdio_usb(emg_band 1)
pico_enable_stdio_uart(emg_band 0)
pico_add_extra_outputs(emg_band)
