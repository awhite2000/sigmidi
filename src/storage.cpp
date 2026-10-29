#include "app.hpp"
#include "nvs.h"
#include "esp_attr.h"
#include "esp_system.h"
#include "esp_log.h"
#include <cstdlib>
// ESP32-C6 has only RTC FAST/LP SRAM; RTC_NOINIT_ATTR uses that retained region.
static RTC_NOINIT_ATTR foot::CounterMemory retainedCounters;
foot::PcCounters &pcCounters() {
    static foot::PcCounters bank(retainedCounters);
    return bank;
}
static void counterStorageTask(void *) {
    auto snapshot = new foot::CounterMemory;
    TickType_t wake = xTaskGetTickCount();
    for (;;) {
        vTaskDelayUntil(&wake, pdMS_TO_TICKS(foot::CounterFlushMs));
        bool dirty;
        {
            Lock lock;
            dirty = pcCounters().snapshot(*snapshot);
        }
        if (!dirty)
            continue;
        // Keep flash I/O outside the state lock; MIDI may advance counters meanwhile.
        nvs_handle_t h;
        auto err = nvs_open("foot", NVS_READWRITE, &h);
        if (err == ESP_OK) {
            err = nvs_set_blob(h, "pc_counters", snapshot, sizeof *snapshot);
            if (err == ESP_OK)
                err = nvs_commit(h);
            nvs_close(h);
        }
        Lock lock;
        if (err == ESP_OK)
            pcCounters().acknowledge(*snapshot);
        else {
            ESP_LOGW("pc_counter", "Flash checkpoint failed: %s", esp_err_to_name(err));
            snprintf(state.notice, sizeof state.notice, "PC counter save failed; retry in 5 min");
        }
    }
}
void startCounterStorage() {
    auto flash = new foot::CounterMemory{};
    nvs_handle_t h;
    bool loaded = false;
    if (nvs_open("foot", NVS_READONLY, &h) == ESP_OK) {
        size_t size = sizeof *flash;
        loaded = nvs_get_blob(h, "pc_counters", flash, &size) == ESP_OK && size == sizeof *flash;
        nvs_close(h);
    }
    auto reset = esp_reset_reason();
    bool retain = reset != ESP_RST_POWERON && reset != ESP_RST_BROWNOUT && reset != ESP_RST_UNKNOWN;
    pcCounters().restore(loaded ? flash : nullptr, retain);
    pcCounters().reconcile(state.saved);
    delete flash;
    configASSERT(xTaskCreate(counterStorageTask, "pc_save", 4096, nullptr, 1, nullptr) == pdPASS);
}
bool saveConfig(const foot::Config &c) {
    char error[80];
    if (!foot::validate(c, error, sizeof error))
        return false;
    auto j = configJson(c);
    char *data = cJSON_PrintUnformatted(j);
    cJSON_Delete(j);
    if (!data)
        return false;
    nvs_handle_t h;
    esp_err_t err = nvs_open("foot", NVS_READWRITE, &h);
    if (err == ESP_OK) {
        err = nvs_set_str(h, "config", data);
        if (err == ESP_OK)
            err = nvs_commit(h);
        nvs_close(h);
    }
    free(data);
    return err == ESP_OK;
}
bool loadConfig(foot::Config &c) {
    nvs_handle_t h;
    if (nvs_open("foot", NVS_READONLY, &h) != ESP_OK)
        return false;
    size_t n = 0;
    auto err = nvs_get_str(h, "config", nullptr, &n);
    if (err != ESP_OK || n > 131072) {
        nvs_close(h);
        return false;
    }
    char *data = (char *)malloc(n);
    if (!data) {
        nvs_close(h);
        return false;
    }
    err = nvs_get_str(h, "config", data, &n);
    nvs_close(h);
    auto j = err == ESP_OK ? cJSON_Parse(data) : nullptr;
    char e[80];
    bool ok = j && configParse(j, c, e, sizeof e);
    cJSON_Delete(j);
    free(data);
    return ok;
}
