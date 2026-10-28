#include "app.hpp"
#include "nvs.h"
#include <cstdlib>
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
