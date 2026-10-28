#include "app.hpp"
#include "branding.hpp"
#include "esp_log.h"
#include "host/ble_hs.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"
#include <atomic>
#include <cstring>
static std::atomic<int> connection{-1};
static std::atomic<bool> subscribed{false};
static uint16_t valueHandle;
static uint8_t addrType;
static const ble_uuid128_t service = BLE_UUID128_INIT(
    0x00, 0xc7, 0xc4, 0x4e, 0xe3, 0x6c, 0x51, 0xa7, 0x33, 0x4b, 0xe8, 0xed, 0x5a, 0x0e, 0xb8, 0x03);
static const ble_uuid128_t characteristic = BLE_UUID128_INIT(
    0xf3, 0x6b, 0x10, 0x9d, 0x66, 0xf2, 0xa1, 0xa9, 0x12, 0x41, 0x68, 0x38, 0xdb, 0xe5, 0x72, 0x77);
static int access(uint16_t, uint16_t, ble_gatt_access_ctxt *, void *) {
    return 0;
} // empty reads; incoming MIDI intentionally ignored
static ble_gatt_chr_def chars[2]{};
static ble_gatt_svc_def services[2]{};
static void advertise();
static int event(ble_gap_event *e, void *) {
    switch (e->type) {
    case BLE_GAP_EVENT_CONNECT:
        if (e->connect.status == 0) {
            connection = e->connect.conn_handle;
            subscribed = false;
            ble_gap_upd_params p{};
            p.itvl_min = 6;
            p.itvl_max = 12;
            p.supervision_timeout = 400;
            ble_gap_update_params(connection, &p);
        } else
            advertise();
        break;
    case BLE_GAP_EVENT_DISCONNECT:
        connection = -1;
        subscribed = false;
        advertise();
        break;
    case BLE_GAP_EVENT_SUBSCRIBE:
        if (e->subscribe.attr_handle == valueHandle)
            subscribed = e->subscribe.cur_notify;
        break;
    case BLE_GAP_EVENT_ADV_COMPLETE:
        advertise();
        break;
    default:
        break;
    }
    return 0;
}
static void advertise() {
    ble_hs_adv_fields f{};
    f.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    f.uuids128 = &service;
    f.num_uuids128 = 1;
    f.uuids128_is_complete = 1;
    ble_gap_adv_set_fields(&f);
    ble_hs_adv_fields scan{};
    const char *name = foot::ProjectName;
    scan.name = (uint8_t *)name;
    scan.name_len = strlen(name);
    scan.name_is_complete = 1;
    ble_gap_adv_rsp_set_fields(&scan);
    ble_gap_adv_params p{};
    p.conn_mode = BLE_GAP_CONN_MODE_UND;
    p.disc_mode = BLE_GAP_DISC_MODE_GEN;
    int rc = ble_gap_adv_start(addrType, nullptr, BLE_HS_FOREVER, &p, event, nullptr);
    if (rc)
        ESP_LOGE("ble", "advertise: %d", rc);
}
static void synced() {
    if (ble_hs_id_infer_auto(0, &addrType) == 0)
        advertise();
}
static void reset(int reason) {
    connection = -1;
    subscribed = false;
    ESP_LOGW("ble", "host reset %d", reason);
}
static void host(void *) {
    nimble_port_run();
    nimble_port_freertos_deinit();
}
void bleStart() {
    ESP_ERROR_CHECK(nimble_port_init());
    ble_svc_gap_init();
    ble_svc_gatt_init();
    ble_svc_gap_device_name_set(foot::ProjectName);
    chars[0].uuid = &characteristic.u;
    chars[0].access_cb = access;
    chars[0].flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_WRITE | BLE_GATT_CHR_F_WRITE_NO_RSP |
                     BLE_GATT_CHR_F_NOTIFY;
    chars[0].val_handle = &valueHandle;
    services[0].type = BLE_GATT_SVC_TYPE_PRIMARY;
    services[0].uuid = &service.u;
    services[0].characteristics = chars;
    if (ble_gatts_count_cfg(services) != 0)
        abort();
    if (ble_gatts_add_svcs(services) != 0)
        abort();
    ble_hs_cfg.sync_cb = synced;
    ble_hs_cfg.reset_cb = reset;
    nimble_port_freertos_init(host);
}
bool bleReady() { return connection >= 0 && subscribed; }
bool bleConnected() { return connection >= 0; }
bool bleSend(const foot::Message &m, uint32_t now, void *) {
    int c = connection;
    if (c < 0 || !subscribed)
        return false;
    uint8_t packet[5];
    auto n = foot::midiPacket(m, now, packet);
    auto b = ble_hs_mbuf_from_flat(packet, n);
    if (!b)
        return false;
    return ble_gatts_notify_custom(c, valueHandle, b) == 0;
}
