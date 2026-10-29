#pragma once
#include <array>
// ESP-IDF uses ESP32 GPIO numbers, not Arduino's remapped D/A pin indices.
namespace foot::board {
inline constexpr int Ladder = 1, Pedal1 = 2, Pedal2 = 4; // A0, A1, A3 / ADC1
inline constexpr std::array<int, 3> AdcChannels{0, 1, 3};
inline constexpr int Pedal1Bias = 5, Pedal2Bias = 6; // D2, D3
inline constexpr int EncoderA = 7, EncoderB = 8, EncoderClick = 9; // D4..D6
inline constexpr int LedData = 10; // D7
inline constexpr int LcdClock = 17, LcdDc = 18, LcdCs = 21; // D8, D9, D10
inline constexpr int LcdMosi = 38, LcdReset = 47; // D11, D12
inline constexpr int UsbVbusSense = 11; // A4, through 100k / 150k divider
inline constexpr std::array<int, 15> UsedPins{Ladder, Pedal1, Pedal2, Pedal1Bias, Pedal2Bias,
    EncoderA, EncoderB, EncoderClick, LedData, LcdClock, LcdDc, LcdCs, LcdMosi, LcdReset, UsbVbusSense};
constexpr bool validPins() {
    for (unsigned i = 0; i < UsedPins.size(); ++i) {
        if (UsedPins[i] == 19 || UsedPins[i] == 20 || UsedPins[i] == 0 || UsedPins[i] == 3 ||
            UsedPins[i] == 45 || UsedPins[i] == 46 || UsedPins[i] == 48) return false;
        for (unsigned j = i + 1; j < UsedPins.size(); ++j)
            if (UsedPins[i] == UsedPins[j]) return false;
    }
    return true;
}
static_assert(validPins(), "Nano peripheral pins conflict with USB, straps or onboard LEDs");
}
