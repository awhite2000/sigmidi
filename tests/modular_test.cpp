#include "app.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
State state;
SemaphoreHandle_t stateMutex;
uint32_t nowMs() { return 0; }
bool bleReady() { return true; }
bool bleConnected() { return true; }
bool wifiStart() { return false; }
bool saveConfig(const foot::Config &) { return true; }
static int testedTap = -1;
bool queueTest(int sw, bool) {
    testedTap = sw + 1;
    return true;
}
struct Output {
    std::vector<int> values, leds;
};
static bool send(const foot::Message &m, uint32_t, void *p) {
    static_cast<Output *>(p)->values.push_back(m.value);
    return true;
}
static void action(int led, bool, bool, void *p) { static_cast<Output *>(p)->leds.push_back(led); }
int main() {
    // Independent expected row-first orders, including all three requested sizes.
    const std::vector<std::vector<int>> orders = {{1, 2, 3, 4},
                                                  {5, 1, 2, 6, 3, 4},
                                                  {7, 5, 1, 2, 8, 6, 3, 4},
                                                  {9, 7, 5, 1, 2, 10, 8, 6, 3, 4}};
    const char *labels[] = {"B", "A", "2", "1", "C", "3", "D", "4", "E", "5"};
    char error[100];
    auto c = foot::defaults();
    c.enclosureVariant = 0; // This suite exercises original Right row order.
    assert(c.version == 6 && c.ladderLayout == 1);
    for (int i = 0; i < 10; ++i) {
        c.switches[i].press.count = c.switches[i].release.count = 1;
        c.switches[i].press.messages[0] = {0, 1, 17, i + 1, 5};
        c.switches[i].release.messages[0] = {0, 1, 17, i + 41, 5};
        c.ladder[i + 1] += float(i) / 10; // distinguish retained measured centers
    }
    for (const auto &order : orders) {
        c.switchCount = int(order.size());
        assert(foot::validate(c, error, sizeof error));
        for (int n = 1; n <= c.switchCount; ++n) {
            int tap = order[n - 1];
            assert(foot::switchTap(1, c.switchCount, n) == tap);
            assert(foot::switchNumber(1, c.switchCount, tap) == n);
            char label[8];
            foot::switchLabel(1, c.switchCount, tap, label, sizeof label);
            assert(!strcmp(label, labels[tap - 1]));
            state.saved = c;
            state.key = tap;
            foot::DisplayFrame live{};
            uiView(live);
            assert(!strcmp(live.activeLabel, labels[tap - 1]));
            assert(!strcmp(live.switchName, c.switches[tap - 1].name));
            // Actual ADC -> debounce -> engine -> both edge lists and associated LED.
            foot::Debouncer debounce;
            foot::Engine engine;
            Output out;
            engine.input(debounce.update(0, 0, 10), c, 0);
            engine.input(debounce.update(0, 10, 10), c, 10);
            int code = foot::decodeLadder(c, c.ladder[tap]);
            assert(code == tap);
            engine.input(debounce.update(code, 11, 10), c, 11);
            engine.input(debounce.update(code, 21, 10), c, 21);
            engine.tick(26, send, &out, action);
            engine.input(debounce.update(0, 30, 10), c, 30);
            engine.input(debounce.update(0, 40, 10), c, 40);
            engine.tick(45, send, &out, action);
            assert((out.values == std::vector<int>{tap, tap + 40}));
            assert((out.leds == std::vector<int>{tap, tap}));
            assert(engine.idle());
        }
        for (int tap = c.switchCount + 1; tap <= 10; ++tap)
            assert(foot::decodeLadder(c, c.ladder[tap]) == -1);
        assert(foot::switchNumber(1, c.switchCount, 0) == 0);
        assert(foot::switchTap(1, c.switchCount, 0) == -1);
        assert(foot::switchNumber(1, c.switchCount, c.switchCount + 1) == -1);
        auto json = configJson(c);
        auto parsed = foot::defaults();
        assert(configParse(json, parsed, error, sizeof error));
        assert(parsed.ladderLayout == 1 && parsed.switchCount == c.switchCount);
        for (int tap = 1; tap <= 10; ++tap) {
            assert(parsed.switches[tap - 1].press.messages[0].value == tap);
            assert(parsed.switches[tap - 1].led == tap);
            assert(parsed.ladder[tap] == c.ladder[tap]);
        }
        cJSON_Delete(json);
    }
    for (int count : {3, 5, 7, 9, 11}) {
        c.switchCount = count;
        assert(!foot::validate(c, error, sizeof error));
        assert(foot::decodeLadder(c, c.ladder[0]) == -1);
    }
    c.switchCount = 6;
    auto json = configJson(c);
    auto parsed = foot::defaults();
    cJSON_DeleteItemFromObject(json, "ladderLayout");
    assert(!configParse(json, parsed, error, sizeof error));
    cJSON_AddStringToObject(json, "ladderLayout", "1");
    assert(!configParse(json, parsed, error, sizeof error));
    cJSON_ReplaceItemInObjectCaseSensitive(json, "ladderLayout", cJSON_CreateNumber(2));
    assert(!configParse(json, parsed, error, sizeof error));
    // A real v3 backup retains tap order, custom LEDs, calibration and messages.
    cJSON_DeleteItemFromObject(json, "ladderLayout");
    cJSON_SetNumberValue(cJSON_GetObjectItem(json, "version"), 3);
    assert(configParse(json, parsed, error, sizeof error));
    assert(parsed.version == 6 && parsed.ladderLayout == 0 && parsed.switchCount == 6);
    assert(parsed.switches[4].press.messages[0].value == 5 && parsed.switches[4].led == 5);
    assert(parsed.ladder[10] == c.ladder[10]);
    cJSON_Delete(json);

    // Real LCD navigation must edit/calibrate/test T5 when displaying switch C at N=6.
    state.setup = true;
    state.draft = c;
    state.saved = c;
    state.revision++;
    uiStep(0, 0);
    uiStep(0, 1); // EDIT CONFIG
    uiStep(6, 1);
    foot::DisplayFrame switchList{};
    uiView(switchList);
    assert(!strcmp(switchList.rows[0], "C"));
    uiStep(0, 1); // switch C, T5
    uiStep(1, 1); // press list
    foot::DisplayFrame view{};
    uiView(view);
    assert(!strcmp(view.rows[0], "CC17:5/1"));
    assert(strstr(view.breadcrumb, "C"));
    uiStep(2, 1); // TEST, index count+1
    assert(testedTap == 5);
    uiStep(0, 2);
    uiStep(0, 2);
    uiStep(0, 2);  // root
    uiStep(-1, 1); // calibration ladder
    uiView(view);
    assert(!strcmp(view.rows[1], "SW C MV"));
    uiStep(1, 1);
    uiStep(7, 0); // displayed 1 -> T5 center
    uiStep(0, 2); // cancel must restore T5, not overwrite T1
    uiStep(0, 2);
    uiStep(0, 2); // root then sync
    assert(state.draft.ladder[5] == c.ladder[5]);
    assert(state.draft.ladder[1] == c.ladder[1]);
    uiStep(0, 1);
    uiStep(5, 1); // calibration
    uiStep(1, 1);
    uiStep(7, 1); // change T5 by 7mV and accept
    uiStep(0, 2);
    uiStep(0, 2); // sync
    assert(state.draft.ladder[5] == c.ladder[5] + 7);
    assert(state.draft.ladder[1] == c.ladder[1]);
    // Count changes preserve physical mappings and calibration (no array reshuffle).
    uiStep(0, 1);
    uiStep(1, 1);
    uiStep(-1, 1); // count 6 -> 4, pair step
    uiStep(0, 2);
    uiStep(0, 2); // sync
    assert(state.draft.switchCount == 4);
    assert(state.draft.switches[4].press.messages[0].value == 5);
    assert(state.draft.ladder[5] == c.ladder[5] + 7);
    state.setup = false;
    state.key = 5;
    uiView(view);
    assert(view.activeSwitch == 1 && !strcmp(view.activeLabel, "C") &&
           !strcmp(view.switchName, c.switches[4].name));
    puts("Modular tests passed: 4/6/8/10 row numbering, ADC-to-MIDI and LEDs, migration, mapped "
         "LCD edit/cancel/test, retained hidden data");
}
