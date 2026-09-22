cmake_minimum_required(VERSION 3.13)
set(PICO_BOARD pico_w CACHE STRING "Board type")
include(pico_sdk_import.cmake)
project(emg_band C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

add_executable(emg_band
  src/main.c src/config.c src/io.c src/emg.c src/imu.c src/net.c src/cfgsrv.c src/hand.c src/factum.c
  src/wheel.c src/wire.c src/ble_mouse.c src/modes.c src/json.c
  lib/sh2/sh2.c lib/sh2/sh2_SensorValue.c lib/sh2/sh2_util.c lib/sh2/shtp.c lib/sh2/euler.c
  lib/dhcpserver/dhcpserver.c
)
pico_generate_pio_header(emg_band ${CMAKE_CURRENT_LIST_DIR}/src/ws2812.pio)
pico_btstack_make_gatt_header(emg_band PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/hog_mouse.gatt)

target_include_directories(emg_band PRIVATE ${CMAKE_CURRENT_LIST_DIR} ${CMAKE_CURRENT_LIST_DIR}/src ${CMAKE_CURRENT_LIST_DIR}/lib/sh2
  ${CMAKE_CURRENT_LIST_DIR}/lib/dhcpserver)
target_compile_definitions(emg_band PRIVATE CYW43_HOST_NAME="robokyle-band" PICO_FLASH_ASSUME_CORE1_SAFE=1)
target_link_libraries(emg_band
  pico_stdlib pico_flash hardware_adc hardware_i2c hardware_pio hardware_uart hardware_watchdog pico_unique_id
  pico_cyw43_arch_lwip_threadsafe_background
  pico_btstack_ble pico_btstack_cyw43
)
pico_enable_stdio_usb(emg_band 1)
pico_enable_stdio_uart(emg_band 0)
pico_add_extra_outputs(emg_band)
