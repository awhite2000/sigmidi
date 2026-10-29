#include "app.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
State state;
SemaphoreHandle_t stateMutex;
uint32_t nowMs() { return 0; }
bool bleReady() { return true; }
bool usbReady() { return false; }
bool bleConnected() { return true; }
bool wifiStart() { return false; }
static std::string stored;
bool saveConfig(const foot::Config &c) {
    auto json = configJson(c);
    auto text = cJSON_PrintUnformatted(json);
    stored = text;
    cJSON_free(text);
    cJSON_Delete(json);
    return true;
}
static int testedTap = -1;
static bool testedRelease = false;
bool queueTest(int sw, bool release) {
    testedTap = sw + 1;
    testedRelease = release;
    return true;
}
static void sameConfig(const foot::Config &a, const foot::Config &b) {
    auto x = configJson(a), y = configJson(b);
    assert(cJSON_Compare(x, y, true));
    cJSON_Delete(x);
    cJSON_Delete(y);
}
struct Output {
    std::vector<int> numbers, channels, values, leds;
};
static bool send(const foot::Message &m, uint32_t, void *p) {
    auto &out = *static_cast<Output *>(p);
    out.numbers.push_back(m.number);
    out.channels.push_back(m.channel);
    out.values.push_back(m.value);
    return true;
}
static void action(int led, bool, bool, void *p) { static_cast<Output *>(p)->leds.push_back(led); }
int main() {
    const std::vector<std::vector<int>> left = {{2, 1, 4, 3},
                                                {2, 1, 5, 4, 3, 6},
                                                {2, 1, 5, 7, 4, 3, 6, 8},
                                                {2, 1, 5, 7, 9, 4, 3, 6, 8, 10}};
    const std::vector<std::vector<int>> right = {{1, 2, 3, 4},
                                                 {5, 1, 2, 6, 3, 4},
                                                 {7, 5, 1, 2, 8, 6, 3, 4},
                                                 {9, 7, 5, 1, 2, 10, 8, 6, 3, 4}};
    const char *labels[] = {"B", "A", "2", "1", "C", "3", "D", "4", "E", "5"};
    auto c = foot::defaults();
    for (int tap = 1; tap <= 10; ++tap) {
        auto &s = c.switches[tap - 1];
        snprintf(s.name, sizeof s.name, "Tap %d", tap);
        s.led = 11 - tap; // deliberately different from the tap number
        s.press.count = s.release.count = 1;
        s.press.messages[0] = {0, tap, 20 + tap, tap, 5};
        s.release.messages[0] = {1, tap + 1, 60 + tap, 0, 5};
        c.ladder[tap] += float(tap) / 100;
    }
    char error[100];
    for (int variant : {0, 1}) {
        c.enclosureVariant = variant;
        for (int i = 0; i < 4; ++i) {
            c.switchCount = 4 + i * 2;
            const auto &order = variant ? left[i] : right[i];
            for (int n = 1; n <= c.switchCount; ++n) {
                int tap = order[n - 1];
                assert(foot::switchTap(1, c.switchCount, n, c.leftVariant()) == tap);
                assert(foot::switchNumber(1, c.switchCount, tap, c.leftVariant()) == n);
                char label[8];
                foot::switchLabel(1, c.switchCount, tap, label, sizeof label);
                assert(!strcmp(label, labels[tap - 1]));
                state.saved = c;
                state.key = tap;
                foot::DisplayFrame v{};
                uiView(v);
                assert(v.activeSwitch == n && !strcmp(v.activeLabel, label));
                assert(!strcmp(v.switchName, c.switches[tap - 1].name));
                assert(v.displayRotation == (variant ? 180 : 0));
                foot::Engine engine;
                Output out;
                engine.input(0, c, 0);
                int code = foot::decodeLadder(c, c.ladder[tap]);
                assert(code == tap);
                engine.input(code, c, 10);
                engine.tick(15, send, &out, action);
                engine.input(0, c, 20);
                engine.tick(25, send, &out, action);
                assert((out.numbers == std::vector<int>{20 + tap, 60 + tap}));
                assert((out.channels == std::vector<int>{tap, tap + 1}));
                assert((out.values == std::vector<int>{tap, 0}));
                assert((out.leds == std::vector<int>{11 - tap, 11 - tap}));
            }
            assert(foot::switchNumber(1, c.switchCount, 0, c.leftVariant()) == 0);
            assert(foot::switchTap(1, c.switchCount, 0, c.leftVariant()) == -1);
            assert(foot::switchTap(1, c.switchCount, c.switchCount + 1, c.leftVariant()) == -1);
            assert(foot::switchNumber(1, c.switchCount, c.switchCount + 1, c.leftVariant()) == -1);
            auto json = configJson(c);
            auto restored = foot::defaults();
            assert(configParse(json, restored, error, sizeof error));
            sameConfig(c, restored); // includes every inactive switch and calibration slot
            cJSON_Delete(json);
        }
    }
    // Odd legacy counts keep their row membership, with one extra upper switch.
    const std::vector<std::vector<int>> linear = {
        {3, 2, 1, 5, 4}, {4, 3, 2, 1, 7, 6, 5}, {5, 4, 3, 2, 1, 9, 8, 7, 6}};
    for (const auto &order : linear)
        for (int n = 1; n <= int(order.size()); ++n) {
            assert(foot::switchTap(0, int(order.size()), n, true) == order[n - 1]);
            assert(foot::switchNumber(0, int(order.size()), order[n - 1], true) == n);
        }
    // Navigate the real Left-variant LCD: edit and test A, not the original first tap B.
    c.enclosureVariant = 1;
    c.switchCount = 6;
    state.saved = state.draft = c;
    state.setup = true;
    state.revision++;
    uiStep(0, 0);
    uiStep(0, 1); // EDIT CONFIG
    uiStep(6, 1); // switches
    foot::DisplayFrame view{};
    uiView(view);
    const char *sixLabels[] = {"A", "B", "C", "1", "2", "3"};
    for (int i = 0; i < 6; ++i)
        assert(!strcmp(view.rows[i], sixLabels[i]));
    uiStep(0, 1); // A = T2
    uiStep(1, 1); // press
    uiView(view);
    assert(!strcmp(view.rows[0], "CC22:2/2"));
    uiStep(2, 1); // Test
    assert(testedTap == 2 && !testedRelease);
    uiStep(-2, 1); // message actions
    uiStep(0, 1);  // Edit
    uiStep(2, 1);  // Controller
    uiStep(7, 1);  // accept +7
    uiStep(0, 2);  // message list
    uiStep(0, 2);  // switch
    uiStep(2, 1);  // LED number
    uiStep(1, 1);  // accept LED 9 -> 10
    uiStep(0, 2);  // switch list
    uiStep(0, 2);  // root
    uiStep(-1, 1); // calibration
    uiView(view);
    for (int i = 0; i < 6; ++i) {
        char name[20];
        snprintf(name, sizeof name, "SW %s MV", sixLabels[i]);
        assert(!strcmp(view.rows[i + 1], name));
    }
    uiStep(1, 1); // SW A MV = T2
    uiStep(5, 1); // accept +5 mV
    uiStep(0, 2); // root
    uiStep(0, 2); // sync draft
    auto expected = c;
    expected.switches[1].press.messages[0].number += 7;
    expected.switches[1].led = 10;
    expected.ladder[2] += 5;
    sameConfig(state.draft, expected);
    uiStep(2, 1); // Save & exit
    assert(!state.setup);
    sameConfig(state.saved, expected);
    auto json = cJSON_Parse(stored.c_str());
    auto restored = foot::defaults();
    assert(configParse(json, restored, error, sizeof error));
    cJSON_Delete(json);
    sameConfig(restored, expected);
    state.saved = restored;
    state.key = 2;
    uiView(view);
    assert(view.activeSwitch == 1 && view.displayRotation == 180);
    // Changing only the unified variant never rewrites any per-tap arrays.
    state.setup = true;
    state.draft = state.saved;
    state.revision++;
    uiStep(-2, 1); // EDIT CONFIG
    uiStep(10, 1); // ENCLOSURE
    uiStep(-1, 1); // RIGHT
    uiStep(0, 2);  // sync
    expected.enclosureVariant = 0;
    sameConfig(state.draft, expected);
    uiStep(2, 1); // Save & exit
    uiView(view);
    assert(view.activeSwitch == 3 && view.displayRotation == 0 && !strcmp(view.activeLabel, "A"));
    sameConfig(state.saved, expected);
    puts("Enclosure tests passed: unified Left/Right rotation, 4/6/8/10 order, fixed labels, "
         "ADC/MIDI/LED identity, LCD edit/test/calibration, save/reload and unchanged hidden data");
}
