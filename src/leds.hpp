#pragma once
#include "core.hpp"

namespace foot {
inline constexpr const char *LedOrders[] = {"RGB", "GRB", "BRG", "BGR", "RBG", "GBR"};
inline constexpr const char *LedProtocols[] = {"2535", "OLD 800K", "OLD 400K"};
constexpr int LedDataGpio = 16, LedBytes = MaxSwitches * 3, LedSymbols = LedBytes * 8 + 1;
constexpr uint32_t LedRefreshMs = 250;
struct LedFrame {
    std::array<uint8_t, LedBytes> bytes{};
    int protocol = 0;
    bool operator==(const LedFrame &other) const {
        return protocol == other.protocol && bytes == other.bytes;
    }
};
// RMT durations at 20MHz (50ns ticks). Final symbol has both levels low.
struct LedPulse {
    uint16_t highTicks = 0, lowTicks = 0;
};
void encodeLedFrame(const LedFrame &, std::array<LedPulse, LedSymbols> &);
class LedFeedback {
    std::array<uint8_t, MaxSwitches> phases{};
    std::array<int, MaxSwitches> mapping{};
    LedConfig settings;
    int count = 0;

  public:
    void configure(const Config &); // clear latched colors when saved settings change
    void clear() { phases.fill(0); }
    void action(int physicalLed, bool release);
    LedFrame frame() const;
};
} // namespace foot
