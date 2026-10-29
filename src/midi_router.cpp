#include "midi_router.hpp"
namespace foot {
void MidiRouter::clear() { for (auto &q : queues) q.head = q.count = 0; }
void MidiRouter::ready(unsigned next) {
    mask = next & 3;
    for (unsigned i = 0; i < 2; ++i)
        if (!(mask & (1u << i))) queues[i].head = queues[i].count = 0;
}
void MidiRouter::tick(Send ble, Send usb, void *ctx) {
    const Send outputs[]{ble, usb};
    for (unsigned i = 0; i < 2; ++i) {
        auto &q = queues[i];
        // Bound work per control-loop iteration, even after a long stall.
        for (unsigned n = 0; n < 8 && q.count && (mask & (1u << i)); ++n) {
            const auto &item = q.items[q.head];
            if (!outputs[i](item.message, item.time, ctx)) break;
            q.head = (q.head + 1) % Capacity; --q.count;
        }
    }
}
bool MidiRouter::send(const Message &message, uint32_t now, Send ble, Send usb, void *ctx) {
    if (!mask) return false;
    for (unsigned i = 0; i < 2; ++i)
        if ((mask & (1u << i)) && queues[i].count == Capacity) return false;
    const Send outputs[]{ble, usb};
    bool delivered[2]{}, accepted = false;
    for (unsigned i = 0; i < 2; ++i)
        if ((mask & (1u << i)) && !queues[i].count)
            accepted |= delivered[i] = outputs[i](message, now, ctx);
    // No link accepted it: let the original scheduler/counter retry unchanged.
    if (!accepted) return false;
    for (unsigned i = 0; i < 2; ++i) {
        if (!(mask & (1u << i)) || delivered[i]) continue;
        auto &q = queues[i];
        q.items[(q.head + q.count) % Capacity] = {message, now}; ++q.count;
    }
    return true;
}
bool usbMidiPacket(const Message &m, uint8_t packet[4]) {
    if ((m.type != 0 && m.type != 1) || m.channel < 1 || m.channel > 16 || m.number < 0 ||
        m.number > 127 || (m.type == 0 && (m.value < 0 || m.value > 127)) ||
        (m.type == 1 && m.pcMode != Static)) return false;
    packet[0] = m.type == 1 ? 0x0c : 0x0b; // cable 0, PC or CC code index
    packet[1] = (m.type == 1 ? 0xc0 : 0xb0) | (m.channel - 1);
    packet[2] = m.number;
    packet[3] = m.type == 1 ? 0 : m.value;
    return true;
}
}
