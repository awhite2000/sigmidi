#include "app.hpp"
#include "branding.hpp"
#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_mac.h"
#include "esp_netif.h"
#include "esp_random.h"
#include "esp_wifi.h"
#include <cstdio>
#include <cstring>
static httpd_handle_t server;
static bool initialized = false;
extern const unsigned char html_start[] asm("_binary_index_html_start");
extern const unsigned char html_end[] asm("_binary_index_html_end");
static esp_err_t response(httpd_req_t *r, cJSON *j) {
    char *text = cJSON_PrintUnformatted(j);
    cJSON_Delete(j);
    if (!text)
        return httpd_resp_send_err(r, HTTPD_500_INTERNAL_SERVER_ERROR, "Out of memory");
    httpd_resp_set_type(r, "application/json");
    httpd_resp_set_hdr(r, "Cache-Control", "no-store");
    auto result = httpd_resp_send(r, text, HTTPD_RESP_USE_STRLEN);
    free(text);
    return result;
}
static esp_err_t error(httpd_req_t *r, const char *status, const char *text) {
    httpd_resp_set_status(r, status);
    auto j = cJSON_CreateObject();
    cJSON_AddStringToObject(j, "error", text);
    return response(r, j);
}
static bool header(httpd_req_t *r, const char *key, const char *expected) {
    char b[128];
    return httpd_req_get_hdr_value_str(r, key, b, sizeof b) == ESP_OK && !strcmp(b, expected);
}
static bool originOK(httpd_req_t *r) {
    size_t n = httpd_req_get_hdr_value_len(r, "Origin");
    return n == 0 || header(r, "Origin", "http://192.168.4.1");
}
static esp_err_t page(httpd_req_t *r) {
    httpd_resp_set_type(r, "text/html");
    httpd_resp_set_hdr(r, "Content-Security-Policy",
                       "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                       "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'");
    return httpd_resp_send(r, (const char *)html_start, html_end - html_start - 1);
}
static esp_err_t session(httpd_req_t *r) {
    Lock lock;
    if (!state.setup || !originOK(r) || !header(r, "X-Setup-Password", state.password))
        return error(r, "403 Forbidden", "Invalid setup password");
    if (!state.owner.empty() && (int32_t)(state.leaseUntil - nowMs()) > 0)
        return error(r, "409 Conflict",
                     "Another editor owns the draft; close it or take over with the encoder");
    char token[33];
    for (int i = 0; i < 4; i++)
        snprintf(token + i * 8, 9, "%08lx", (unsigned long)esp_random());
    state.owner = token;
    state.leaseUntil = nowMs() + 60000;
    auto j = cJSON_CreateObject();
    cJSON_AddStringToObject(j, "token", token);
    return response(r, j);
}
static esp_err_t api(httpd_req_t *r) {
    cJSON *body = nullptr;
    if (r->method == HTTP_POST) {
        if (r->content_len <= 0 || r->content_len > 32768)
            return error(r, "413 Payload Too Large", "Request exceeds limit");
        auto data = (char *)malloc(r->content_len + 1);
        if (!data)
            return error(r, "500 Internal Server Error", "Out of memory");
        int offset = 0;
        while (offset < r->content_len) {
            int got = httpd_req_recv(r, data + offset, r->content_len - offset);
            if (got <= 0) {
                free(data);
                return error(r, "408 Request Timeout", "Incomplete request");
            }
            offset += got;
        }
        data[offset] = 0;
        body = cJSON_ParseWithLength(data, offset);
        free(data);
        if (!body)
            return error(r, "400 Bad Request", "Invalid JSON");
    }
    struct JsonGuard {
        cJSON *p;
        ~JsonGuard() { cJSON_Delete(p); }
    } guard{body};
    Lock lock;
    if (!state.setup || state.owner.empty() || (int32_t)(state.leaseUntil - nowMs()) <= 0 ||
        !header(r, "X-Session", state.owner.c_str()) || !originOK(r))
        return error(r, "403 Forbidden", "Session expired");
    state.leaseUntil = nowMs() + 60000;
    if (r->method == HTTP_POST) {
        auto rev = cJSON_GetObjectItem(body, "revision");
        if (!cJSON_IsNumber(rev) || rev->valuedouble != state.revision)
            return error(r, "409 Conflict", "Draft changed; reload before writing");
        auto action = cJSON_GetObjectItem(body, "action");
        if (!cJSON_IsString(action))
            return error(r, "400 Bad Request", "Missing action");
        if (!strcmp(action->valuestring, "draft") || !strcmp(action->valuestring, "save") ||
            !strcmp(action->valuestring, "exit")) {
            auto next = new foot::Config;
            char why[80];
            bool valid = configParse(cJSON_GetObjectItem(body, "config"), *next, why, sizeof why);
            if (!valid) {
                delete next;
                return error(r, "400 Bad Request", why);
            }
            bool saving = strcmp(action->valuestring, "draft") != 0;
            if (saving && !saveConfig(*next)) {
                delete next;
                return error(r, "500 Internal Server Error", "Flash save failed");
            }
            state.draft = *next;
            if (saving) {
                state.saved = *next;
                ++state.savedRevision;
            }
            delete next;
            state.revision++;
            if (!strcmp(action->valuestring, "exit"))
                state.setup = false;
        } else if (!strcmp(action->valuestring, "discard")) {
            state.draft = state.saved;
            state.discardCounterDraft = true;
            state.revision++;
        } else if (!strcmp(action->valuestring, "release")) {
            state.owner.clear();
        } else if (!strcmp(action->valuestring, "test")) {
            auto sw = cJSON_GetObjectItem(body, "switch");
            auto edge = cJSON_GetObjectItem(body, "edge");
            if (!cJSON_IsNumber(sw) || sw->valuedouble != sw->valueint || sw->valueint < 0 ||
                sw->valueint >= state.draft.switchCount || !cJSON_IsString(edge) ||
                (strcmp(edge->valuestring, "press") && strcmp(edge->valuestring, "release")))
                return error(r, "400 Bad Request", "Invalid test");
            extern bool queueTest(int, bool);
            if (!queueTest(sw->valueint, !strcmp(edge->valuestring, "release")))
                return error(r, "409 Conflict", "BLE not ready or test busy");
        } else
            return error(r, "400 Bad Request", "Unknown action");
    }
    auto out = cJSON_CreateObject();
    cJSON_AddNumberToObject(out, "revision", state.revision);
    cJSON_AddBoolToObject(out, "bleReady", bleReady());
    cJSON_AddBoolToObject(out, "adcCalibrated", state.calibrated);
    cJSON_AddNumberToObject(out, "key",
                            foot::switchNumber(state.saved.ladderLayout, state.saved.switchCount,
                                               state.key, state.saved.leftVariant()));
    char keyLabel[8];
    foot::switchLabel(state.saved.ladderLayout, state.saved.switchCount, state.key, keyLabel,
                      sizeof keyLabel);
    cJSON_AddStringToObject(out, "keyLabel", keyLabel);
    cJSON_AddStringToObject(out, "notice", state.notice);
    auto mv = cJSON_AddArrayToObject(out, "mv");
    for (auto v : state.mv)
        cJSON_AddItemToArray(mv, cJSON_CreateNumber(v));
    if (r->method == HTTP_POST || strstr(r->uri, "config"))
        cJSON_AddItemToObject(out, "config", configJson(state.draft));
    return response(r, out);
}
bool wifiStart() {
    if (state.wifi)
        return true;
    if (!initialized) {
        ESP_ERROR_CHECK(esp_netif_init());
        ESP_ERROR_CHECK(esp_event_loop_create_default());
        esp_netif_create_default_wifi_ap();
        wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
        ESP_ERROR_CHECK(esp_wifi_init(&init));
        initialized = true;
    }
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP);
    snprintf(state.ssid, sizeof state.ssid, foot::WifiSsidFormat, mac[4], mac[5]);
    for (int i = 0; i < 16; i++)
        state.password[i] = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[esp_random() % 31];
    state.password[16] = 0;
    wifi_config_t cfg{};
    strcpy((char *)cfg.ap.ssid, state.ssid);
    strcpy((char *)cfg.ap.password, state.password);
    cfg.ap.ssid_len = strlen(state.ssid);
    cfg.ap.channel = 1;
    cfg.ap.max_connection = 2;
    cfg.ap.authmode = WIFI_AUTH_WPA2_PSK;
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &cfg));
    ESP_ERROR_CHECK(esp_wifi_start());
    httpd_config_t hc = HTTPD_DEFAULT_CONFIG();
    hc.stack_size = 8192;
    hc.max_uri_handlers = 6;
    hc.recv_wait_timeout = 5;
    hc.lru_purge_enable = true;
    if (httpd_start(&server, &hc) != ESP_OK) {
        esp_wifi_stop();
        return false;
    }
    httpd_uri_t u{};
    u.uri = "/";
    u.method = HTTP_GET;
    u.handler = page;
    httpd_register_uri_handler(server, &u);
    u.uri = "/session";
    u.method = HTTP_POST;
    u.handler = session;
    httpd_register_uri_handler(server, &u);
    u.uri = "/api";
    u.method = HTTP_GET;
    u.handler = api;
    httpd_register_uri_handler(server, &u);
    u.method = HTTP_POST;
    httpd_register_uri_handler(server, &u);
    state.wifi = true;
    return true;
}
void wifiStop() {
    if (server) {
        httpd_stop(server);
        server = nullptr;
    }
    if (initialized)
        esp_wifi_stop();
    Lock lock;
    state.wifi = false;
    state.owner.clear();
}
