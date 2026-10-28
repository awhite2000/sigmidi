#include "app.hpp"
#include "driver/gpio.h"
#include "driver/rmt_encoder.h"
#include "driver/rmt_tx.h"
#include "esp_log.h"
#include <cstring>

static constexpr const char *Tag = "switch-leds";
static rmt_channel_handle_t channel;
static rmt_encoder_handle_t encoder;
// Internal static storage remains valid while the IRAM-safe RMT ISR reads it.
static std::array<rmt_symbol_word_t, foot::LedSymbols> symbols;
static void ledTask(void *) {
    foot::LedFrame previous;
    bool first = true;
    uint32_t lastRefresh = 0;
    std::array<foot::LedPulse, foot::LedSymbols> pulses;
    for (;;) {
        foot::LedFrame next;
        {
            Lock lock;
            next = state.leds.frame();
        }
        // Pololu 2535 powers up blue. Periodic refresh also handles LED-rail restarts.
        if (first || !(next == previous) || uint32_t(nowMs() - lastRefresh) >= foot::LedRefreshMs) {
            foot::encodeLedFrame(next, pulses);
            for (int i = 0; i < foot::LedSymbols; ++i) {
                symbols[i].duration0 = pulses[i].highTicks;
                symbols[i].level0 = i == foot::LedSymbols - 1 ? 0 : 1;
                symbols[i].duration1 = pulses[i].lowTicks;
                symbols[i].level1 = 0;
            }
            rmt_transmit_config_t tx{}; // one frame, leave data low afterwards
            auto err = rmt_transmit(channel, encoder, symbols.data(), sizeof symbols, &tx);
            if (err == ESP_OK)
                err = rmt_tx_wait_all_done(channel, 20);
            if (err != ESP_OK) {
                ESP_LOGE(Tag, "LED transmission failed: %s", esp_err_to_name(err));
                // Stop before symbols can be reused after a timeout. MIDI keeps running.
                rmt_disable(channel);
                Lock lock;
                strcpy(state.notice, "LED output unavailable");
                break;
            }
            previous = next;
            lastRefresh = nowMs();
            first = false;
        }
        vTaskDelay(pdMS_TO_TICKS(2));
    }
    vTaskDelete(nullptr);
}
void ledsStart() {
    // Reserve an otherwise unused header pin. A missing chain is harmless.
    gpio_set_direction(static_cast<gpio_num_t>(foot::LedDataGpio), GPIO_MODE_OUTPUT);
    gpio_set_level(static_cast<gpio_num_t>(foot::LedDataGpio), 0);
    rmt_tx_channel_config_t config{};
    config.gpio_num = static_cast<gpio_num_t>(foot::LedDataGpio);
    config.clk_src = RMT_CLK_SRC_DEFAULT;
    config.resolution_hz = 20000000;
    config.mem_block_symbols = 96; // both C6 TX memory blocks, no competing RMT peripheral
    config.trans_queue_depth = 1;
    config.intr_priority = 3;
    auto err = rmt_new_tx_channel(&config, &channel);
    rmt_copy_encoder_config_t copy{};
    if (err == ESP_OK)
        err = rmt_new_copy_encoder(&copy, &encoder);
    if (err == ESP_OK)
        err = rmt_enable(channel);
    if (err == ESP_OK && xTaskCreate(ledTask, "switch-leds", 4096, nullptr, 2, nullptr) == pdPASS)
        return;
    ESP_LOGE(Tag, "LED output unavailable");
    if (channel) {
        rmt_disable(channel);
        rmt_del_channel(channel);
        channel = nullptr;
    }
    if (encoder) {
        rmt_del_encoder(encoder);
        encoder = nullptr;
    }
    strcpy(state.notice, "LED output unavailable");
}
