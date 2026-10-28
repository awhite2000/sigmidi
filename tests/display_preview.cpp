// Export real UI views through the same stripe renderer used on the controller.
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
bool bleConnected() { return true; }
bool wifiStart() { return true; }
bool saveConfig(const foot::Config &) { return true; }
bool queueTest(int, bool) { return true; }
static void capture(const std::string &dir, const char *name, const char *firstRow = nullptr) {
    foot::DisplayFrame view{};
    uiView(view);
    if (firstRow)
        assert(view.screen == foot::Screen::Menu && !strcmp(view.rows[0], firstRow));
    std::vector<uint16_t> stripe(foot::DisplayWidth * foot::DisplayStripeRows);
    auto file = fopen((dir + "/" + name + ".ppm").c_str(), "wb");
    if (!file)
        std::abort();
    fprintf(file, "P6\n%d %d\n255\n", foot::DisplayWidth, foot::DisplayHeight);
    for (int y = 0; y < foot::DisplayHeight; y += foot::DisplayStripeRows) {
        foot::renderDisplayStripe(view, y, foot::DisplayStripeRows, stripe.data());
        for (auto p : stripe) {
            uint8_t rgb[] = {uint8_t(((p >> 11) & 31) * 255 / 31),
                             uint8_t(((p >> 5) & 63) * 255 / 63), uint8_t((p & 31) * 255 / 31)};
            fwrite(rgb, 1, 3, file);
        }
    }
    fclose(file);
}
int main(int argc, char **argv) {
    if (argc != 2)
        return 2;
    state.saved = foot::defaults();
    strcpy(state.saved.switches[0].name, "LEAD");
    auto &sw = state.saved.switches[0];
    sw.press.count = 3;
    sw.release.count = 2;
    sw.press.messages[0] = {1, 2, 24, 0, 5};
    sw.press.messages[1] = {0, 3, 17, 127, 5};
    sw.press.messages[2] = {0, 2, 64, 0, 5};
    state.saved.pedals[0].enabled = state.saved.pedals[1].enabled = true;
    state.saved.pedals[1].cc = 7;
    state.pedal[0] = 84;
    state.pedal[1] = 32;
    state.key = 1;
    strcpy(state.notice, "BLE MIDI CONNECTED");
    capture(argv[1], "01");
    state.setup = true;
    state.draft = state.saved;
    state.revision++;
    uiStep(0, 0);
    capture(argv[1], "02");
    uiStep(0, 1);
    uiStep(6, 1);
    uiStep(foot::switchNumber(state.saved.ladderLayout, state.saved.switchCount, 1, state.saved.leftVariant()) - 1, 1);
    uiStep(1, 1);
    capture(argv[1], "03");
    uiStep(0, 1);
    uiStep(0, 1);
    uiStep(0, 1);
    capture(argv[1], "04");
    uiStep(0, 2);
    uiStep(0, 2);
    uiStep(1, 1);
    uiStep(0, 1);
    capture(argv[1], "05");
    // Return through message, sequence, switch and switch-array to root.
    for (int i = 0; i < 5; ++i)
        uiStep(0, 2);
    state.wifi = true;
    strcpy(state.ssid, "SIGMIDI-A1B2");
    strcpy(state.password, "ABCD2345EFGH6789");
    capture(argv[1], "06");
    state.owner = "preview";
    state.leaseUntil = 1000;
    capture(argv[1], "07");
    state.owner.clear();
    uiStep(0, 1); // edit config
    uiStep(8, 1); // LED chain
    capture(argv[1], "08");
    uiStep(0, 2);  // config root
    uiStep(-2, 1); // switches
    uiStep(foot::switchNumber(state.saved.ladderLayout, state.saved.switchCount, 1, state.saved.leftVariant()) - 1,
           1);    // switch B
    uiStep(3, 0); // LED assignment
    capture(argv[1], "09");
    uiStep(0, 2); // switch array
    uiStep(0, 2); // configuration root
    uiStep(4, 1); // ENCLOSURE at index 10, after switches at 6
    uiStep(1, 0); // Preferred Left variant, already selected by new defaults
    capture(argv[1], "10");
    uiStep(0, 1); // accept Left
    uiStep(0, 2); // sync draft and return to setup
    uiStep(2, 1); // Save & exit
    state.setup = true;
    state.draft = state.saved;
    state.revision++;
    uiStep(-2, 1); // EDIT CONFIG
    uiStep(6, 1); // switches, now A through E / 1 through 5
    assert(state.saved.leftVariant());
    capture(argv[1], "11", "A");
    uiStep(0, 2); // root
    uiStep(-1, 1); // same physical calibration slots in Left browsing order
    capture(argv[1], "12", "IDLE MV");
    uiStep(0, 2); // root
    uiStep(1, 1); // Left switches
    uiStep(100, 0); // scroll to the lower row's final switch
    capture(argv[1], "13", "D");
    uiStep(0, 2); // root
    uiStep(-1, 1); // Left calibration
    uiStep(100, 0);
    capture(argv[1], "14", "SW D MV");
    uiStep(0, 2); // root, calibration at index 5
    uiStep(5, 1); // ENCLOSURE
    uiStep(-1, 1); // Right, accept
    uiStep(0, 2); // sync draft, return to setup
    uiStep(2, 1); // Save & exit
    assert(!state.saved.leftVariant());
    state.setup = true;
    state.draft = state.saved;
    state.revision++;
    uiStep(-2, 1); // EDIT CONFIG
    uiStep(6, 1); // Right switches
    capture(argv[1], "15", "E");
    uiStep(100, 0);
    capture(argv[1], "16", "B");
    uiStep(0, 2); // root
    uiStep(-1, 1); // Right calibration
    capture(argv[1], "17", "IDLE MV");
    uiStep(100, 0);
    capture(argv[1], "18", "SW B MV");
}
