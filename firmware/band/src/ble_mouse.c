#include "ble_mouse.h"
#include "config.h"
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "btstack.h"
#include "ble/gatt-service/battery_service_server.h"
#include "ble/gatt-service/device_information_service_server.h"
#include "ble/gatt-service/hids_device.h"
#include "hog_mouse.h"        // generated from hog_mouse.gatt

// Report: buttons (3 bits + 5 pad), X, Y, wheel
static const uint8_t hid_descriptor[] = {
  0x05, 0x01, 0x09, 0x02, 0xa1, 0x01, 0x85, 0x01, 0x09, 0x01, 0xa1, 0x00,
  0x05, 0x09, 0x19, 0x01, 0x29, 0x03, 0x15, 0x00, 0x25, 0x01, 0x95, 0x03, 0x75, 0x01, 0x81, 0x02,
  0x95, 0x01, 0x75, 0x05, 0x81, 0x03,
  0x05, 0x01, 0x09, 0x30, 0x09, 0x31, 0x09, 0x38, 0x15, 0x81, 0x25, 0x7f, 0x75, 0x08, 0x95, 0x03, 0x81, 0x06,
  0xc0, 0xc0
};
static const uint8_t adv_data[] = {
  0x02, BLUETOOTH_DATA_TYPE_FLAGS, 0x06,
  0x0e, BLUETOOTH_DATA_TYPE_COMPLETE_LOCAL_NAME, 'R', 'o', 'b', 'o', 'K', 'y', 'l', 'e', ' ', 'B', 'a', 'n', 'd',
  0x03, BLUETOOTH_DATA_TYPE_COMPLETE_LIST_OF_16_BIT_SERVICE_CLASS_UUIDS,
        ORG_BLUETOOTH_SERVICE_HUMAN_INTERFACE_DEVICE & 0xff, ORG_BLUETOOTH_SERVICE_HUMAN_INTERFACE_DEVICE >> 8,
  0x03, BLUETOOTH_DATA_TYPE_APPEARANCE, 0xC2, 0x03,
};

static btstack_packet_callback_registration_t hci_cb, sm_cb;
static hci_con_handle_t con = HCI_CON_HANDLE_INVALID;
static uint8_t protocol_mode = 1, slot, pairing;
static bool stack_up, running;
static struct { int dx, dy, wheel; uint8_t buttons; bool dirty; } rep;

static bool slot_bonded(uint8_t s) { static const uint8_t z[6]; return memcmp(cfg.bt_addr[s], z, 6) != 0; }

static void advertise(void) {
  // Undirected advertising with the controller whitelist limited to this slot's bonded host, so no other host
  // can connect or even scan us (filter policy 3). While pairing the filter is open.
  // Hosts using resolvable private addresses (iPhone/Mac) need the controller's resolving list for the
  // whitelist to match; if a bonded Apple host stops reconnecting, use filter 0 for that slot.
  gap_advertisements_enable(0);
  bd_addr_t none; memset(none, 0, 6);
  gap_whitelist_clear();
  uint8_t filter = 0;
  if (!pairing && slot_bonded(slot)) { gap_whitelist_add(cfg.bt_addr_type[slot], cfg.bt_addr[slot]); filter = 3; }
  gap_advertisements_set_params(0x0030, 0x0060, 0 /* ADV_IND */, 0, none, 0x07, filter);
  gap_advertisements_set_data(sizeof adv_data, (uint8_t *)adv_data);
  gap_advertisements_enable(1);
}

static void send_report(void) {
  int8_t dx = rep.dx > 127 ? 127 : rep.dx < -127 ? -127 : rep.dx, dy = rep.dy > 127 ? 127 : rep.dy < -127 ? -127 : rep.dy;
  uint8_t r[4] = { rep.buttons, (uint8_t)dx, (uint8_t)dy, (uint8_t)(int8_t)rep.wheel };
  if (protocol_mode == 0) hids_device_send_boot_mouse_input_report(con, r, 3);
  else hids_device_send_input_report(con, r, sizeof r);
  rep.dx = rep.dy = rep.wheel = 0; rep.dirty = false;
}

