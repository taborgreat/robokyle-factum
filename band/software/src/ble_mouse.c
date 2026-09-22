// Based on BTstack's hog_mouse_demo.c (BLE HID over GATT). VERIFY function names against the BTstack version bundled with
// your Pico SDK (lib/btstack). The GATT database comes from hog_mouse.gatt, compiled by CMake into hog_mouse.h.
#include "ble_mouse.h"
#include "config.h"
#include "btstack.h"
#include "hog_mouse.h"          // generated: profile_data[]
#include "ble/gatt-service/battery_service_server.h"
#include "ble/gatt-service/device_information_service_server.h"
#include "ble/gatt-service/hids_device.h"
#include <string.h>

// HID report map: 3-button mouse with X, Y, wheel (report id 1)
static const uint8_t hid_descriptor[] = {
  0x05,0x01, 0x09,0x02, 0xA1,0x01, 0x85,0x01, 0x09,0x01, 0xA1,0x00,
  0x05,0x09, 0x19,0x01, 0x29,0x03, 0x15,0x00, 0x25,0x01, 0x95,0x03, 0x75,0x01, 0x81,0x02,
  0x95,0x01, 0x75,0x05, 0x81,0x03,
  0x05,0x01, 0x09,0x30, 0x09,0x31, 0x09,0x38, 0x15,0x81, 0x25,0x7F, 0x75,0x08, 0x95,0x03, 0x81,0x06,
  0xC0, 0xC0 };

static hci_con_handle_t con = HCI_CON_HANDLE_INVALID;
static uint8_t slot = 0; static bool running=false;
static btstack_packet_callback_registration_t hci_cb, sm_cb;
static int8_t pend_dx, pend_dy, pend_w; static uint8_t pend_b; static bool pending=false;

// bond table: one host address per slot, persisted in cfg? kept simple: BTstack's le_device_db holds bonds; we store the
// slot->db index map in flash next to cfg (VERIFY: extend band_config_t with bd_addr_t slot_addr[4], uint8_t slot_type[4]).
static bd_addr_t slot_addr[4]; static uint8_t slot_addr_type[4]; static bool slot_used[4];

static const uint8_t adv_data[] = {
  0x02, BLUETOOTH_DATA_TYPE_FLAGS, 0x06,
  0x0D, BLUETOOTH_DATA_TYPE_COMPLETE_LOCAL_NAME, 'R','o','b','o','K','y','l','e',' ','B','a','n','d',
  0x03, BLUETOOTH_DATA_TYPE_INCOMPLETE_LIST_OF_16_BIT_SERVICE_CLASS_UUIDS, 0x12, 0x18,
  0x03, BLUETOOTH_DATA_TYPE_APPEARANCE, 0xC2, 0x03 };   // 0x03C2 = HID mouse

static void start_adv(void){
  uint16_t iv_min=0x0030, iv_max=0x0030; bd_addr_t null_addr={0};
  if (slot_used[slot]) { gap_advertisements_set_params(iv_min, iv_max, 1 /*ADV_DIRECT_IND*/, slot_addr_type[slot], slot_addr[slot], 0x07, 0); }
  else               { gap_advertisements_set_params(iv_min, iv_max, 0 /*ADV_IND*/, 0, null_addr, 0x07, 0); }
  gap_advertisements_set_data(sizeof adv_data, (uint8_t*)adv_data);
  gap_advertisements_enable(1);
}

static void send_report(void){
  uint8_t r[4] = { pend_b, (uint8_t)pend_dx, (uint8_t)pend_dy, (uint8_t)pend_w };
  hids_device_send_input_report(con, r, sizeof r);
  pending=false;
}

static void packet_handler(uint8_t type, uint16_t ch, uint8_t *pkt, uint16_t size){
  if (type != HCI_EVENT_PACKET) return;
  switch (hci_event_packet_get_type(pkt)) {
    case HCI_EVENT_DISCONNECTION_COMPLETE: con = HCI_CON_HANDLE_INVALID; if (running) start_adv(); break;
    case SM_EVENT_JUST_WORKS_REQUEST: sm_just_works_confirm(sm_event_just_works_request_get_handle(pkt)); break;
    case SM_EVENT_PAIRING_COMPLETE:
      if (sm_event_pairing_complete_get_status(pkt)==ERROR_CODE_SUCCESS) {
        sm_event_pairing_complete_get_address(pkt, slot_addr[slot]); slot_addr_type[slot]=sm_event_pairing_complete_get_addr_type(pkt); slot_used[slot]=true; config_save();
      } break;
    case HCI_EVENT_HIDS_META:
      switch (hci_event_hids_meta_get_subevent_code(pkt)) {
        case HIDS_SUBEVENT_INPUT_REPORT_ENABLE: con = hids_subevent_input_report_enable_get_con_handle(pkt);
          gap_request_connection_parameter_update(con, 6, 12, 0, 0x48);   // 7.5–15 ms for smooth cursor
          break;
        case HIDS_SUBEVENT_CAN_SEND_NOW: if (pending) send_report(); break;
      } break;
  }
}

bool ble_mouse_start(uint8_t s){
  slot = s & 3;
  l2cap_init(); sm_init();
  sm_set_io_capabilities(IO_CAPABILITY_NO_INPUT_NO_OUTPUT);
  sm_set_authentication_requirements(SM_AUTHREQ_SECURE_CONNECTION | SM_AUTHREQ_BONDING);
  att_server_init(profile_data, NULL, NULL);
  battery_service_server_init(100);
  device_information_service_server_init(); device_information_service_server_set_manufacturer_name("Robo Kyle");
  hids_device_init(0, hid_descriptor, sizeof hid_descriptor);
  hci_cb.callback = &packet_handler; hci_add_event_handler(&hci_cb);
  sm_cb.callback = &packet_handler;  sm_add_event_handler(&sm_cb);
  hids_device_register_packet_handler(packet_handler);
  hci_power_control(HCI_POWER_ON);
  running=true; start_adv(); return true;
}
void ble_mouse_stop(void){ running=false; gap_advertisements_enable(0); if (con!=HCI_CON_HANDLE_INVALID) gap_disconnect(con); hci_power_control(HCI_POWER_OFF); }
void ble_mouse_move(int8_t dx,int8_t dy,int8_t w,uint8_t b){ if (con==HCI_CON_HANDLE_INVALID) return; pend_dx=dx; pend_dy=dy; pend_w=w; pend_b=b; pending=true; hids_device_request_can_send_now_event(con); }
void ble_mouse_pair(void){ slot_used[slot]=false; if (con!=HCI_CON_HANDLE_INVALID) gap_disconnect(con); start_adv(); }
void ble_mouse_set_slot(uint8_t s){ slot=s&3; cfg.bt_slot=slot; config_save(); if (con!=HCI_CON_HANDLE_INVALID) gap_disconnect(con); else start_adv(); }
bool ble_mouse_connected(void){ return con!=HCI_CON_HANDLE_INVALID; }
