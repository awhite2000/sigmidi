#include "counters.hpp"
#include <climits>
#include <cstring>

namespace foot {
namespace {
constexpr uint32_t Magic = 0x50434335, Format = 1;
uint32_t checksum(const CounterMemory &m) {
    uint32_t h = 2166136261u;
    auto word = [&](uint32_t v) {
        for (int i = 0; i < 4; ++i) {
            h = (h ^ (v & 255)) * 16777619u;
            v >>= 8;
        }
    };
    word(m.magic); word(m.format); word(m.generation); word(m.modified);
    for (const auto &e : m.entries) { word(e.id); word(e.value); }
    return h;
}
bool uses(const Config &c, uint32_t id) {
    for (const auto &s : c.switches)
        for (auto seq : {&s.press, &s.release})
            for (int i = 0; i < seq->count; ++i)
                if (static_cast<uint32_t>(seq->messages[i].counterId) == id)
                    return true;
    return false;
}
} // namespace
void PcCounters::seal() { memory.checksum = checksum(memory); }
bool PcCounters::valid(const CounterMemory &m) {
    if (m.magic != Magic || m.format != Format || m.modified > 1 || m.checksum != checksum(m))
        return false;
    for (int i = 0; i < CounterCapacity; ++i) {
        if (m.entries[i].id >= INT_MAX || m.entries[i].value > 127)
            return false;
        for (int j = 0; j < i; ++j)
            if (m.entries[i].id && m.entries[i].id == m.entries[j].id)
                return false;
    }
    return true;
}
void PcCounters::restore(const CounterMemory *flash, bool allowRetained) {
    invoked.fill(0);
    if (allowRetained && valid(memory))
        return;
    if (flash && valid(*flash)) {
        memory = *flash;
        memory.modified = 0;
    } else {
        memset(&memory, 0, sizeof memory);
        memory.magic = Magic;
        memory.format = Format;
    }
    seal();
}
void PcCounters::reconcile(const Config &saved, const Config *draft) {
    for (int i = 0; i < CounterCapacity; ++i)
        if (memory.entries[i].id && !uses(saved, memory.entries[i].id) &&
            (!draft || !uses(*draft, memory.entries[i].id))) {
            memory.entries[i] = {};
            invoked[i] = 0;
        }
    ++memory.generation;
    seal();
}
CounterEntry *PcCounters::entry(int id) {
    if (id <= 0 || id == INT_MAX)
        return nullptr;
    for (auto &e : memory.entries)
        if (e.id == static_cast<uint32_t>(id))
            return &e;
    for (auto &e : memory.entries)
        if (!e.id) {
            e = {static_cast<uint32_t>(id), 0};
            seal();
            return &e;
        }
    return nullptr;
}
int PcCounters::value(int id) const {
    for (const auto &e : memory.entries)
        if (id > 0 && e.id == static_cast<uint32_t>(id))
            return e.value;
    return 0;
}
bool PcCounters::transmit(const Message &m, uint32_t now, Send send, void *ctx) {
    if (m.type != 1 || m.pcMode == Static)
        return send(m, now, ctx);
    if (m.pcMode != Increment && m.pcMode != Decrement)
        return false;
    auto e = entry(m.counterId);
    if (!e)
        return false;
    const int slot = static_cast<int>(e - memory.entries);
    const bool advance = invoked[slot] == e->id;
    Message resolved = m;
    resolved.pcMode = Static;
    resolved.number = advance ? (e->value + (m.pcMode == Increment ? 1 : 127)) % 128 : e->value;
    if (!send(resolved, now, ctx))
        return false;
    invoked[slot] = e->id;
    if (advance) {
        e->value = resolved.number;
        memory.modified = 1;
        ++memory.generation;
        seal();
    }
    return true;
}
bool PcCounters::snapshot(CounterMemory &out) const {
    if (!memory.modified)
        return false;
    out = memory;
    return true;
}
void PcCounters::acknowledge(const CounterMemory &saved) {
    if (memory.generation == saved.generation) {
        memory.modified = 0;
        seal();
    }
}
} // namespace foot
