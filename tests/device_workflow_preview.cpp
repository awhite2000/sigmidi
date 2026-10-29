// Capture real local-menu paths for the illustrated user manual.
#include "app.hpp"
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
State state;
SemaphoreHandle_t stateMutex;
uint32_t nowMs() { return 0; }
bool bleReady() { return true; }
bool usbReady() { return false; }
bool bleConnected() { return true; }
bool wifiStart() { return true; }
bool saveConfig(const foot::Config &) { return true; }
bool queueTest(int, bool) { return true; }
static cJSON *frames;
static void select(const char *name, foot::MenuRowKind kind) {
    uiStep(-100, 0);
    for (int i = 0; i < 64; ++i) {
        foot::DisplayFrame v{};
        uiView(v);
        int row = v.selectedRow;
        if (!strcmp(v.rows[row], name) && v.rowKinds[row] == kind)
            return;
        uiStep(1, 0);
    }
    fprintf(stderr, "Menu item not found: %s\n", name);
    std::abort();
}
static void root() {
    for (int i = 0; i < 12; ++i) {
        foot::DisplayFrame v{};
        uiView(v);
        if (!strcmp(v.breadcrumb, "CONTROLLER SETTINGS") && !v.editing)
            return;
        uiStep(0, 2);
    }
    std::abort();
}
static void capture(const std::string &dir, const char *name) {
    foot::DisplayFrame v{};
    uiView(v);
    auto item = cJSON_CreateObject();
    cJSON_AddStringToObject(item, "file", name);
    cJSON_AddStringToObject(item, "title", v.title);
    cJSON_AddStringToObject(item, "breadcrumb", v.breadcrumb);
    cJSON_AddBoolToObject(item, "editing", v.editing);
    if (v.screen == foot::Screen::Menu) {
        cJSON_AddStringToObject(item, "selected", v.rows[v.selectedRow]);
        cJSON_AddStringToObject(item, "value", v.values[v.selectedRow]);
        cJSON_AddNumberToObject(item, "kind", static_cast<int>(v.rowKinds[v.selectedRow]));
    }
    cJSON_AddItemToArray(frames, item);
    auto f = fopen((dir + "/" + name + ".ppm").c_str(), "wb");
    assert(f);
    fprintf(f, "P6\n%d %d\n255\n", foot::DisplayWidth, foot::DisplayHeight);
    std::vector<uint16_t> pixels(foot::DisplayWidth * foot::DisplayStripeRows);
    for (int y = 0; y < foot::DisplayHeight; y += foot::DisplayStripeRows) {
        foot::renderDisplayStripe(v, y, foot::DisplayStripeRows, pixels.data());
        for (auto p : pixels) {
            unsigned char rgb[] = {static_cast<unsigned char>(((p >> 11) & 31) * 255 / 31),
                                   static_cast<unsigned char>(((p >> 5) & 63) * 255 / 63),
                                   static_cast<unsigned char>((p & 31) * 255 / 31)};
            fwrite(rgb, 1, 3, f);
        }
    }
    fclose(f);
}
int main(int argc, char **argv) {
    assert(argc == 2);
    const std::string dir = argv[1];
    using K = foot::MenuRowKind;
    frames = cJSON_CreateArray();
    state.saved = foot::defaults();
    state.key = 0;
    auto &sw = state.saved.switches[foot::switchTap(1, 10, 1, true) - 1];
    strcpy(sw.name, "LEAD");
    sw.press.count = 2;
    sw.press.messages[0] = {1, 2, 24, 0, 5};
    sw.press.messages[1] = {0, 3, 17, 127, 5};
    capture(dir, "performance");
    // The main UI task enters setup on an idle encoder click.
    state.setup = true;
    state.draft = state.saved;
    ++state.revision;
    uiStep(0, 0);
    capture(dir, "setup-edit");
    uiStep(0, 1);
    select("switches", K::Navigation); capture(dir, "config-switches");
    uiStep(0, 1);
    select("A", K::Navigation); capture(dir, "switch-list");
    uiStep(0, 1);
    select("press", K::Navigation); capture(dir, "switch-press");
    uiStep(0, 1);
    select("PC24/2", K::Message); capture(dir, "press-list");
    uiStep(0, 1); capture(dir, "message-actions");
    uiStep(0, 1);
    select("PROGRAM", K::Parameter); capture(dir, "pc-editor");
    uiStep(0, 1); capture(dir, "program-edit");
    uiStep(0, 1); // Accept unchanged; editing is not a flash save.
    root();
    select("pedals", K::Navigation); capture(dir, "config-pedals");
    uiStep(0, 1);
    select("1", K::Navigation); capture(dir, "pedal-list");
    uiStep(0, 1);
    select("RESISTOR", K::Parameter); capture(dir, "pedal-settings");
    root();
    select("ladder", K::Navigation); capture(dir, "config-ladder");
    uiStep(0, 1);
    select("IDLE MV", K::Parameter); capture(dir, "ladder-centers");
    root();
    select("LED CHAIN", K::Navigation); capture(dir, "config-leds");
    uiStep(0, 1);
    select("ENABLED", K::Parameter); capture(dir, "led-settings");
    root();
    select("ENCLOSURE", K::Parameter); capture(dir, "config-enclosure");
    uiStep(0, 1); capture(dir, "enclosure-edit");
    uiStep(0, 1);
    uiStep(0, 2); // SETUP
    uiStep(2, 0); capture(dir, "save-exit");
    uiStep(0, 1);
    assert(!state.setup);
    capture(dir, "saved-performance");
    char *json = cJSON_Print(frames);
    auto f = fopen((dir + "/frames.json").c_str(), "w");
    assert(f); fputs(json, f); fclose(f);
    cJSON_free(json); cJSON_Delete(frames);
}
