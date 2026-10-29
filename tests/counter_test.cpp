#include "counters.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
using namespace foot;
struct Output { bool ready = true; std::vector<Message> sent; };
static bool collect(const Message &m, uint32_t, void *ctx) {
    auto &out = *static_cast<Output *>(ctx);
    if (!out.ready) return false;
    out.sent.push_back(m);
    return true;
}
struct EngineOutput { PcCounters &bank; Output &output; };
static bool configured(const Message &m, uint32_t now, void *ctx) {
    auto &c = *static_cast<EngineOutput *>(ctx);
    return c.bank.transmit(m, now, collect, &c.output);
}
int main() {
    CounterMemory memory{}, checkpoint{};
    PcCounters bank(memory);
    bank.restore(nullptr, false);
    Output out;
    Message up{1, 2, 99, 0, 5, Increment, 1}, down{1, 2, 88, 0, 5, Decrement, 2};
    assert(CounterFlushMs == 300000 && PcCounters::valid(memory));
    assert(!bank.snapshot(checkpoint));
    assert(out.sent.empty()); // Restore alone never transmits.
    out.ready = false;
    for (int i = 0; i < 3; ++i) assert(!bank.transmit(up, i, collect, &out));
    assert(bank.value(1) == 0 && !bank.snapshot(checkpoint));
    out.ready = true;
    assert(bank.transmit(up, 0, collect, &out)); // First successful action sends stored zero.
    assert(out.sent.back().number == 0 && !bank.snapshot(checkpoint));
    for (int i = 1; i <= 129; ++i) {
        assert(bank.transmit(up, i, collect, &out));
        assert(out.sent.back().number == i % 128);
    }
    assert(bank.value(1) == 1 && bank.value(2) == 0);
    assert(bank.transmit(down, 0, collect, &out));
    assert(out.sent.back().number == 0); // Independent first invocation, even on the same channel.
    assert(bank.transmit(down, 0, collect, &out));
    assert(out.sent.back().number == 127 && bank.value(1) == 1);
    assert(bank.transmit(down, 0, collect, &out));
    assert(out.sent.back().number == 126);
    // Static PC and CC never read/modify counters.
    Message fixed{1, 16, 24, 0, 5}, cc{0, 3, 17, 127, 5};
    assert(bank.transmit(fixed, 0, collect, &out) && out.sent.back().number == 24);
    assert(bank.transmit(cc, 0, collect, &out) && out.sent.back().value == 127);
    assert(bank.snapshot(checkpoint));
    assert(bank.transmit(up, 0, collect, &out)); // Send during a flash commit.
    bank.acknowledge(checkpoint);
    CounterMemory latest{};
    assert(bank.snapshot(latest)); // Acknowledging the older write must not lose dirty.
    bank.acknowledge(latest);
    assert(!bank.snapshot(checkpoint));
    CounterMemory cold{};
    PcCounters reboot(cold);
    reboot.restore(&latest, false);
    assert(reboot.value(1) == 2 && reboot.value(2) == 126 && !reboot.snapshot(checkpoint));
    assert(reboot.transmit(up, 0, collect, &out));
    assert(out.sent.back().number == 2 && !reboot.snapshot(checkpoint));
    assert(reboot.transmit(up, 0, collect, &out));
    assert(out.sent.back().number == 3);
    PcCounters warm(cold);
    warm.restore(&latest, true);
    assert(warm.value(1) == 3 && warm.snapshot(checkpoint));
    assert(warm.transmit(up, 0, collect, &out) && out.sent.back().number == 3);
    cold.entries[0].value ^= 3; // Corrupt retained state falls back to valid NVS.
    warm.restore(&latest, true);
    assert(warm.value(1) == 2);
    latest.checksum ^= 1;
    cold.checksum ^= 1;
    warm.restore(&latest, true);
    assert(warm.value(1) == 0 && !warm.snapshot(checkpoint));

    auto c = defaults();
    // Identity travels with a message and deleted IDs are not recycled.
    c = defaults();
    c.switches[0].press.count = 2;
    c.switches[0].press.messages[0] = {1, 1, 0, 0, 5, Increment};
    c.switches[0].press.messages[1] = {1, 1, 0, 0, 5, Decrement};
    assert(assignCounterIds(c));
    auto &seq = c.switches[0].press;
    int first = seq.messages[0].counterId, second = seq.messages[1].counterId;
    assert(first != second && first && second);
    char error[100]; assert(validate(c, error, sizeof error));
    assert(warm.transmit(seq.messages[0], 0, collect, &out));
    assert(warm.transmit(seq.messages[0], 0, collect, &out));
    std::swap(seq.messages[0], seq.messages[1]);
    warm.reconcile(c);
    assert(warm.value(seq.messages[1].counterId) == 1);
    seq.messages[0] = {1, 1, 0, 0, 5, Increment};
    assert(assignCounterIds(c) && seq.messages[0].counterId > second);
    warm.reconcile(c);
    assert(warm.value(seq.messages[0].counterId) == 0);
    seq.messages[0].counterId = first;
    assert(!validate(c, error, sizeof error));
    // The real action queue snapshots mode/identity, resolves at send time and retries once.
    CounterMemory queuedMemory{};
    PcCounters queued(queuedMemory);
    queued.restore(nullptr, false);
    c = defaults();
    c.switches[0].press.count = c.switches[0].release.count = 1;
    c.switches[0].press.messages[0] = up;
    c.switches[0].release.messages[0] = down;
    Engine engine;
    EngineOutput context{queued, out};
    out.sent.clear(); out.ready = false;
    engine.input(0, c, 0); engine.input(1, c, 1);
    c.switches[0].press.messages[0].pcMode = Decrement; // Cannot alter the queued snapshot.
    engine.tick(6, configured, &context);
    assert(queued.value(1) == 0 && out.sent.empty());
    out.ready = true; engine.tick(7, configured, &context);
    engine.input(0, c, 8); engine.tick(13, configured, &context);
    assert(out.sent.size() == 2 && out.sent[0].number == 0 && out.sent[1].number == 0);
    c.switches[0].press.messages[0].pcMode = Increment;
    engine.input(1, c, 20);
    c.switches[0].press.messages[0].pcMode = Decrement;
    engine.tick(25, configured, &context);
    engine.input(0, c, 26); engine.tick(31, configured, &context);
    assert(out.sent.size() == 4 && out.sent[2].number == 1 && out.sent[3].number == 127);
    // Discarding an unsaved draft removes test-only state before its ID can be reused.
    queued.reconcile(defaults());
    assert(queued.value(1) == 0 && queued.value(2) == 0);
    puts("PC counters passed: independent IDs, wrapping, first invocation after reboot, retries, retained/flash restore and concurrent checkpoint acknowledgement");
}
