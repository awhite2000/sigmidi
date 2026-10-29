#include "leds.hpp"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <vector>
using namespace foot;
struct Trace {
    bool accept = true;
    std::vector<int> values;
    std::vector<int> phases;
    LedFeedback leds;
};
static bool send(const Message &m, uint32_t, void *ctx) {
    auto &t = *static_cast<Trace *>(ctx);
    if (t.accept) t.values.push_back(m.value);
    return t.accept;
}
static void action(int led, bool release, bool toggle, void *ctx) {
    auto &t = *static_cast<Trace *>(ctx);
    assert(toggle);
    t.phases.push_back(release ? -led : led);
    t.leds.action(led, release, toggle);
}
static bool black(const LedFrame &f) {
    return std::all_of(f.bytes.begin(), f.bytes.end(), [](uint8_t v){ return v == 0; });
}
int main() {
    auto c = defaults(); c.leds.enabled = true;
    for (int i = 0; i < 2; ++i) {
        auto &s = c.switches[i]; s.toggle = true;
        s.press.count = s.release.count = 2;
        s.press.messages[0] = {0, 1, 17, 11 + i, 5};
        s.press.messages[1] = {0, 1, 18, 21 + i, 20};
        s.release.messages[0] = {0, 2, 17, 31 + i, 5};
        s.release.messages[1] = {0, 2, 18, 41 + i, 5};
    }
    Engine e; Trace t; t.leds.configure(c);
    e.input(0,c,0); e.input(1,c,1);
    e.tick(5,send,&t,action); assert(t.values.empty());
    t.accept=false; e.tick(6,send,&t,action);
    assert(t.phases.empty() && black(t.leds.frame()));
    t.accept=true; e.tick(7,send,&t,action);
    assert(t.values == std::vector<int>{11} && t.phases == std::vector<int>{1});
    assert(t.leds.frame().bytes[2] == 64);
    e.input(1,c,8); e.input(1,c,9); // held: never retrigger
    e.input(0,c,10); // release does not enqueue Release messages
    e.tick(27,send,&t,action); e.tick(100,send,&t,action);
    assert((t.values == std::vector<int>{11,21}) && e.idle());
    e.input(1,c,101); e.input(0,c,102);
    t.accept=false; e.tick(106,send,&t,action);
    assert(t.phases.size()==1 && !black(t.leds.frame()));
    t.accept=true; e.tick(107,send,&t,action); e.tick(112,send,&t,action);
    assert((t.values == std::vector<int>{11,21,31,41}));
    assert((t.phases == std::vector<int>{1,-1}) && black(t.leds.frame()));
    // Independent switches; ON again after two presses, no release messages.
    e.input(2,c,113); e.input(0,c,114);
    e.tick(118,send,&t,action); e.tick(138,send,&t,action);
    assert(t.phases.back()==2 && t.values.back()==22);
    e.input(1,c,140); e.input(0,c,141);
    e.tick(145,send,&t,action); e.tick(165,send,&t,action);
    assert(t.phases.back()==1 && t.values.back()==21);
    // Rapid OFF must wait for the preceding delayed ON list, with captured settings.
    e.reset(); t.values.clear(); t.phases.clear();
    e.input(0,c,200); e.input(1,c,201); e.input(0,c,202); e.input(1,c,203);
    c.switches[0].led=9; c.switches[0].release.messages[0].value=99;
    e.tick(206,send,&t,action); e.tick(208,send,&t,action);
    assert(t.values == std::vector<int>{11});
    e.tick(226,send,&t,action); e.tick(227,send,&t,action); e.tick(232,send,&t,action);
    assert((t.values == std::vector<int>{11,21,31,41}));
    assert((t.phases == std::vector<int>{1,-1}));
    // Empty lists still drive ON/OFF, without inventing MIDI messages.
    e.reset(); t.values.clear(); t.phases.clear();
    c.switches[0].led=1; c.switches[0].press.count=c.switches[0].release.count=0;
    t.leds.configure(c); t.leds.clear();
    e.input(0,c,300); e.input(1,c,301); e.tick(301,send,&t,action);
    assert(t.values.empty() && t.phases.back()==1 && !black(t.leds.frame()));
    e.input(0,c,302); e.tick(302,send,&t,action); assert(t.phases.size()==1);
    e.input(1,c,303); e.tick(303,send,&t,action);
    assert(t.values.empty() && t.phases.back()==-1 && black(t.leds.frame()));
    e.reset(); e.input(0,c,304); e.input(1,c,305); e.tick(305,send,&t,action);
    assert(t.phases.back()==1); // reset begins OFF
    // A full queue rejects without consuming the next toggle state.
    e.reset(); t.values.clear(); t.phases.clear();
    c.switches[0].press.count=c.switches[0].release.count=1;
    c.switches[0].press.messages[0].value=11;
    c.switches[0].release.messages[0].value=31;
    for(int i=0;i<17;++i) { e.input(0,c,400); e.input(1,c,400); }
    assert(e.rejected==1);
    for(int i=0;i<16;++i)e.tick(500+i*5,send,&t,action);
    assert(e.idle() && t.phases.size()==16 && t.phases.back()==-1);
    e.input(0,c,600); e.input(1,c,601); e.tick(606,send,&t,action);
    assert(t.phases.back()==1 && t.values.back()==11);
    puts("Toggle tests passed: alternate lists, ignored release/hold, independent state, retries, FIFO, empty lists, LED white/off, reset and queue rejection");
}
