#include "pong.hpp"
#include <algorithm>
#include <cmath>
namespace foot {
namespace {
constexpr float HalfPaddle = PongFrame::PaddleHeight / 2.0f, BallRadius = 3;
// The first hit raises the original horizontal speed from 145 to 155 px/s.
// Scale ball motion, acceleration and the opponent together so its first full
// 234-pixel crossing takes four seconds, preserving angles and relative difficulty.
constexpr float SpeedScale = 234.0f / (155.0f * 4.0f);
constexpr float MaxHorizontalSpeed = 234.0f / 2.0f; // two-second fastest crossing
float paddle(float y) {
    return std::clamp(y, PongFrame::Top + HalfPaddle, PongFrame::Bottom - HalfPaddle);
}
}
void HiddenPong::resetGesture() {
    gestureRuns = lastDirection = 0;
}
float HiddenPong::randomOffset() {
    randomState ^= randomState << 13;
    randomState ^= randomState >> 17;
    randomState ^= randomState << 5;
    return int(randomState % 1001) / 500.0f - 1.0f;
}
void HiddenPong::serve(int direction) {
    view.ballX = 140;
    view.ballY = 126;
    vx = direction * 145 * SpeedScale;
    vy = randomOffset() * 75 * SpeedScale;
    if (std::fabs(vy) < 35 * SpeedScale)
        vy = (vy < 0 ? -35 : 35) * SpeedScale;
    aim = randomOffset() * 24;
}
void HiddenPong::restart(uint32_t now) {
    view = {};
    view.phase = PongPhase::Playing;
    lastTick = now;
    serve(-1);
}
bool HiddenPong::update(bool performance, const EncoderInput &input, int click, uint32_t now) {
    if (!performance) {
        opened = false;
        resetGesture();
        return false;
    }
    if (opened) {
        if (click == 2) {
            opened = false;
            resetGesture();
            return true;
        }
        if (click == 1)
            restart(now);
        view.player = paddle(view.player + std::clamp(input.rotation, -20, 20) * 9);
        // Fixed 10 ms physics, with bounded catch-up after a delayed LCD transfer.
        uint32_t elapsed = now - lastTick;
        if (elapsed > 250)
            lastTick = now - 250;
        while (uint32_t(now - lastTick) >= 10) {
            lastTick += 10;
            step(lastTick);
        }
        return true;
    }
    if (click || input.overflow) {
        resetGesture();
        return false;
    }
    if (gestureRuns && (uint32_t(now - gestureLast) > 600 ||
                        uint32_t(now - gestureStarted) > 4000))
        resetGesture();
    for (int i = 0; i < input.count; ++i) {
        int direction = input.turns[i];
        if (direction == lastDirection) {
            // Several detents in one direction count as one movement, not a pair.
            gestureLast = now;
            continue;
        }
        if (!gestureRuns && direction != 1)
            continue;
        if (!gestureRuns)
            gestureStarted = now;
        lastDirection = direction;
        gestureLast = now;
        if (++gestureRuns == 8) {
            opened = true;
            view = {};
            lastTick = now;
            randomState ^= now;
            if (!randomState)
                randomState = 1;
            resetGesture();
            return true;
        }
    }
    return false;
}
void HiddenPong::step(uint32_t now) {
    if (view.phase == PongPhase::Point) {
        if (uint32_t(now - pointAt) >= 800) {
            view.phase = PongPhase::Playing;
            serve(vx < 0 ? -1 : 1);
        }
        return;
    }
    if (view.phase != PongPhase::Playing)
        return;
    // A speed-limited opponent with a varying aim can miss; it cannot teleport.
    float target = vx > 0 ? view.ballY + aim : 126;
    view.computer = paddle(view.computer +
                          std::clamp(target - view.computer, -1.05f * SpeedScale, 1.05f * SpeedScale));
    float previousX = view.ballX;
    view.ballX += vx * 0.01f;
    view.ballY += vy * 0.01f;
    if (view.ballY < PongFrame::Top + BallRadius) {
        view.ballY = 2 * (PongFrame::Top + BallRadius) - view.ballY;
        vy = std::fabs(vy);
    } else if (view.ballY > PongFrame::Bottom - BallRadius) {
        view.ballY = 2 * (PongFrame::Bottom - BallRadius) - view.ballY;
        vy = -std::fabs(vy);
    }
    bool left = vx < 0 && previousX >= 23 && view.ballX <= 23;
    bool right = vx > 0 && previousX <= 257 && view.ballX >= 257;
    float center = left ? view.player : view.computer;
    if ((left || right) && std::fabs(view.ballY - center) <= HalfPaddle + BallRadius) {
        view.ballX = left ? 23 : 257;
        vx = (left ? 1 : -1) * std::min(MaxHorizontalSpeed, std::fabs(vx) + 10 * SpeedScale);
        vy = std::clamp((view.ballY - center) / HalfPaddle, -1.0f, 1.0f) * 185 * SpeedScale;
        if (std::fabs(vy) < 25 * SpeedScale)
            vy = (vy < 0 ? -25 : 25) * SpeedScale;
        aim = randomOffset() * 24;
    }
    if (view.ballX < -BallRadius || view.ballX > 280 + BallRadius) {
        if (view.ballX < 0)
            ++view.computerScore;
        else
            ++view.playerScore;
        pointAt = now;
        view.phase = view.playerScore == 7 || view.computerScore == 7
                         ? PongPhase::Finished : PongPhase::Point;
    }
}
} // namespace foot
