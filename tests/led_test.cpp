#include "leds.hpp"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <utility>
#include <vector>
using namespace foot;
static bool black(const LedFrame &f) {
    return std::all_of(f.bytes.begin(), f.bytes.end(), [](uint8_t v) { return v == 0; });
}
struct Trace {
    bool accept = true;
    int sent = 0;
    LedFeedback feedback;
    std::vector<std::pair<int, bool>> events;
};
static bool send(const Message &, uint32_t, void *ctx) {
    auto &t = *static_cast<Trace *>(ctx);
    if (t.accept)
        ++t.sent;
    return t.accept;
}
static void action(int led, bool release, bool toggle, void *ctx) {
    auto &t = *static_cast<Trace *>(ctx);
    t.events.emplace_back(led, release);
    t.feedback.action(led, release, toggle);
}
int main() {
    auto c = defaults();
    LedFeedback feedback;
    feedback.configure(c);
    for (int i = 0; i < MaxSwitches; ++i)
        assert(c.switches[i].led == i + 1);
    assert(!c.leds.enabled && c.leds.brightness == 64);
    feedback.action(1, false);
    assert(black(feedback.frame()));
    c.leds.enabled = true;
    feedback.configure(c);
    feedback.action(1, false);
    auto f = feedback.frame();
    assert(f.bytes[0] == 64 && f.bytes[1] == 64 && f.bytes[2] == 64);
    assert(std::all_of(f.bytes.begin() + 3, f.bytes.end(), [](uint8_t v) { return !v; }));
    feedback.action(1, true);
    f = feedback.frame();
    assert(f.bytes[0] == 64 && f.bytes[1] == 64 && f.bytes[2] == 0);
    feedback.action(0, false);
    feedback.action(11, false);
    assert(f == feedback.frame());
    const uint8_t yellow[6][3] = {{64, 64, 0}, {64, 64, 0}, {0, 64, 64},
                                  {0, 64, 64}, {64, 0, 64}, {64, 0, 64}};
    for (int order = 0; order < 6; ++order) {
        c.leds.colorOrder = order;
        feedback.configure(c);
        feedback.action(10, true);
        f = feedback.frame();
        assert(std::equal(f.bytes.end() - 3, f.bytes.end(), yellow[order]));
    }
    c.switchCount = 6;
    feedback.configure(c);
    assert(black(feedback.frame())); // no stale indicators from inactive switches
    c.leds.brightness = 0;
    feedback.configure(c);
    feedback.action(1, false);
    assert(black(feedback.frame()));
    // Verify MSB-first 24-bit pixels, timing profiles and a 350us low reset.
    std::array<LedPulse, LedSymbols> pulses;
    for (int protocol = 0; protocol < 3; ++protocol) {
        f = {};
        f.protocol = protocol;
        f.bytes[0] = 0x80;
        f.bytes[29] = 1;
        encodeLedFrame(f, pulses);
        assert(pulses[0].highTicks > pulses[1].highTicks);
        assert(pulses[239].highTicks == pulses[0].highTicks);
        for (int i = 0; i < 240; ++i)
            assert(pulses[i].highTicks + pulses[i].lowTicks == (protocol == 2 ? 50 : 25));
        assert(pulses.back().highTicks + pulses.back().lowTicks == 7000);
        assert(pulses[1].highTicks == (protocol == 0 ? 7 : protocol == 1 ? 5 : 10));
        assert(pulses[0].highTicks == (protocol == 0 ? 18 : protocol == 1 ? 12 : 24));
    }
    // A quick physical release must not overtake the delayed press sequence.
    c = defaults();
    c.leds.enabled = true;
    auto &s = c.switches[2];
    s.press.count = 2;
    s.release.count = 1;
    Trace t;
    t.feedback.configure(c);
    Engine engine;
    engine.input(0, c, 0);
    engine.input(3, c, 1);
    engine.input(0, c, 2);
    engine.tick(5, send, &t, action);
    assert(t.events.empty());
    t.accept = false;
    engine.tick(6, send, &t, action);
    assert(t.events.empty() && black(t.feedback.frame()));
    t.accept = true;
    engine.tick(7, send, &t, action);
    assert((t.events == std::vector<std::pair<int, bool>>{{3, false}}));
    assert(t.feedback.frame().bytes[8] == 64); // blue is on for white
    c.switches[2].led = 9;                     // job captured the original mapping
    engine.tick(12, send, &t, action);
    assert(t.events.size() == 1); // additional messages don't retrigger
    engine.tick(17, send, &t, action);
    assert((t.events == std::vector<std::pair<int, bool>>{{3, false}, {3, true}}));
    f = t.feedback.frame();
    assert(f.bytes[6] == 64 && f.bytes[7] == 64 && f.bytes[8] == 0);
    assert(f.bytes[24] == 0 && t.sent == 3);
    t.feedback.clear();
    assert(black(t.feedback.frame()));
    // Empty phases have no performed-message event, including release-only actions.
    c = defaults();
    c.switches[0].release.count = 1;
    t.events.clear();
    engine.reset();
    engine.input(0, c, 20);
    engine.input(1, c, 21);
    engine.tick(30, send, &t, action);
    assert(t.events.empty());
    engine.input(0, c, 31);
    engine.tick(36, send, &t, action);
    assert((t.events == std::vector<std::pair<int, bool>>{{1, true}}));
    t.events.clear();
    engine.input(2, c, 40);
    engine.input(0, c, 41);
    engine.tick(50, send, &t, action);
    assert(t.events.empty());
    puts("LED tests passed: defaults, brightness/order, timing/reset, MIDI success gating, "
         "delayed press/release order, captured assignments, empty actions and reset");
}
