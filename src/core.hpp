#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
namespace foot {
constexpr int MinSwitches = 4, MaxSwitches = 10, MaxMessages = 32;
constexpr int MaxTotalMessages = 128;
enum PcMode { Static = 0, Increment = 1, Decrement = 2 };
struct Message {
    int type = 0, channel = 1, number = 0, value = 0, delayMs = 5;
    int pcMode = Static, counterId = 0;
}; // 0 CC, 1 PC
struct Sequence {
    int count = 0;
    std::array<Message, MaxMessages> messages{};
};
struct Switch {
    char name[25]{};
    Sequence press, release;
    bool toggle = false; // alternate Press/Release lists on successive physical presses
    int led = 0; // physical pixel 1..10, 0 disables this switch's indicator
};
struct LedConfig {
    bool enabled = false;
    int brightness = 64, colorOrder = 0, protocol = 0;
};
struct Pedal {
    bool enabled = false, resistor = true, invert = false, logarithmic = false;
    int channel = 1, cc = 11, outMin = 0, outMax = 127;
    float maxOhms = 10000, heel = 0, toe = 3300, curve = 9;
};
struct Config {
    int version = 6, switchCount = MaxSwitches, debounceMs = 10, pcOffset = 0;
    int ladderLayout = 1;     // 0 legacy tap order, 1 modular base + extension pairs
    int enclosureVariant = 1; // Default Left; 0 Right, 1 Left (mirrored order and 180-degree LCD)
    bool leftVariant() const { return enclosureVariant == 1; }
    std::array<Switch, MaxSwitches> switches{};
    std::array<Pedal, 2> pedals{};
    std::array<float, MaxSwitches + 1> ladder{};
    float windowMv = 20;
    LedConfig leds;
    int nextCounterId = 1; // Monotonic message identity; never derived from list position.
};
Config defaults();
bool validSwitchCount(int layout, int count);
// Internal browsing positions are row-first; stored mappings use permanent taps.
int switchTap(int layout, int count, int number, bool mirrored = false); // 1-based; -1 invalid
int switchNumber(int layout, int count, int tap, bool mirrored = false); // position; idle 0
// Labels belong to permanent taps and never change when the panel is mirrored.
void switchLabel(int layout, int count, int tap, char *out, size_t size);

bool validate(const Config &, char *error, size_t size);
bool assignCounterIds(Config &); // Normalize new/imported dynamic PC messages with id=0.
size_t midiPacket(const Message &, uint32_t ms, uint8_t out[5]);
int decodeLadder(const Config &, float mv); // -1 invalid, 0 idle, permanent taps T1..TN
int pedalValue(const Pedal &, float adcMv, int previous = -1); // -1 invalid
class Debouncer {
    int candidate = -1, stable = -1;
    uint32_t since = 0;

  public:
    int update(int code, uint32_t now, int delay);
    void reset() {
        candidate = stable = -1;
        since = 0;
    }
};
using Send = bool (*)(const Message &, uint32_t, void *);
using Action = void (*)(int led, bool release, bool toggle, void *);
class Engine {
    struct Job {
        bool used = false, released = false, toggle = false, toggleOff = false;
        int sw = 0, index = 0, led = 0;
        uint32_t due = 0;
        uint64_t order = 0;
        Sequence press, release;
    };
    std::array<Job, 16> jobs{};
    std::array<bool, MaxSwitches> toggled{};
    int active = -1;
    bool armed = false;
    uint64_t nextOrder = 0;

  public:
    unsigned rejected = 0;
    void reset();
    void input(int code, const Config &, uint32_t now);
    void tick(uint32_t now, Send, void *, Action = nullptr);
    bool idle() const;
};
} // namespace foot
