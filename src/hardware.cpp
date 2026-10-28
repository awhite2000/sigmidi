#include "app.hpp"
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_heap_caps.h"
#include <algorithm>
#include <cctype>
#include <cstring>
static adc_oneshot_unit_handle_t adc;
static adc_cali_handle_t calibration;
static spi_device_handle_t display;
static uint16_t *frame;
static portMUX_TYPE encMux = portMUX_INITIALIZER_UNLOCKED;
static volatile int encSteps = 0;
static volatile uint8_t previous = 0;
static volatile int quarter = 0;
// Full-cycle decoder. Set EDGES_PER_DETENT=2 for encoders with half-cycle detents.
#ifndef EDGES_PER_DETENT
#define EDGES_PER_DETENT 4
#endif
static void IRAM_ATTR encoderISR(void *) {
    int next = (gpio_get_level(GPIO_NUM_6) << 1) | gpio_get_level(GPIO_NUM_7);
    static const int8_t transitions[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
    portENTER_CRITICAL_ISR(&encMux);
    if ((previous ^ next) == 3)
        quarter = 0;
    else
        quarter += transitions[(previous << 2) | next];
    previous = next;
    if (quarter >= EDGES_PER_DETENT) {
        encSteps++;
        quarter = 0;
    }
    if (quarter <= -EDGES_PER_DETENT) {
        encSteps--;
        quarter = 0;
    }
    portEXIT_CRITICAL_ISR(&encMux);
}
static void spi(const uint8_t *d, size_t n, bool data) {
    gpio_set_level(GPIO_NUM_19, data);
    spi_transaction_t t{};
    t.length = n * 8;
    t.tx_buffer = d;
    ESP_ERROR_CHECK(spi_device_transmit(display, &t));
}
static void command(uint8_t c) { spi(&c, 1, false); }
static void pair(uint8_t c, uint8_t v) {
    command(c);
    spi(&v, 1, true);
}
void hardwareStart() {
    gpio_config_t g{};
    g.pin_bit_mask = (1ULL << 20) | (1ULL << 21) | (1ULL << 19) | (1ULL << 14);
    g.mode = GPIO_MODE_OUTPUT;
    ESP_ERROR_CHECK(gpio_config(&g));
    gpio_set_level(GPIO_NUM_20, 1);
    gpio_set_level(GPIO_NUM_21, 1);
    g = {};
    g.pin_bit_mask = (1ULL << 6) | (1ULL << 7) | (1ULL << 17);
    g.mode = GPIO_MODE_INPUT;
    g.pull_up_en = GPIO_PULLUP_ENABLE;
    ESP_ERROR_CHECK(gpio_config(&g));
    previous = (gpio_get_level(GPIO_NUM_6) << 1) | gpio_get_level(GPIO_NUM_7);
    ESP_ERROR_CHECK(gpio_install_isr_service(0));
    for (auto pin : {GPIO_NUM_6, GPIO_NUM_7}) {
        gpio_set_intr_type(pin, GPIO_INTR_ANYEDGE);
        gpio_isr_handler_add(pin, encoderISR, nullptr);
    }
    adc_oneshot_unit_init_cfg_t a{};
    a.unit_id = ADC_UNIT_1;
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&a, &adc));
    adc_oneshot_chan_cfg_t channel{};
    channel.atten = ADC_ATTEN_DB_12;
    channel.bitwidth = ADC_BITWIDTH_12;
    for (int i = 1; i <= 3; i++)
        ESP_ERROR_CHECK(adc_oneshot_config_channel(adc, (adc_channel_t)i, &channel));
    adc_cali_curve_fitting_config_t cal{};
    cal.unit_id = ADC_UNIT_1;
    cal.atten = ADC_ATTEN_DB_12;
    cal.bitwidth = ADC_BITWIDTH_12;
    state.calibrated = adc_cali_create_scheme_curve_fitting(&cal, &calibration) == ESP_OK;
    spi_bus_config_t bus{};
    bus.mosi_io_num = 22;
    bus.miso_io_num = -1;
    bus.sclk_io_num = 23;
    bus.quadwp_io_num = -1;
    bus.quadhd_io_num = -1;
    bus.max_transfer_sz = foot::DisplayWidth * foot::DisplayStripeRows * 2;
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_CH_AUTO));
    spi_device_interface_config_t device{};
    device.clock_speed_hz = 10000000;
    device.mode = 0;
    device.spics_io_num = 18;
    device.queue_size = 1;
    ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST, &device, &display));
    frame = (uint16_t *)heap_caps_calloc(foot::DisplayWidth * foot::DisplayStripeRows, 2,
                                         MALLOC_CAP_DMA);
    assert(frame);
    gpio_set_level(GPIO_NUM_14, 0);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(GPIO_NUM_14, 1);
    vTaskDelay(pdMS_TO_TICKS(100));
    // Waveshare 24382 / ST7789V2, 280x240 landscape, RGB565.
    // Register parameters follow Waveshare's LCD_1IN69 example; set landscape last.
    command(0x01);
    vTaskDelay(pdMS_TO_TICKS(150));
    pair(0x3a, 0x05);
    const uint8_t porch[] = {0x0b, 0x0b, 0, 0x33, 0x35};
    command(0xb2);
    spi(porch, sizeof porch, true);
    pair(0xb7, 0x11);
    pair(0xbb, 0x35);
    pair(0xc0, 0x2c);
    pair(0xc2, 0x01);
    pair(0xc3, 0x0d);
    pair(0xc4, 0x20);
    pair(0xc6, 0x13);
    const uint8_t power[] = {0xa4, 0xa1};
    command(0xd0);
    spi(power, sizeof power, true);
    pair(0xd6, 0xa1);
    const uint8_t positive[] = {0xf0, 0x06, 0x0b, 0x0a, 0x09, 0x26, 0x29,
                                0x33, 0x41, 0x18, 0x16, 0x15, 0x29, 0x2d};
    const uint8_t negative[] = {0xf0, 0x04, 0x08, 0x08, 0x07, 0x03, 0x28,
                                0x32, 0x40, 0x3b, 0x19, 0x18, 0x2a, 0x2e};
    command(0xe0);
    spi(positive, sizeof positive, true);
    command(0xe1);
    spi(negative, sizeof negative, true);
    const uint8_t gate[] = {0x25, 0, 0};
    command(0xe4);
    spi(gate, sizeof gate, true);
    command(0x21); // IPS panel requires display inversion.
    command(0x11);
    vTaskDelay(pdMS_TO_TICKS(120));
    pair(0x36, 0x70); // Waveshare horizontal scan; RGB, not BGR.
    command(0x29);
    vTaskDelay(pdMS_TO_TICKS(100));
}
float readMv(int index) {
    int raw = 0, mv = 0;
    if (adc_oneshot_read(adc, (adc_channel_t)(index + 1), &raw) != ESP_OK)
        return -1;
    if (!calibration || adc_cali_raw_to_voltage(calibration, raw, &mv) != ESP_OK)
        return -1;
    return mv;
}
int encoderDelta() {
    portENTER_CRITICAL(&encMux);
    int n = encSteps;
    encSteps = 0;
    portEXIT_CRITICAL(&encMux);
    return std::clamp(n, -20, 20);
}
int clickEvent(uint32_t now) {
    static bool raw = false, stable = false, held = false, armed = false;
    static uint32_t changed = 0, down = 0;
    bool r = !gpio_get_level(GPIO_NUM_17);
    if (r != raw) {
        raw = r;
        changed = now;
    }
    if (now - changed >= 20 && stable != raw) {
        stable = raw;
        if (stable) {
            down = now;
            held = false;
        } else {
            bool shortClick = armed && !held;
            armed = true;
            if (shortClick)
                return 1;
        }
    }
    if (!stable)
        armed = true;
    if (stable && armed && !held && now - down >= 700) {
        held = true;
        return 2;
    }
    return 0;
}
void pedalModes(const foot::Config &c) {
    gpio_set_level(GPIO_NUM_20, !c.pedals[0].resistor);
    gpio_set_level(GPIO_NUM_21, !c.pedals[1].resistor);
}
void lcdDraw(const foot::DisplayFrame &view) {
    static foot::DisplayFrame previousFrame{};
    static bool first = true;
    if (!first && !memcmp(&previousFrame, &view, sizeof view))
        return;
    for (int y = 0; y < foot::DisplayHeight; y += foot::DisplayStripeRows) {
        int rows = std::min(foot::DisplayStripeRows, foot::DisplayHeight - y);
        foot::renderDisplayStripe(view, y, rows, frame);
        foot::DisplayWindow window{};
        // Rotation and MSB-first SPI conversion share the existing DMA stripe.
        if (!foot::displayWindow(y, rows, window, view.displayRotation) ||
            !foot::prepareDisplayStripe(frame, rows, view.displayRotation)) {
            assert(false && "Invalid display orientation or stripe");
            return;
        }
        command(0x2a);
        spi(window.columns, sizeof window.columns, true);
        command(0x2b);
        spi(window.rows, sizeof window.rows, true);
        command(0x2c);
        spi((const uint8_t *)frame, foot::DisplayWidth * rows * 2, true);
    }
    previousFrame = view;
    first = false;
}
