#include "pong.hpp"
#include "display.hpp"
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
using namespace foot;
static EncoderInput turn(int delta) {
    EncoderInput input;
    input.rotation = delta;
    input.count = 1;
    input.turns[0] = delta > 0 ? 1 : -1;
    return input;
}
static uint32_t unlock(HiddenPong &game, uint32_t now) {
    for (int i = 0; i < 8; ++i) {
        bool consumed = game.update(true, turn(i % 2 ? -1 : 1), 0, now += 100);
        assert(consumed == (i == 7));
    }
    assert(game.active() && game.frame().phase == PongPhase::Ready);
    return now;
}
int main() {
    // Measure the actual serve and first full crossing through production physics.
    HiddenPong timedGame;
    uint32_t timingNow = unlock(timedGame, 0);
    timedGame.update(true, {}, 1, timingNow);
    uint32_t started = timingNow, firstHitAt = 0, crossedAt = 0;
    bool returning = false;
    float precedingX = timedGame.frame().ballX;
    for (int tick = 0; tick < 1000 && !crossedAt; ++tick) {
        const auto before = timedGame.frame();
        int move = before.ballY > before.player + 4 ? 1 : before.ballY < before.player - 4 ? -1 : 0;
        timedGame.update(true, move ? turn(move) : EncoderInput{}, 0, timingNow += 10);
        const auto &after = timedGame.frame();
        if (!returning && after.ballX > precedingX) {
            returning = true;
            firstHitAt = timingNow - 10; // the preceding tick clamped the ball to x=23
        }
        if (returning && after.ballX >= 257)
            crossedAt = timingNow;
        precedingX = after.ballX;
    }
    assert(firstHitAt && crossedAt);
    assert(firstHitAt - started >= 2130 && firstHitAt - started <= 2150);
    assert(crossedAt - firstHitAt >= 3990 && crossedAt - firstHitAt <= 4020);
    printf("Pong timing: center serve %u ms; initial full crossing %u ms\n",
           firstHitAt - started, crossedAt - firstHitAt);

    // Play repeated rallies to measure the speed cap through real paddle hits.
    HiddenPong fastGame;
    uint32_t fastNow = unlock(fastGame, 5000), leftHitAt = 0, fastest = UINT32_MAX;
    fastGame.update(true, {}, 1, fastNow);
    for (int tick = 0; tick < 1000000 && fastest > 2010; ++tick) {
        const auto before = fastGame.frame();
        if (before.phase == PongPhase::Finished) {
            fastGame.update(true, {}, 1, fastNow);
            leftHitAt = 0;
            continue;
        }
        int move = before.ballY > before.player + 4 ? 1 : before.ballY < before.player - 4 ? -1 : 0;
        fastGame.update(true, move ? turn(move) : EncoderInput{}, 0, fastNow += 10);
        const auto &after = fastGame.frame();
        if (before.phase != PongPhase::Playing || after.phase != PongPhase::Playing) {
            leftHitAt = 0;
            continue;
        }
        if (after.ballX == 23 && before.ballX > 23)
            leftHitAt = fastNow;
        if (leftHitAt && after.ballX >= 257) {
            auto crossing = fastNow - leftHitAt;
            assert(crossing >= 1990 && crossing <= 4020);
            fastest = std::min(fastest, crossing);
            leftHitAt = 0;
        }
    }
    assert(fastest >= 1990 && fastest <= 2010);
    printf("Pong timing: fastest measured full crossing %u ms\n", fastest);

    // Fast reversals within one UI poll must survive even with zero net rotation.
    EncoderTurns queue;
    for (int i = 0; i < 8; ++i)
        queue.push(i % 2 ? -1 : 1);
    EncoderInput batch;
    queue.read(batch);
    assert(batch.rotation == 0 && batch.count == 8 && !batch.overflow);
    HiddenPong game;
    assert(game.update(true, batch, 0, 100) && game.active());
    assert(game.update(true, {}, 2, 101) && !game.active());
    queue.read(batch);
    assert(batch.count == 0 && batch.rotation == 0);
    for (int i = 0; i < 40; ++i)
        queue.push(i % 2 ? -1 : 1);
    queue.read(batch);
    assert(batch.overflow && batch.count == EncoderInput::Capacity);
    assert(!game.update(true, batch, 0, 200) && !game.active());

    // No menu-side gesture, wrong starting direction, slow pairs, or click carryover.
    uint32_t now = 1000;
    for (int i = 0; i < 16; ++i) {
        assert(!game.update(false, turn(i % 2 ? -1 : 1), 0, now += 100));
        assert(!game.active());
    }
    for (int i = 0; i < 8; ++i)
        assert(!game.update(true, turn(i % 2 ? 1 : -1), 0, now += 100));
    assert(!game.active());
    game.update(true, {}, 1, now++);
    for (int i = 0; i < 8; ++i)
        assert(!game.update(true, turn(i % 2 ? -1 : 1), 0, now += 601));
    assert(!game.active());
    game.update(true, {}, 1, now++);
    for (int i = 0; i < 6; ++i)
        assert(!game.update(true, turn(i % 2 ? -1 : 1), 0, now += 100));
    assert(!game.update(true, {}, 1, ++now));
    assert(!game.update(true, turn(1), 0, now += 100));
    assert(!game.update(true, turn(-1), 0, now += 100));
    game.update(false, {}, 0, now++);

    // Multiple detents in each direction form one run, and total duration is limited.
    for (int i = 0; i < 8; ++i) {
        bool expected = i == 7;
        assert(game.update(true, turn(i % 2 ? -1 : 1), 0, now += 100) == expected);
        if (!expected)
            assert(!game.update(true, turn(i % 2 ? -1 : 1), 0, now += 50));
    }
    assert(game.active());
    game.update(true, {}, 2, ++now);
    for (int i = 0; i < 7; ++i)
        assert(!game.update(true, turn(i % 2 ? -1 : 1), 0, now += 580));
    assert(!game.update(true, turn(-1), 0, now += 580));
    assert(!game.active());
    game.update(false, {}, 0, ++now);

    // Unsigned timing remains correct across the system millisecond rollover.
    now = unlock(game, UINT32_MAX - 500);
    assert(game.update(true, turn(20), 0, now += 10));
    assert(game.frame().player == PongFrame::Bottom - PongFrame::PaddleHeight / 2);
    assert(game.update(true, turn(-20), 0, now += 10));
    assert(game.frame().player == PongFrame::Top + PongFrame::PaddleHeight / 2);
    assert(game.update(true, {}, 1, ++now));
    assert(game.frame().phase == PongPhase::Playing && game.frame().playerScore == 0);
    auto start = game.frame();
    game.update(true, {}, 0, now += 30);
    assert(game.frame().ballX < start.ballX);
    game.update(true, {}, 1, ++now);
    assert(game.frame().ballX == 140 && game.frame().computerScore == 0);

    // Exercise rallies, wall/paddle bounces, scoring, serves and game over.
    bool bounced = false, point = false;
    float oldX = 140, oldDx = -1;
    for (int i = 0; i < 100000 && game.frame().phase != PongPhase::Finished; ++i) {
        const auto before = game.frame();
        // First rallies follow the ball; then move away so the CPU also scores.
        int movement = i < 1000 ? (before.ballY > before.player + 4 ? 1 :
                                  before.ballY < before.player - 4 ? -1 : 0) : -20;
        game.update(true, movement ? turn(movement) : EncoderInput{}, 0, now += 10);
        const auto &v = game.frame();
        assert(std::isfinite(v.ballX) && std::isfinite(v.ballY));
        assert(v.player >= 62 && v.player <= 190 && v.computer >= 62 && v.computer <= 190);
        assert(v.ballY >= 48 && v.ballY <= 204);
        assert(v.playerScore >= before.playerScore && v.computerScore >= before.computerScore);
        assert(v.playerScore + v.computerScore - before.playerScore - before.computerScore <= 1);
        if (v.phase == PongPhase::Playing && before.phase == PongPhase::Playing) {
            float dx = v.ballX - oldX;
            bounced |= dx * oldDx < 0;
            oldDx = dx;
        }
        oldX = v.ballX;
        point |= v.phase == PongPhase::Point;
    }
    assert(bounced && point && game.frame().phase == PongPhase::Finished);
    assert(game.frame().playerScore == 7 || game.frame().computerScore == 7);
    auto end = game.frame();
    game.update(true, {}, 0, now += 3000);
    assert(game.frame().playerScore == end.playerScore && game.frame().computerScore == end.computerScore);
    game.update(true, {}, 1, ++now);
    assert(game.frame().phase == PongPhase::Playing && game.frame().playerScore == 0 && game.frame().computerScore == 0);
    assert(game.update(true, {}, 2, ++now) && !game.active());
    assert(!game.update(true, {}, 1, ++now)); // next click can open the ordinary menu

    // Skipped SPI stripes must preserve every pixel of the full rendering.
    DisplayFrame previous;
    previous.screen = Screen::Pong;
    std::vector<uint16_t> screen(DisplayWidth * DisplayHeight), expected(screen.size());
    renderDisplayStripe(previous, 0, DisplayHeight, screen.data());
    for (int i = 0; i < 300; ++i) {
        DisplayFrame next = previous;
        next.pong.phase = static_cast<PongPhase>((i / 50) % 4);
        next.pong.player = 62 + (i * 7) % 129;
        next.pong.computer = 62 + (i * 3) % 129;
        next.pong.ballX = 23 + (i * 5) % 235;
        next.pong.ballY = 48 + (i * 11) % 157;
        next.pong.playerScore = (i / 13) % 8;
        next.pong.computerScore = (i / 31) % 8;
        for (int y = 0; y < DisplayHeight; y += DisplayStripeRows)
            if (pongStripeChanged(previous.pong, next.pong, y, DisplayStripeRows))
                renderDisplayStripe(next, y, DisplayStripeRows, screen.data() + y * DisplayWidth);
        renderDisplayStripe(next, 0, DisplayHeight, expected.data());
        assert(screen == expected);
        previous = next;
    }
    auto winner = previous.pong;
    winner.phase = PongPhase::Finished;
    auto otherWinner = winner;
    otherWinner.playerScore = winner.playerScore == 7 ? 0 : 7;
    assert(pongStripeChanged(winner, otherWinner, 96, 16));
    // Each game state renders identically in full-frame and guarded DMA stripes.
    for (auto phase : {PongPhase::Ready, PongPhase::Playing, PongPhase::Point, PongPhase::Finished}) {
        DisplayFrame frame;
        frame.screen = Screen::Pong;
        frame.pong.phase = phase;
        frame.pong.playerScore = 7;
        std::vector<uint16_t> full(DisplayWidth * DisplayHeight);
        renderDisplayStripe(frame, 0, DisplayHeight, full.data());
        std::array<uint16_t, DisplayWidth * DisplayStripeRows + 2> stripe;
        for (int y = 0; y < DisplayHeight; y += DisplayStripeRows) {
            stripe.fill(0xf00f);
            renderDisplayStripe(frame, y, DisplayStripeRows, stripe.data() + 1);
            assert(stripe.front() == 0xf00f && stripe.back() == 0xf00f);
            assert(std::equal(stripe.begin() + 1, stripe.end() - 1, full.begin() + y * DisplayWidth));
        }
    }
    puts("Pong tests passed: four-to-two-second crossings, ordered gesture, timeouts, menu isolation, controls, physics, scores, restart/exit and stripes");
}