static void packet_handler(uint8_t type, uint16_t channel, uint8_t *packet, uint16_t size) {
  (void)channel; (void)size;
  if (type != HCI_EVENT_PACKET) return;
  switch (hci_event_packet_get_type(packet)) {
    case BTSTACK_EVENT_STATE:
      if (btstack_event_state_get_state(packet) == HCI_STATE_WORKING) { stack_up = true; if (running) advertise(); }
      break;
    case HCI_EVENT_DISCONNECTION_COMPLETE:
      con = HCI_CON_HANDLE_INVALID; printf("ble: disconnected\n"); if (running) advertise();
      break;
    case SM_EVENT_JUST_WORKS_REQUEST: sm_just_works_confirm(sm_event_just_works_request_get_handle(packet)); break;
    case SM_EVENT_NUMERIC_COMPARISON_REQUEST: sm_numeric_comparison_confirm(sm_event_numeric_comparison_request_get_handle(packet)); break;
    case SM_EVENT_PAIRING_COMPLETE:
      if (sm_event_pairing_complete_get_status(packet) == ERROR_CODE_SUCCESS) {
        bd_addr_t a; sm_event_pairing_complete_get_address(packet, a);
        memcpy(cfg.bt_addr[slot], a, 6); cfg.bt_addr_type[slot] = sm_event_pairing_complete_get_addr_type(packet);
        pairing = 0; config_save(); printf("ble: slot %d bonded to %s\n", slot, bd_addr_to_str(a));
      }
      break;
    case HCI_EVENT_HIDS_META:
      switch (hci_event_hids_meta_get_subevent_code(packet)) {
        case HIDS_SUBEVENT_INPUT_REPORT_ENABLE:
          con = hids_subevent_input_report_enable_get_con_handle(packet); printf("ble: host subscribed\n"); break;
        case HIDS_SUBEVENT_BOOT_MOUSE_INPUT_REPORT_ENABLE:
          con = hids_subevent_boot_mouse_input_report_enable_get_con_handle(packet); break;
        case HIDS_SUBEVENT_PROTOCOL_MODE: protocol_mode = hids_subevent_protocol_mode_get_protocol_mode(packet); break;
        case HIDS_SUBEVENT_CAN_SEND_NOW: send_report(); break;
        default: break;
      }
      break;
    default: break;
  }
}

static void stack_init(void) {
  static bool done; if (done) return; done = true;
  l2cap_init(); sm_init();
  sm_set_io_capabilities(IO_CAPABILITY_NO_INPUT_NO_OUTPUT);
  sm_set_authentication_requirements(SM_AUTHREQ_SECURE_CONNECTION | SM_AUTHREQ_BONDING);
  att_server_init(profile_data, NULL, NULL);
  battery_service_server_init(100);
  device_information_service_server_init();
  hids_device_init(0, hid_descriptor, sizeof hid_descriptor);
  hci_cb.callback = packet_handler; hci_add_event_handler(&hci_cb);
  sm_cb.callback = packet_handler; sm_add_event_handler(&sm_cb);
  hids_device_register_packet_handler(packet_handler);
  hci_power_control(HCI_POWER_ON);
}

// The stack runs in the cyw43 background context; everything below is called from the main loop, so take the
// context lock (the same lock cyw43_arch_lwip_begin uses) around BTstack calls.
#define LOCK()   cyw43_arch_lwip_begin()
#define UNLOCK() cyw43_arch_lwip_end()

void ble_mouse_start(uint8_t s) { slot = s & 3; running = true; LOCK(); stack_init(); if (stack_up) advertise(); UNLOCK(); }
void ble_mouse_stop(void) {
  running = false;
  if (!stack_up) return;
  LOCK(); gap_advertisements_enable(0); if (con != HCI_CON_HANDLE_INVALID) gap_disconnect(con); UNLOCK();
}
void ble_mouse_set_slot(uint8_t s) {
  slot = s & 3; cfg.bt_slot = slot; pairing = 0;
  LOCK(); if (con != HCI_CON_HANDLE_INVALID) gap_disconnect(con); else if (stack_up && running) advertise(); UNLOCK();
}
void ble_mouse_pair(void) {
  memset(cfg.bt_addr[slot], 0, 6); pairing = 1;
  LOCK(); if (con != HCI_CON_HANDLE_INVALID) gap_disconnect(con); else if (stack_up && running) advertise(); UNLOCK();
}
bool ble_mouse_connected(void) { return con != HCI_CON_HANDLE_INVALID; }

void ble_mouse_move(int8_t dx, int8_t dy, int8_t wheel, uint8_t buttons) {
  rep.dx += dx; rep.dy += dy; rep.wheel += wheel; rep.buttons = buttons;
  if (con == HCI_CON_HANDLE_INVALID) { rep.dx = rep.dy = rep.wheel = 0; return; }
  if (!rep.dirty) { rep.dirty = true; LOCK(); hids_device_request_can_send_now_event(con); UNLOCK(); }
}
