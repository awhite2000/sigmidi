#include "core.hpp"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
using namespace foot;
static bool collect(const Message &m, uint32_t, void *p) {
    ((std::vector<int> *)p)->push_back(m.value);
    return true;
}
int main() {
    auto c = defaults();
    char error[100];
    assert(validate(c, error, sizeof error));
    auto invalid = c;
    invalid.switches[0].press.count = 33;
    assert(!validate(invalid, error, sizeof error));
    invalid = c;
    invalid.pedals[0].maxOhms = NAN;
    assert(!validate(invalid, error, sizeof error));
    invalid = c;
    invalid.ladder[2] = invalid.ladder[1] + 5;
    assert(!validate(invalid, error, sizeof error));
    // Every supported count decodes only its installed taps, preserves idle,
    // and sends ordered press/release messages on the last active switch.
    assert(std::fabs(c.ladder[1] - 286.95652f) < .001f);
    assert(std::fabs(c.ladder[10] - 1320.0f) < .001f);
    for (int count = MinSwitches; count <= MaxSwitches; ++count) {
        auto variant = defaults();
        variant.switchCount = count;
        variant.ladderLayout = 0;
        assert(validate(variant, error, sizeof error));
        for (int i = 0; i <= count; ++i) {
            assert(decodeLadder(variant, variant.ladder[i]) == i);
            assert(decodeLadder(variant, variant.ladder[i] + variant.windowMv - .01f) == i);
            assert(decodeLadder(variant, variant.ladder[i] + variant.windowMv + .01f) == -1);
        }
        for (int i = count + 1; i <= MaxSwitches; ++i)
            assert(decodeLadder(variant, variant.ladder[i]) == -1);
        assert(decodeLadder(variant, NAN) == -1);
        auto &last = variant.switches[count - 1];
        last.press.count = last.release.count = 1;
        last.press.messages[0] = {1, 2, 24, 77, 5};
        last.release.messages[0] = {0, 3, 17, 55, 5};
        Engine engine;
        std::vector<int> sent;
        engine.input(0, variant, 0);
        engine.input(count + 1, variant, 1); // must not arm a hidden mapping
        engine.input(count, variant, 2);     // invalid code requires idle again
        engine.tick(20, collect, &sent);
        assert(sent.empty());
        engine.input(0, variant, 21);
        engine.input(count, variant, 22);
        engine.input(0, variant, 23);
        engine.tick(27, collect, &sent);
        engine.tick(32, collect, &sent);
        assert((sent == std::vector<int>{77, 55}));
        engine.reset();
        engine.input(0, variant, 40);
        engine.input(1000000, variant, 41); // bounds guard, no array access
        engine.tick(99, collect, &sent);
        assert(sent.size() == 2);
    }
    for (int count : {-1, 0, 3, 5, 11, 1000000}) {
        invalid = c;
        invalid.switchCount = count;
        assert(!validate(invalid, error, sizeof error));
        assert(decodeLadder(invalid, invalid.ladder[0]) == -1);
    }
    invalid = c;
    invalid.switchCount = 6;
    invalid.ladder[10] = invalid.ladder[1]; // inactive centers do not collide
    assert(validate(invalid, error, sizeof error));
    invalid.switchCount = 10;
    assert(!validate(invalid, error, sizeof error));
    uint8_t data[5];
    Message m;
    m.channel = 16;
    m.number = 127;
    m.value = 127;
    assert(midiPacket(m, 8191, data) == 5);
    assert(data[0] == 0xbf && data[1] == 0xff && data[2] == 0xbf && data[3] == 127 &&
           data[4] == 127);
    m.type = 1;
    assert(midiPacket(m, 8192, data) == 4 && data[0] == 0x80 && data[1] == 0x80 && data[2] == 0xcf);
    for (int i = 0; i < 11; i++)
        assert(decodeLadder(c, c.ladder[i]) == i);
    assert(decodeLadder(c, 1800) == -1);
    Debouncer d;
    assert(d.update(0, 0, 10) == -1);
    assert(d.update(1, 5, 10) == -1);
    assert(d.update(0, 8, 10) == -1);
    assert(d.update(0, 18, 10) == 0);
    assert(d.update(1, 20, 10) == 0);
    assert(d.update(1, 30, 10) == 1);
    assert(d.update(-1, 31, 10) == 1);
    assert(d.update(-1, 81, 10) == -1);
    Pedal p;
    p.maxOhms = 5000;
    assert(pedalValue(p, 0) == 0);
    assert(pedalValue(p, 1100.0f) == 127); // 5k to GND with 10k bias at 3.3V
    assert(pedalValue(p, 3300) == -1);
    p.maxOhms = 10000;
    assert(pedalValue(p, 1650) == 127);
    assert(pedalValue(p, 1100) == 64);
    p.resistor = false;
    p.heel = 100;
    p.toe = 3100;
    assert(pedalValue(p, 100) == 0);
    assert(pedalValue(p, 3100) == 127);
    p.invert = true;
    assert(pedalValue(p, 3100) == 0);
    p.invert = false;
    p.logarithmic = true;
    int previous = -1;
    for (int i = 0; i <= 100; i++) {
        int value = pedalValue(p, 100 + i * 30);
        assert(value >= previous);
        previous = value;
    }
    p.logarithmic = false;
    p.heel = 0;
    p.toe = 3300.0f * 10000 / (5100 + 10000);
    assert(pedalValue(p, p.toe) == 127); // full travel of a passive 10k pot
    assert(pedalValue(p, p.toe / 2) == 64);
    // Raw browser-captured passive-pot endpoints must span the complete MIDI range.
    p.heel = 120;
    p.toe = 2185;
    assert(pedalValue(p, 120) == 0);
    assert(pedalValue(p, 1152.5f) == 64);
    assert(pedalValue(p, 2185) == 127);
    auto calibrated = defaults();
    char pedalError[80];
    for (auto &input : calibrated.pedals) {
        input = p;
        input.toe = 3000.25f; // Valid ADC endpoint above the old 1.5x overflow threshold.
        assert(pedalValue(input, input.toe) == 127);
    }
    assert(validate(calibrated, pedalError, sizeof pedalError));
    assert(Message{}.delayMs == 5);
    c.switches[0].press.messages[0].delayMs = 0;
    c.switches[0].release.messages[0].delayMs = 0;
    c.switches[0].press.count = 2;
    c.switches[0].press.messages[0].value = 11;
    c.switches[0].press.messages[1].value = 22;
    c.switches[0].press.messages[1].delayMs = 20;
    c.switches[0].release.count = 1;
    c.switches[0].release.messages[0].value = 33;
    Engine e;
    std::vector<int> out;
    e.reset();
    e.input(1, c, 0);
    e.tick(0, collect, &out);
    assert(out.empty());
    e.input(0, c, 1);
    e.input(1, c, 2);
    e.tick(2, collect, &out);
    assert((out == std::vector<int>{11}));
    e.input(0, c, 3);
    c.switches[0].release.messages[0].value = 99; // snapshot must retain 33
    e.tick(21, collect, &out);
    assert(out.size() == 1);
    e.tick(22, collect, &out);
    e.tick(23, collect, &out);
    assert((out == std::vector<int>{11, 22, 33}));
    assert(e.idle());
    // A second press on the same switch cannot overtake a delayed first release.
    out.clear();
    e.reset();
    c.switches[0].release.messages[0].delayMs = 100;
    e.input(0, c, 0);
    e.input(1, c, 1);
    e.tick(1, collect, &out);
    e.input(0, c, 2);
    e.input(1, c, 3);
    e.tick(3, collect, &out);
    assert(out.size() == 1);
    e.tick(21, collect, &out);
    e.tick(120, collect, &out);
    assert(out.size() == 2);
    e.tick(121, collect, &out);
    assert(out.back() == 99);
    e.tick(122, collect, &out);
    assert(out.back() == 11);
    // Invalid ladder state disarms until idle; reset drops all delayed actions.
    e.reset();
    out.clear();
    e.input(-1, c, 200);
    e.input(2, c, 201);
    e.tick(201, collect, &out);
    assert(out.empty());
    assert(e.idle());
    // Every switch supports independent ordered lists on both edges, mixing
    // CC/PC messages and channels. Release during the press list stays ordered.
    for (int sw = 0; sw < MaxSwitches; ++sw) {
        auto lists = defaults();
        auto &mapping = lists.switches[sw];
        mapping.press.count = mapping.release.count = 3;
        for (int i = 0; i < 3; ++i) {
            mapping.press.messages[i] = {i % 2, i + 1, 20 + i, 40 + i, 5};
            mapping.release.messages[i] = {(i + 1) % 2, 16 - i, 70 + i, 10 + i, 5};
        }
        std::vector<Message> sent;
        auto send = [](const Message &message, uint32_t, void *context) {
            static_cast<std::vector<Message> *>(context)->push_back(message);
            return true;
        };
        e.reset();
        e.input(0, lists, 0);
        e.input(sw + 1, lists, 1);
        e.input(0, lists, 2);
        for (uint32_t time = 2; time <= 40; ++time)
            e.tick(time, send, &sent);
        assert(sent.size() == 6 && e.idle());
        for (int i = 0; i < 6; ++i) {
            auto expected = i < 3 ? mapping.press.messages[i] : mapping.release.messages[i - 3];
            assert(sent[i].type == expected.type && sent[i].channel == expected.channel &&
                   sent[i].number == expected.number && sent[i].value == expected.value);
        }
    }
    puts("Core tests passed: validation, packet encoding, calibration mapping, debounce, "
         "sequencing, snapshots, FIFO, reset");
}
