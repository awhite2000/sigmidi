#pragma once
#include "core.hpp"
namespace foot {
// One bounded FIFO per link. The scheduler and counters resolve each message once.
class MidiRouter {
  public:
    enum Link { Ble = 0, Usb = 1 };
    static constexpr unsigned Capacity = 64;
    void ready(unsigned mask);
    void clear();
    void tick(Send ble, Send usb, void *ctx);
    bool send(const Message &, uint32_t now, Send ble, Send usb, void *ctx);
    unsigned pending(Link link) const { return queues[link].count; }
  private:
    struct Item { Message message; uint32_t time = 0; };
    struct Queue { std::array<Item, Capacity> items{}; unsigned head = 0, count = 0; };
    std::array<Queue, 2> queues{};
    unsigned mask = 0;
};
bool usbMidiPacket(const Message &, uint8_t packet[4]);
}
