#include "status_led.h"
#include "pins.h"
#include "hardware/pio.h"
#include "ws2812.pio.h"
static PIO pio; static uint sm;
void led_init(void) { pio = pio0; sm = pio_claim_unused_sm(pio, true); uint off = pio_add_program(pio, &ws2812_program); ws2812_program_init(pio, sm, off, PIN_WS2812, 800000); led_rgb(0, 0, 0); }
void led_rgb(uint8_t r, uint8_t g, uint8_t b) { pio_sm_put_blocking(pio, sm, ((uint32_t)g << 24) | ((uint32_t)r << 16) | ((uint32_t)b << 8)); }
