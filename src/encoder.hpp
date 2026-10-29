#pragma once
#include <algorithm>
#include <cstdint>
namespace foot {
// Keep direction changes as well as the net displacement: a fast right-left
// movement can otherwise disappear between display refreshes.
struct EncoderInput {
    static constexpr int Capacity = 32;
    int rotation = 0, count = 0;
    int8_t turns[Capacity]{};
    bool overflow = false;
};
class EncoderTurns {
    EncoderInput pending;
public:
    // Caller protects push/read with the encoder's ISR critical section.
    void push(int direction) {
        pending.rotation = std::clamp(pending.rotation + direction, -20, 20);
        if (pending.count < EncoderInput::Capacity)
            pending.turns[pending.count++] = static_cast<int8_t>(direction);
        else
            pending.overflow = true;
    }
    void read(EncoderInput &input) {
        input = pending;
        pending = {};
    }
};
} // namespace foot
