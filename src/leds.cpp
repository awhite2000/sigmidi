#include "leds.hpp"
#include <algorithm>

namespace foot {
void LedFeedback::configure(const Config &c) {
    bool changed = count != c.switchCount || settings.enabled != c.leds.enabled ||
                   settings.brightness != c.leds.brightness ||
                   settings.colorOrder != c.leds.colorOrder || settings.protocol != c.leds.protocol;
    for (int i = 0; i < MaxSwitches; ++i) {
        changed |= mapping[i] != c.switches[i].led;
        mapping[i] = c.switches[i].led;
    }
    settings = c.leds;
    count = c.switchCount;
    if (changed)
        clear();
}
void LedFeedback::action(int physicalLed, bool release, bool toggle) {
    if (settings.enabled && physicalLed >= 1 && physicalLed <= MaxSwitches)
        phases[physicalLed - 1] = release ? (toggle ? 0 : 2) : 1;
}
LedFrame LedFeedback::frame() const {
    LedFrame result;
    result.protocol = settings.protocol;
    static constexpr uint8_t orders[6][3] = {{0, 1, 2}, {1, 0, 2}, {2, 0, 1},
                                             {2, 1, 0}, {0, 2, 1}, {1, 2, 0}};
    int order = std::clamp(settings.colorOrder, 0, 5);
    uint8_t brightness = std::clamp(settings.brightness, 0, 255);
    if (settings.enabled)
        for (int i = 0; i < MaxSwitches; ++i) {
            const uint8_t rgb[] = {uint8_t(phases[i] ? brightness : 0),
                                   uint8_t(phases[i] ? brightness : 0),
                                   uint8_t(phases[i] == 1 ? brightness : 0)};
            for (int c = 0; c < 3; ++c)
                result.bytes[i * 3 + c] = rgb[orders[order][c]];
        }
    return result;
}
void encodeLedFrame(const LedFrame &frame, std::array<LedPulse, LedSymbols> &out) {
    // Pololu 2535: 0=0.35/0.90us, 1=0.90/0.35us; RGB, 800kbit/s.
    // Older two-speed WS2811 uses 0=0.25/1.00us, 1=0.60/0.65us at 800K.
    static constexpr LedPulse zero[] = {{7, 18}, {5, 20}, {10, 40}};
    static constexpr LedPulse one[] = {{18, 7}, {12, 13}, {24, 26}};
    int protocol = std::clamp(frame.protocol, 0, 2), at = 0;
    for (uint8_t byte : frame.bytes)
        for (int bit = 7; bit >= 0; --bit)
            out[at++] = byte & (1 << bit) ? one[protocol] : zero[protocol];
    // 350us reset satisfies both the older >50us and newer >280us specifications.
    out[at] = {3500, 3500};
}
} // namespace foot
