#include "core.hpp"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
namespace foot {
Config defaults() {
    Config c;
    for (int i = 0; i < MaxSwitches; i++) {
        char label[8];
        switchLabel(c.ladderLayout, c.switchCount, i + 1, label, sizeof label);
        snprintf(c.switches[i].name, 25, "Switch %s", label);
        c.switches[i].led = i + 1;
        float r = (i + 1) * 1000.0f;
        r = r * 20000 / (r + 20000);
        c.ladder[i + 1] = 3300 * r / (10000 + r);
    }
    c.ladder[0] = 2200;
    return c;
}
bool validSwitchCount(int layout, int count) {
    return (layout == 0 || layout == 1) && count >= MinSwitches && count <= MaxSwitches &&
           (layout == 0 || count % 2 == 0);
}
int switchTap(int layout, int count, int number, bool mirrored) {
    if (!validSwitchCount(layout, count) || number < 1 || number > count)
        return -1;
    if (mirrored) {
        // Preserve upper/lower row membership. Odd linear counts put the extra switch above.
        int upper = (count + 1) / 2;
        number = number <= upper ? upper + 1 - number : upper + 1 + count - number;
    }
    if (layout == 0)
        return number;
    int extensions = (count - 4) / 2, rowSize = count / 2;
    bool lower = number > rowSize;
    int column = (number - 1) % rowSize;
    if (column < extensions)
        return 5 + 2 * (extensions - 1 - column) + (lower ? 1 : 0);
    return column - extensions + 1 + (lower ? 2 : 0);
}
int switchNumber(int layout, int count, int tap, bool mirrored) {
    if (!validSwitchCount(layout, count) || tap < 0 || tap > count)
        return -1;
    if (tap == 0)
        return 0;
    for (int n = 1; n <= count; ++n)
        if (switchTap(layout, count, n, mirrored) == tap)
            return n;
    return -1;
}
void switchLabel(int layout, int count, int tap, char *out, size_t size) {
    int position = switchNumber(layout, count, tap);
    if (position <= 0) {
        snprintf(out, size, "%s", position == 0 ? "IDLE" : "--");
    } else if (layout == 0) {
        snprintf(out, size, "%d", tap);
    } else if (position <= count / 2) {
        snprintf(out, size, "%c", 'A' + count / 2 - position);
    } else {
        snprintf(out, size, "%d", count - position + 1);
    }
}
static bool finite(float v) { return std::isfinite(v); }
bool validate(const Config &c, char *e, size_t n) {
    auto fail = [&](const char *s) {
        snprintf(e, n, "%s", s);
        return false;
    };
    if (c.version != 4)
        return fail("Unsupported configuration version");
    if (c.enclosureVariant < 0 || c.enclosureVariant > 1)
        return fail("Enclosure variant must be Right or Left");
    if (!validSwitchCount(c.ladderLayout, c.switchCount))
        return fail("Modular: 4/6/8/10 switches; linear: 4 to 10");
    if (c.debounceMs < 2 || c.debounceMs > 100 || c.pcOffset < 0 || c.pcOffset > 1)
        return fail("Invalid global settings");
    if (!finite(c.windowMv) || c.windowMv < 3 || c.windowMv > 100)
        return fail("Invalid ladder window");
    if (c.leds.brightness < 0 || c.leds.brightness > 255 || c.leds.colorOrder < 0 ||
        c.leds.colorOrder > 5 || c.leds.protocol < 0 || c.leds.protocol > 2)
        return fail("Invalid LED chain settings");
    for (int i = 0; i <= MaxSwitches; i++) {
        if (!finite(c.ladder[i]) || c.ladder[i] < 0 || c.ladder[i] > 3300)
            return fail("Invalid ladder center");
        for (int j = 0; i <= c.switchCount && j < i; j++)
            if (std::fabs(c.ladder[i] - c.ladder[j]) <= 2 * c.windowMv)
                return fail("Ladder windows overlap");
    }
    int totalMessages = 0;
    for (auto &s : c.switches) {
        if (s.led < 0 || s.led > MaxSwitches)
            return fail("LED assignment must be 0 to 10");
        if (!memchr(s.name, 0, sizeof s.name))
            return fail("Switch name too long");
        for (auto seq : {&s.press, &s.release}) {
            if (seq->count < 0 || seq->count > 32)
                return fail("Maximum 32 messages per edge");
            totalMessages += seq->count;
            if (totalMessages > 128)
                return fail("Maximum 128 messages across all switches");
            for (int i = 0; i < seq->count; i++) {
                auto m = seq->messages[i];
                if (m.type < 0 || m.type > 1 || m.channel < 1 || m.channel > 16 || m.number < 0 ||
                    m.number > 127 || m.value < 0 || m.value > 127 || m.delayMs < 0 ||
                    m.delayMs > 10000)
                    return fail("Invalid MIDI message");
            }
        }
    }
    for (auto p : c.pedals) {
        if (p.channel < 1 || p.channel > 16 || p.cc < 0 || p.cc > 127 || p.outMin < 0 ||
            p.outMin > 127 || p.outMax < 0 || p.outMax > 127 || !finite(p.maxOhms) ||
            p.maxOhms <= 0 || p.maxOhms > 10000 || !finite(p.heel) || !finite(p.toe) ||
            p.heel < 0 || p.toe > 3300 || p.toe - p.heel < 50 || !finite(p.curve) ||
            p.curve < 0.1f || p.curve > 100)
            return fail("Invalid pedal settings");
    }
    return true;
}
size_t midiPacket(const Message &m, uint32_t ms, uint8_t out[5]) {
    ms &= 8191;
    out[0] = 0x80 | ((ms >> 7) & 63);
    out[1] = 0x80 | (ms & 127);
    out[2] = (m.type ? 0xc0 : 0xb0) | (m.channel - 1);
    out[3] = m.number;
    out[4] = m.value;
    return m.type ? 4 : 5;
}
int decodeLadder(const Config &c, float mv) {
    if (!validSwitchCount(c.ladderLayout, c.switchCount) || !finite(mv))
        return -1;
    for (int i = 0; i <= c.switchCount; i++)
        if (std::fabs(mv - c.ladder[i]) <= c.windowMv)
            return i;
    return -1;
}
int pedalValue(const Pedal &p, float adc, int previous) {
    // Passive pedal TIP is wired directly to the ADC; no buffer/divider gain.
    float v = adc, x;
    if (!finite(v) || v < 0 || v > 3400)
        return -1;
    if (p.resistor) {
        if (v >= 3200)
            return -1;
        float r = 10000 * v / (3300 - v);
        x = r / p.maxOhms;
    } else
        x = (v - p.heel) / (p.toe - p.heel);
    x = std::clamp(x, 0.0f, 1.0f);
    if (p.invert)
        x = 1 - x;
    if (p.logarithmic)
        x = std::log1p(p.curve * x) / std::log1p(p.curve);
    float scaled = p.outMin + x * (p.outMax - p.outMin);
    if (x > 0 && x < 1 && previous >= 0 && std::fabs(scaled - previous) < 0.75f)
        return previous;
    return std::clamp((int)std::lround(scaled), 0, 127);
}
int Debouncer::update(int code, uint32_t now, int delay) {
    if (code != candidate) {
        candidate = code;
        since = now;
    }
    if ((uint32_t)(now - since) >= (uint32_t)(code < 0 ? 50 : delay))
        stable = candidate;
    return stable;
}
void Engine::reset() {
    for (auto &j : jobs)
        j.used = false;
    active = -1;
    armed = false;
}
bool Engine::idle() const {
    for (auto &j : jobs)
        if (j.used)
            return false;
    return true;
}
void Engine::input(int code, const Config &c, uint32_t now) {
    if (!validSwitchCount(c.ladderLayout, c.switchCount) || code > c.switchCount || code < -1)
        code = -1;
    if (active >= 0 && code != jobs[active].sw + 1) {
        auto &j = jobs[active];
        j.released = true;
        if (j.index >= j.press.count) {
            j.index = j.press.count;
            j.due = now + (j.release.count ? j.release.messages[0].delayMs : 0);
        }
        active = -1;
    }
    if (code == 0) {
        armed = true;
        return;
    }
    if (code < 0) {
        armed = false;
        return;
    }
    if (!armed)
        return;
    armed = false;
    int slot = -1;
    for (int i = 0; i < (int)jobs.size(); i++)
        if (!jobs[i].used) {
            slot = i;
            break;
        }
    if (slot < 0) {
        rejected++;
        return;
    }
    auto &j = jobs[slot];
    j = Job{};
    j.used = true;
    j.order = nextOrder++;
    j.sw = code - 1;
    j.press = c.switches[j.sw].press;
    j.release = c.switches[j.sw].release;
    j.led = c.switches[j.sw].led;
    j.due = now + (j.press.count ? j.press.messages[0].delayMs : 0);
    active = slot;
}
void Engine::tick(uint32_t now, Send send, void *ctx, Action action) {
    Job *chosen = nullptr;
    for (auto &j : jobs) {
        if (!j.used)
            continue;
        int total = j.press.count + j.release.count;
        if (j.released && j.index >= total) {
            j.used = false;
            continue;
        }
        if (j.index >= j.press.count && !j.released)
            continue;
        bool blocked = false;
        for (auto &prior : jobs)
            if (prior.used && prior.sw == j.sw && prior.order < j.order)
                blocked = true;
        if (blocked || (int32_t)(now - j.due) < 0)
            continue;
        if (!chosen || (int32_t)(j.due - chosen->due) < 0 ||
            (j.due == chosen->due && j.order < chosen->order))
            chosen = &j;
    }
    if (!chosen)
        return;
    auto &j = *chosen;
    auto &m = j.index < j.press.count ? j.press.messages[j.index]
                                      : j.release.messages[j.index - j.press.count];
    if (!send(m, now, ctx))
        return;
    if (action && (j.index == 0 || j.index == j.press.count))
        action(j.led, j.index >= j.press.count, ctx);
    j.index++;
    int total = j.press.count + j.release.count;
    if (j.index < j.press.count)
        j.due = now + j.press.messages[j.index].delayMs;
    else if (j.index < total)
        j.due = now + j.release.messages[j.index - j.press.count].delayMs;
    else if (j.released)
        j.used = false;
}
} // namespace foot
