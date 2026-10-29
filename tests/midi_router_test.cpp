#include "midi_router.hpp"
#include "counters.hpp"
#include "board.hpp"
#include <cassert>
#include <cstdio>
#include <vector>
using namespace foot;
struct Output {
    bool ble = true, usb = true;
    std::vector<Message> b, u;
    std::vector<uint32_t> bt, ut;
};
static bool ble(const Message &m, uint32_t t, void *p) {
    auto &o = *static_cast<Output *>(p); if (!o.ble) return false;
    o.b.push_back(m); o.bt.push_back(t); return true;
}
static bool usb(const Message &m, uint32_t t, void *p) {
    auto &o = *static_cast<Output *>(p); if (!o.usb) return false;
    o.u.push_back(m); o.ut.push_back(t); return true;
}
struct Context { MidiRouter &router; Output &output; };
static bool route(const Message &m, uint32_t t, void *p) {
    auto &c = *static_cast<Context *>(p); return c.router.send(m,t,ble,usb,&c.output);
}
int main() {
    static_assert(board::validPins());
    static_assert(board::AdcChannels[0] == 0 && board::AdcChannels[1] == 1 && board::AdcChannels[2] == 3);
    Message cc{0,16,17,127,5}, pc{1,2,24,99,5}; uint8_t p[4]{};
    assert(usbMidiPacket(cc,p) && p[0]==0x0b && p[1]==0xbf && p[2]==17 && p[3]==127);
    assert(usbMidiPacket(pc,p) && p[0]==0x0c && p[1]==0xc1 && p[2]==24 && p[3]==0);
    for (int channel : {0,17}) { auto m=cc; m.channel=channel; assert(!usbMidiPacket(m,p)); }
    auto invalid=cc;invalid.value=128;assert(!usbMidiPacket(invalid,p));
    invalid=pc;invalid.number=-1;assert(!usbMidiPacket(invalid,p));
    invalid=pc;invalid.pcMode=Increment;assert(!usbMidiPacket(invalid,p));
    MidiRouter r; Output o;
    assert(!r.send(cc,1,ble,usb,&o) && o.b.empty() && o.u.empty());
    r.ready(2); assert(r.send(cc,2,ble,usb,&o)); assert(o.b.empty() && o.u.size()==1);
    r.ready(1); assert(r.send(pc,3,ble,usb,&o)); assert(o.b.size()==1 && o.u.size()==1);
    r.ready(3);assert(r.send(cc,4,ble,usb,&o));assert(o.b.size()==2 && o.u.size()==2);
    // Dynamic PC resolves once. Partial success commits exactly once, retry only the failed link.
    r.clear(); o=Output{};o.ble=false;Context ctx{r,o};CounterMemory memory{};PcCounters bank(memory);
    bank.restore(nullptr,false);Message up{1,3,0,0,5,Increment,1};
    assert(bank.transmit(up,10,route,&ctx));assert(bank.value(1)==0 && o.u.back().number==0);
    assert(bank.transmit(up,20,route,&ctx));assert(bank.value(1)==1 && o.u.back().number==1);
    assert(r.pending(MidiRouter::Ble)==2 && r.pending(MidiRouter::Usb)==0);
    r.tick(ble,usb,&o);assert(o.b.empty() && o.u.size()==2);
    o.ble=true;r.tick(ble,usb,&o);
    assert(o.b.size()==2 && o.b[0].number==0 && o.b[1].number==1 && o.bt[0]==10 && o.bt[1]==20);
    assert(o.u.size()==2 && bank.value(1)==1 && !r.pending(MidiRouter::Ble));
    o.ble=o.usb=false;assert(!bank.transmit(up,30,route,&ctx));assert(bank.value(1)==1);
    assert(!r.pending(MidiRouter::Ble) && !r.pending(MidiRouter::Usb));
    o.usb=true;assert(bank.transmit(up,31,route,&ctx));assert(bank.value(1)==2);
    r.ready(2);assert(!r.pending(MidiRouter::Ble)); // Drop stale copies on disconnect.
    r.ready(3);o.ble=true;r.tick(ble,usb,&o);assert(o.b.size()==2); // No replay on reconnect.
    // A stalled link applies bounded, atomic backpressure before the successful link sends again.
    r.clear();o=Output{};o.usb=false;
    for (unsigned n=0;n<MidiRouter::Capacity;++n) {cc.value=n;assert(r.send(cc,n,ble,usb,&o));}
    auto count=o.b.size();assert(!r.send(pc,100,ble,usb,&o) && o.b.size()==count);
    assert(r.pending(MidiRouter::Usb)==MidiRouter::Capacity);
    o.usb=true;r.tick(ble,usb,&o);assert(o.u.size()==8);
    assert(r.send(pc,101,ble,usb,&o));
    for (int n=0;n<9;++n)r.tick(ble,usb,&o);
    assert(o.u.size()==65 && o.b.size()==65 && o.u.back().number==24);
    for(unsigned n=0;n<MidiRouter::Capacity;++n)assert(o.u[n].value==int(n));
    r.clear();assert(!r.pending(MidiRouter::Ble) && !r.pending(MidiRouter::Usb));
    puts("USB MIDI packets and dual-transport routing passed: ordering, retries, disconnects, bounded backpressure and single PC-counter advancement");
}
