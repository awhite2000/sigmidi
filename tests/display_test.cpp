#include "display.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
using namespace foot;
int main() {
    DisplayWindow w{};
    assert(displayWindow(0, 16, w));
    assert(w.columns[0] == 0 && w.columns[1] == 20 && w.columns[2] == 1 && w.columns[3] == 43);
    assert(w.rows[1] == 0 && w.rows[3] == 15);
    assert(displayWindow(224, 16, w) && w.rows[3] == 239);
    assert(!displayWindow(-1, 16, w) && !displayWindow(240, 1, w));
    assert(!displayWindow(224, 17, w) && !displayWindow(0, 0, w));
    assert(!displayWindow(0, 16, w, 90));
    std::array<uint16_t, DisplayWidth * DisplayStripeRows + 2> invalid{};
    invalid.fill(0xf00f);
    for (int rotation : {-180, 90, 360})
        assert(!prepareDisplayStripe(invalid.data() + 1, 16, rotation));
    assert(!prepareDisplayStripe(nullptr, 16, 0));
    assert(!prepareDisplayStripe(invalid.data() + 1, 0, 0));
    assert(!prepareDisplayStripe(invalid.data() + 1, DisplayStripeRows + 1, 180));
    assert(std::all_of(invalid.begin(), invalid.end(), [](auto p) { return p == 0xf00f; }));
    for (Screen screen : {Screen::Performance, Screen::Menu, Screen::Browser, Screen::Pong}) {
        DisplayFrame v{};
        v.screen = screen;
        v.ble = 2;
        v.activeSwitch = 3;
        strcpy(v.activeLabel, "C");
        std::strcpy(v.title, "ON PRESS");
        std::strcpy(v.switchName, "LEAD");
        std::strcpy(v.action, "PRESS 3 / RELEASE 2 MESSAGES");
        std::strcpy(v.footer, "CLICK: SELECT / HOLD: BACK");
        std::strcpy(v.ssid, "SIGMIDI-A1B2");
        std::strcpy(v.password, "ABCD2345EFGH6789");
        v.rowCount = 7;
        v.totalRows = 11;
        v.firstRow = 4;
        v.selectedRow = 6;
        for (int i = 0; i < MenuRows; ++i)
            snprintf(v.rows[i], sizeof v.rows[i], i % 2 ? "CC17:127/3" : "PC24/2");
        v.rowKinds[0] = v.rowKinds[1] = MenuRowKind::Message;
        v.rowKinds[2] = v.rowKinds[3] = MenuRowKind::Parameter;
        strcpy(v.rows[2], "CONTROL");
        strcpy(v.values[2], "127");
        strcpy(v.rows[3], "NAME");
        strcpy(v.values[3], "ABCDEFGHIJKLMNOPQRSTUVWX");
        v.rowKinds[6] = MenuRowKind::Action;
        strcpy(v.rows[6], "MOVE DOWN");
        v.editing = true;
        v.pedals[0] = {127, 11, true};
        v.pedals[1] = {32, 7, true};
        v.pedals[1].needsMove = true;
        v.pedals[1].valueVisible = false;
        std::vector<uint16_t> full(DisplayWidth * DisplayHeight);
        renderDisplayStripe(v, 0, DisplayHeight, full.data());
        assert(*std::max_element(full.begin(), full.end()) != 0);
        std::array<uint16_t, DisplayWidth * DisplayStripeRows + 2> stripe{};
        for (int y = 0; y < DisplayHeight; y += DisplayStripeRows) {
            stripe.fill(0xf00f);
            renderDisplayStripe(v, y, DisplayStripeRows, stripe.data() + 1);
            assert(stripe.front() == 0xf00f && stripe.back() == 0xf00f);
            assert(
                std::equal(stripe.begin() + 1, stripe.end() - 1, full.begin() + y * DisplayWidth));
        }
        // Reconstruct physical controller RAM from the exact window/payload path.
        // Uneven 7-row transfers also exercise the short final stripe and both axes.
        for (int rotation : {0, 180}) {
            std::vector<uint16_t> physical(full.size());
            for (int y = 0; y < DisplayHeight; y += 7) {
                int rows = std::min(7, DisplayHeight - y);
                stripe.fill(0xf00f);
                renderDisplayStripe(v, y, rows, stripe.data() + 1);
                assert(displayWindow(y, rows, w, rotation));
                assert(prepareDisplayStripe(stripe.data() + 1, rows, rotation));
                assert(stripe.front() == 0xf00f && stripe[1 + DisplayWidth * rows] == 0xf00f);
                int firstRow = (int(w.rows[0]) << 8) | w.rows[1];
                int lastRow = (int(w.rows[2]) << 8) | w.rows[3];
                assert(lastRow - firstRow + 1 == rows && firstRow >= 0 && lastRow < DisplayHeight);
                assert(w.columns[1] == 20 && w.columns[2] == 1 && w.columns[3] == 43);
                for (int i = 0; i < DisplayWidth * rows; ++i) {
                    auto wire = stripe[i + 1];
                    physical[firstRow * DisplayWidth + i] = (wire >> 8) | (wire << 8);
                }
            }
            for (size_t i = 0; i < full.size(); ++i)
                assert(physical[i] == full[rotation == 180 ? full.size() - 1 - i : i]);
        }
    }
    // Before first movement, neither the digits nor bar may reveal the sampled position.
    for (int input = 0; input < 2; ++input) {
        DisplayFrame pending{};
        auto &pedal = pending.pedals[input];
        pedal.enabled = pedal.needsMove = true;
        pedal.valueVisible = false;
        std::vector<uint16_t> low(DisplayWidth * DisplayHeight), high(low.size());
        pedal.value = 0;
        renderDisplayStripe(pending, 0, DisplayHeight, low.data());
        pedal.value = 127;
        renderDisplayStripe(pending, 0, DisplayHeight, high.data());
        assert(low == high);
        pedal.valueVisible = true;
        pedal.needsMove = false;
        pedal.value = 0;
        renderDisplayStripe(pending, 0, DisplayHeight, low.data());
        pedal.value = 127;
        renderDisplayStripe(pending, 0, DisplayHeight, high.data());
        assert(low != high);
    }
    puts("Display tests passed: hidden pending pedal values/bars, exact 0/180-degree SPI output, 280x240 offsets, stripe/frame "
         "equivalence, clipping guards, "
         "four screens");
}
