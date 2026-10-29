#pragma once
#include "cJSON.h"
#include "core.hpp"
#include "counters.hpp"
#include "display.hpp"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "leds.hpp"
#include <string>
struct State {
    foot::Config saved = foot::defaults(), draft = saved;
    bool setup = false, wifi = false, calibrated = false;
    unsigned revision = 1;
    unsigned savedRevision = 0;
    bool discardCounterDraft = false;
    float mv[3]{};
    int pedal[2] = {-1, -1}, key = -1;
    char notice[80] = "Ready", ssid[33]{}, password[17]{};
    std::string owner;
    foot::LedFeedback leds;
    uint32_t leaseUntil = 0; // browser writer lease
};
extern State state;
extern SemaphoreHandle_t stateMutex;
struct Lock {
    Lock() { xSemaphoreTake(stateMutex, portMAX_DELAY); }
    ~Lock() { xSemaphoreGive(stateMutex); }
};
cJSON *configJson(const foot::Config &);
bool configParse(const cJSON *, foot::Config &, char *, size_t);
bool loadConfig(foot::Config &);
bool saveConfig(const foot::Config &);
foot::PcCounters &pcCounters();
void startCounterStorage();
bool bleReady();
bool bleConnected();
void bleStart();
bool bleSend(const foot::Message &, uint32_t, void *);
void hardwareStart();
void ledsStart();
float readMv(int index);
int encoderDelta();
int clickEvent(uint32_t now);
void pedalModes(const foot::Config &);
void lcdDraw(const foot::DisplayFrame &);
void uiStep(int rotation, int click);
void uiRender(char lines[10][24]); // host-test adapter for the shared UI view
void uiView(foot::DisplayFrame &);
bool wifiStart();
void wifiStop();
uint32_t nowMs();
