#pragma once
#include "encoder.hpp"
#include <cstdint>
namespace foot {
enum class PongPhase { Ready, Playing, Point, Finished };
struct PongFrame {
    static constexpr int Top = 45, Bottom = 207, PaddleHeight = 34;
    PongPhase phase = PongPhase::Ready;
    float player = 126, computer = 126, ballX = 140, ballY = 126;
    int playerScore = 0, computerScore = 0;
};
class HiddenPong {
public:
    // True consumes this input (including the long press that exits the game).
    bool update(bool performance, const EncoderInput &, int click, uint32_t now);
    bool active() const { return opened; }
    const PongFrame &frame() const { return view; }
private:
    bool opened = false;
    int gestureRuns = 0, lastDirection = 0;
    uint32_t gestureStarted = 0, gestureLast = 0, lastTick = 0, pointAt = 0;
    uint32_t randomState = 0x5349474d;
    PongFrame view;
    float vx = 0, vy = 0, aim = 0;
    void resetGesture();
    void restart(uint32_t now);
    void serve(int direction);
    void step(uint32_t now);
    float randomOffset();
};
} // namespace foot
