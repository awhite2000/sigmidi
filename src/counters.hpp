#pragma once
#include "core.hpp"

namespace foot {
// Room for the saved configuration plus an unsaved MIDI Test draft.
constexpr int CounterCapacity = 2 * MaxTotalMessages;
constexpr uint32_t CounterFlushMs = 5 * 60 * 1000;
struct CounterEntry { uint32_t id, value; };
// POD only: RTC_NOINIT storage must never run a constructor at startup.
struct CounterMemory {
    uint32_t magic, format, generation, modified, checksum;
    CounterEntry entries[CounterCapacity];
};
class PcCounters {
    CounterMemory &memory;
    std::array<uint32_t, CounterCapacity> invoked{}; // Deliberately not retained across reboot.
    CounterEntry *entry(int id);
    void seal();
  public:
    explicit PcCounters(CounterMemory &retained) : memory(retained) {}
    static bool valid(const CounterMemory &);
    void restore(const CounterMemory *flash, bool allowRetained);
    void reconcile(const Config &saved, const Config *draft = nullptr);
    int value(int id) const;
    bool transmit(const Message &, uint32_t now, Send, void *);
    bool snapshot(CounterMemory &) const;
    void acknowledge(const CounterMemory &); // Keep dirty if a newer send occurred during flash I/O.
};
} // namespace foot
