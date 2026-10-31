#include "app.hpp"
#include "board.hpp"
#include "driver/uart.h"
#include "esp_log.h"
#include "midi_router.hpp"
#include <atomic>

namespace {
constexpr uart_port_t MidiUart = UART_NUM_1;
constexpr int MidiBaud = 31250;
constexpr UBaseType_t QueueDepth = 32;
constexpr const char *Tag = "midi-out";
struct Packet { uint8_t bytes[3]{}; uint8_t length = 0; };
QueueHandle_t txQueue = nullptr;
std::atomic<bool> initialized{false};

void midiTxTask(void *) {
    Packet packet;
    for (;;) {
        if (xQueueReceive(txQueue, &packet, portMAX_DELAY) == pdTRUE) {
            size_t offset = 0;
            while (offset < packet.length) {
                int written = uart_write_bytes(MidiUart, packet.bytes + offset,
                                               packet.length - offset);
                if (written > 0) {
                    offset += static_cast<size_t>(written);
                } else {
                    ESP_LOGE(Tag, "UART transmit failed");
                    break;
                }
            }
        }
    }
}
}

void midiOutStart() {
    uart_config_t config{};
    config.baud_rate = MidiBaud;
    config.data_bits = UART_DATA_8_BITS;
    config.parity = UART_PARITY_DISABLE;
    config.stop_bits = UART_STOP_BITS_1;
    config.flow_ctrl = UART_HW_FLOWCTRL_DISABLE;
    config.rx_flow_ctrl_thresh = 0;
    config.source_clk = UART_SCLK_DEFAULT;

    ESP_ERROR_CHECK(uart_param_config(MidiUart, &config));
    ESP_ERROR_CHECK(uart_set_pin(MidiUart, foot::board::MidiOutTx, UART_PIN_NO_CHANGE,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    // A transmit ring buffer and a dedicated task keep FIFO waits out of the 1 ms
    // switch-scan/router loop. TX ring capacity covers the full application queue.
    ESP_ERROR_CHECK(uart_driver_install(MidiUart, 0, 256, 0, nullptr, 0));
    txQueue = xQueueCreate(QueueDepth, sizeof(Packet));
    configASSERT(txQueue);
    configASSERT(xTaskCreate(midiTxTask, "midi_tx", 3072, nullptr, 3, nullptr) == pdPASS);
    initialized = true;
    ESP_LOGI(Tag, "UART1 MIDI OUT ready on D0 / GPIO%d at %d baud", foot::board::MidiOutTx, MidiBaud);
}

bool serialReady() { return initialized.load(); }

bool serialSend(const foot::Message &message, uint32_t, void *) {
    if (!initialized.load())
        return false;
    Packet packet{};
    unsigned size = foot::serialMidiPacket(message, packet.bytes);
    if (!size || size > sizeof packet.bytes)
        return false;
    packet.length = static_cast<uint8_t>(size);
    // Zero-time enqueue: queue saturation returns false so the scheduler retries
    // without blocking and the PC counter does not advance prematurely.
    return xQueueSend(txQueue, &packet, 0) == pdTRUE;
}
