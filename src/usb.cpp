#include "app.hpp"
#include "board.hpp"
#include "branding.hpp"
#include "midi_router.hpp"
#include "tinyusb.h"
#include "esp_mac.h"
#include <atomic>
#include <cstdio>
static std::atomic<bool> mounted{false}, suspended{false};
static char serial[13];
static const char language[]{0x09, 0x04};
static const char *strings[]{language, "SIGMIDI", foot::ProjectName, serial, "SIGMIDI MIDI"};
static const uint8_t configuration[]{
    // One class-compliant MIDI 1.0 cable, bidirectional endpoints. Input is discarded.
    TUD_CONFIG_DESCRIPTOR(1, 2, 0, TUD_CONFIG_DESC_LEN + TUD_MIDI_DESC_LEN,
                          TUSB_DESC_CONFIG_ATT_SELF_POWERED, 500),
    TUD_MIDI_DESCRIPTOR(0, 4, 0x01, 0x81, 64),
};
extern "C" void tud_mount_cb() { mounted = true; suspended = false; }
extern "C" void tud_umount_cb() { mounted = false; suspended = false; }
extern "C" void tud_suspend_cb(bool) { suspended = true; }
extern "C" void tud_resume_cb() { suspended = false; }
static void usbReceive(void *) {
    uint8_t packet[4];
    for (;;) {
        // Drain inbound host traffic; no MIDI-thru or input actions.
        for (int i = 0; i < 32 && tud_midi_packet_read(packet); ++i) {}
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}
void usbStart() {
    uint8_t mac[6]; ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_STA));
    snprintf(serial, sizeof serial, "%02X%02X%02X%02X%02X%02X", mac[0],mac[1],mac[2],mac[3],mac[4],mac[5]);
    tinyusb_config_t config{};
    config.string_descriptor = strings;
    config.string_descriptor_count = sizeof strings / sizeof strings[0];
    config.configuration_descriptor = configuration;
    // VIN-powered operation must disconnect the USB pull-up when host VBUS vanishes.
    config.self_powered = true;
    config.vbus_monitor_io = foot::board::UsbVbusSense;
    ESP_ERROR_CHECK(tinyusb_driver_install(&config));
    configASSERT(xTaskCreate(usbReceive, "usb_rx", 3072, nullptr, 2, nullptr) == pdPASS);
}
bool usbReady() { return mounted && !suspended; }
bool usbSend(const foot::Message &m, uint32_t, void *) {
    uint8_t packet[4];
    return usbReady() && foot::usbMidiPacket(m, packet) && tud_midi_packet_write(packet);
}
