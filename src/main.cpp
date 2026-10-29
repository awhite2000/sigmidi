#include "app.hpp"
#include "esp_timer.h"
#include "nvs_flash.h"
#include <cmath>
#include <cstring>
State state;
SemaphoreHandle_t stateMutex;
uint32_t nowMs() { return esp_timer_get_time() / 1000; }
static foot::Engine engine;
static bool sendConfigured(const foot::Message &m, uint32_t now, void *ctx) {
    return pcCounters().transmit(m, now, bleSend, ctx);
}
static bool canSetup = false;
static foot::Sequence test;
static int testIndex = -1;
static uint32_t testDue = 0;
static int testLed = 0;
static bool testRelease = false;
static void actionFeedback(int led, bool release, void *) { state.leds.action(led, release); }
bool queueTest(int sw, bool release) {
    if (!state.setup || sw < 0 || sw >= state.draft.switchCount || !bleReady() || testIndex >= 0)
        return false;
    if (state.discardCounterDraft) {
        pcCounters().reconcile(state.saved);
        state.discardCounterDraft = false;
    }
    pcCounters().reconcile(state.saved, &state.draft);
    test = release ? state.draft.switches[sw].release : state.draft.switches[sw].press;
    testLed = state.draft.switches[sw].led;
    testRelease = release;
    testIndex = test.count ? 0 : -1;
    testDue = nowMs() + (test.count ? test.messages[0].delayMs : 0);
    return true;
}
static void uiTask(void *) {
    uint32_t shutdownAt = 0;
    for (;;) {
        foot::DisplayFrame view{};
        bool stop = false;
        {
            Lock l;
            int rotate = encoderDelta(), click = clickEvent(nowMs());
            if (!state.setup && click == 1) {
                if (canSetup) {
                    state.setup = true;
                    state.draft = state.saved;
                    state.discardCounterDraft = true;
                    state.revision++;
                    strcpy(state.notice, "Setup");
                } else
                    strcpy(state.notice, "Release switches first");
            } else
                uiStep(rotate, click);
            uiView(view);
            if (!state.setup && state.wifi) {
                if (!shutdownAt)
                    shutdownAt = nowMs() + 1000;
                stop = (int32_t)(nowMs() - shutdownAt) >= 0;
            } else
                shutdownAt = 0;
        }
        lcdDraw(view);
        if (stop) {
            wifiStop();
            shutdownAt = 0;
        }
        vTaskDelay(pdMS_TO_TICKS(30));
    }
}
extern "C" void app_main() {
    auto err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);
    stateMutex = xSemaphoreCreateMutex();
    assert(stateMutex);
    auto loaded = new foot::Config;
    if (loadConfig(*loaded)) {
        state.saved = *loaded;
        state.draft = *loaded;
    } else
        strcpy(state.notice, "Defaults: mappings empty");
    delete loaded;
    startCounterStorage();
    unsigned savedRevision = state.savedRevision;
    hardwareStart();
    if (!state.calibrated)
        strcpy(state.notice, "ADC calibration failed");
    pedalModes(state.saved);
    state.leds.configure(state.saved);
    ledsStart();
    bleStart();
    xTaskCreate(uiTask, "ui", 8192, nullptr, 3, nullptr);
    foot::Debouncer debounce;
    bool wasReady = false, wasSetup = false;
    int lastPedal[2] = {-1, -1};
    uint32_t lastSent[2]{}, lastRead = 0;
    float filtered[2] = {-1, -1};
    unsigned rejected = 0;
    for (;;) {
        uint32_t now = nowMs();
        float mv = readMv(0);
        float pedals[2] = {-2, -2};
        if (now - lastRead >= 5) {
            lastRead = now;
            pedals[0] = readMv(1);
            pedals[1] = readMv(2);
        }
        {
            Lock l;
            if (state.discardCounterDraft) {
                pcCounters().reconcile(state.saved);
                state.discardCounterDraft = false;
            }
            if (savedRevision != state.savedRevision) {
                pcCounters().reconcile(state.saved, state.setup ? &state.draft : nullptr);
                savedRevision = state.savedRevision;
            }
            state.mv[0] = mv;
            state.leds.configure(state.saved);
            int code = mv < 0 ? -1 : foot::decodeLadder(state.saved, mv);
            state.key = debounce.update(code, now, state.saved.debounceMs);
            bool ready = bleReady();
            if (ready != wasReady || state.setup != wasSetup) {
                engine.reset();
                state.leds.clear();
                debounce.reset();
                testIndex = -1;
                for (int i = 0; i < 2; i++)
                    lastPedal[i] = -1;
                wasReady = ready;
                wasSetup = state.setup;
                if (!state.setup)
                    pedalModes(state.saved);
            }
            if (!state.setup && ready) {
                engine.input(state.key, state.saved, now);
                engine.tick(now, sendConfigured, nullptr, actionFeedback);
            }
            canSetup = state.key == 0 && engine.idle();
            if (engine.rejected != rejected) {
                rejected = engine.rejected;
                strcpy(state.notice, "Action queue full");
            }
            if (state.setup && testIndex >= 0 && ready && (int32_t)(now - testDue) >= 0) {
                if (sendConfigured(test.messages[testIndex], now, nullptr)) {
                    if (testIndex == 0)
                        actionFeedback(testLed, testRelease, nullptr);
                    testIndex++;
                    if (testIndex >= test.count)
                        testIndex = -1;
                    else
                        testDue = now + test.messages[testIndex].delayMs;
                }
            }
            for (int i = 0; i < 2; i++) {
                if (pedals[i] != -2) {
                    state.mv[i + 1] = pedals[i];
                    if (pedals[i] < 0)
                        filtered[i] = -1;
                    else
                        filtered[i] =
                            filtered[i] < 0 ? pedals[i] : filtered[i] * 0.75f + pedals[i] * 0.25f;
                }
                auto &p = state.saved.pedals[i];
                int value = filtered[i] < 0 ? -1 : foot::pedalValue(p, filtered[i], lastPedal[i]);
                state.pedal[i] = value;
                if (value >= 0 && lastPedal[i] < 0)
                    lastPedal[i] = value;
                if (!state.setup && ready && p.enabled && value >= 0 && value != lastPedal[i] &&
                    now - lastSent[i] >= 20) {
                    foot::Message m;
                    m.channel = p.channel;
                    m.number = p.cc;
                    m.value = value;
                    if (bleSend(m, now, nullptr)) {
                        lastPedal[i] = value;
                        lastSent[i] = now;
                    }
                }
            }
        }
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}
