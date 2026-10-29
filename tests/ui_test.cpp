#include "app.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
State state;
SemaphoreHandle_t stateMutex;
uint32_t nowMs() { return 0; }
static bool midiReady = false;
bool bleReady() { return midiReady; }
bool bleConnected() { return midiReady; }
bool wifiStart() { return false; }
bool saveConfig(const foot::Config &) { return true; }
bool queueTest(int, bool) { return false; }
static bool shown(const char *text) {
    char lines[10][24]{};
    uiRender(lines);
    for (auto &line : lines)
        if (!strcmp(line, text))
            return true;
    return false;
}
int main() {
    // Initial pedal values are not transmitted: prompt each enabled input until its first send.
    state.key = 0;
    state.saved.pedals[0].enabled = state.saved.pedals[1].enabled = true;
    state.pedal[0] = 84;
    state.pedal[1] = 32;
    strcpy(state.notice, "ADC calibration failed");
    foot::DisplayFrame prompt{};
    uiView(prompt);
    assert(!prompt.pedals[0].needsMove && !prompt.pedals[1].needsMove); // Offline.
    midiReady = true;
    for (int variant : {0, 1}) {
        state.saved.enclosureVariant = variant;
        state.pedalNeedsMove[0] = state.pedalNeedsMove[1] = true;
        uiView(prompt);
        assert(!strcmp(prompt.action, "MOVE PEDALS 1+2 TO SYNC"));
        assert(prompt.pedals[0].needsMove && prompt.pedals[1].needsMove);
        assert(!strcmp(prompt.notice, "ADC calibration failed")); // Do not hide faults.
        state.pedalNeedsMove[0] = false;
        uiView(prompt);
        assert(!strcmp(prompt.action, "MOVE PEDAL 2 TO SYNC"));
        assert(!prompt.pedals[0].needsMove && prompt.pedals[1].needsMove);
        state.key = 1;
        uiView(prompt);
        assert(!strncmp(prompt.action, "PRESS ", 6)); // Switch message counts remain visible.
        assert(prompt.pedals[1].needsMove);
        state.key = 0;
        state.saved.pedals[1].enabled = false;
        uiView(prompt);
        assert(!prompt.pedals[1].needsMove);
        assert(!strcmp(prompt.action, "PRESS A FOOTSWITCH TO PLAY"));
        state.saved.pedals[1].enabled = true;
        state.pedal[1] = -1;
        uiView(prompt);
        assert(!prompt.pedals[1].needsMove); // Invalid reading stays --- rather than MOVE.
        state.pedal[1] = 32;
        state.pedalNeedsMove[1] = false;
        uiView(prompt);
        assert(!strcmp(prompt.action, "PRESS A FOOTSWITCH TO PLAY"));
    }
    state = State{};
    midiReady = false;
    state.saved.enclosureVariant = 0; // Explicit Right fixture for existing navigation cases.
    for (int count = 6; count <= 10; ++count) {
        state.setup = true;
        state.draft = foot::defaults();
        state.draft.enclosureVariant = 0; // Explicit Right fixture.
        state.draft.ladderLayout = 0;
        state.draft.switchCount = count;
        state.revision++;
        uiStep(0, 0); // refresh tree, browsing persists after the first iteration
        if (count == 6)
            uiStep(0, 1); // EDIT CONFIG
        // Root JSON fields: version, count, debounce, offset, window, ladder, switches, pedals.
        uiStep(6, 1); // switch array
        uiStep(100, 0);
        char expected[24];
        snprintf(expected, sizeof expected, ">%d", count);
        assert(shown(expected));
        uiStep(0, 2);  // root, selects switches at 6
        uiStep(-1, 1); // ladder (index 5)
        uiStep(100, 0);
        foot::DisplayFrame view{};
        uiView(view);
        snprintf(expected, sizeof expected, "SW %d MV", count);
        assert(!strcmp(view.rows[view.selectedRow], expected));
        assert(view.rowKinds[view.selectedRow] == foot::MenuRowKind::Parameter);
        assert(view.values[view.selectedRow][0]);
        uiStep(0, 2);  // root, selects ladder at 5
        uiStep(-4, 1); // edit count at 1
        uiStep(-100, 0);
        assert(shown("*SWITCHES 4"));
        uiStep(100, 0);
        assert(shown("*SWITCHES 10"));
        uiStep(0, 2); // cancel restores original count
        uiStep(0, 2); // root -> edit menu, sync draft
        assert(state.draft.switchCount == count);
        uiStep(0, 1); // enter root for next iteration
    }
    state.draft = foot::defaults();
    state.draft.enclosureVariant = 0; // Explicit Right fixture.
    state.draft.ladderLayout = 0;
    auto &press = state.draft.switches[2].press;
    press.count = 2;
    press.messages[0] = {1, 2, 24, 0, 5};
    press.messages[1] = {0, 3, 17, 127, 5};
    state.revision++;
    uiStep(0, 0);
    uiStep(6, 1); // switches
    uiStep(2, 1); // switch 3
    uiStep(1, 1); // press
    foot::DisplayFrame view{};
    uiView(view);
    assert(view.rowKinds[0] == foot::MenuRowKind::Message);
    assert(!strcmp(view.rows[0], "PC24/2"));
    assert(view.rowKinds[2] == foot::MenuRowKind::Action);
    assert(!strcmp(view.rows[2], "APPEND MSG"));
    uiStep(0, 1);
    uiView(view);
    for (int i = 0; i < 3; ++i)
        assert(view.rowKinds[i] == foot::MenuRowKind::Action);
    uiStep(0, 1); // edit PC
    uiView(view);
    assert(!strcmp(view.rows[0], "TYPE") && !strcmp(view.values[0], "PC"));
    assert(!strcmp(view.rows[3], "PROGRAM") && !strcmp(view.values[3], "24"));
    assert(!strcmp(view.rows[4], "DELAY MS") && !strcmp(view.values[4], "5"));
    for (int i = 0; i < view.rowCount; ++i)
        assert(strcmp(view.rows[i], "VALUE"));
    assert(view.rowKinds[5] == foot::MenuRowKind::Action);
    assert(!strcmp(view.rows[1], "MODE") && !strcmp(view.values[1], "STATIC"));
    uiStep(1, 1); // PC mode
    uiStep(1, 1); // INCR
    uiView(view);
    assert(!strcmp(view.values[1], "INCR"));
    for (int i = 0; i < view.rowCount; ++i)
        assert(strcmp(view.rows[i], "PROGRAM") && strcmp(view.rows[i], "VALUE"));
    uiStep(0, 2);
    uiView(view);
    assert(!strcmp(view.rows[0], "PC+/2"));
    uiStep(0, 1); uiStep(0, 1); // edit message again
    uiStep(1, 1); uiStep(1, 1); // DECR
    uiView(view);
    assert(!strcmp(view.values[1], "DECR"));
    uiStep(0, 1); uiStep(-2, 1); // restore STATIC
    uiStep(0, 2); // list
    uiStep(1, 1); // CC actions
    uiStep(0, 1); // edit CC
    uiView(view);
    assert(!strcmp(view.rows[0], "TYPE") && !strcmp(view.values[0], "CC"));
    assert(!strcmp(view.rows[2], "CONTROL") && !strcmp(view.values[2], "17"));
    assert(!strcmp(view.rows[3], "VALUE") && !strcmp(view.values[3], "127"));
    for (int i = 0; i < 5; ++i)
        assert(view.rowKinds[i] == foot::MenuRowKind::Parameter);
    assert(view.rowKinds[5] == foot::MenuRowKind::Action);
    for (int i = 0; i < 4; ++i)
        uiStep(0, 2); // configuration root
    uiStep(2, 1);     // LED CHAIN, appended at index 8
    uiView(view);
    assert(!strcmp(view.title, "LED CHAIN"));
    assert(!strcmp(view.rows[0], "ENABLED") && !strcmp(view.values[0], "OFF"));
    uiStep(0, 1); // enabled
    uiStep(1, 1); // ON, accept
    uiView(view);
    assert(!strcmp(view.values[0], "ON"));
    uiStep(1, 1); // brightness
    uiStep(1000, 0);
    uiView(view);
    assert(!strcmp(view.values[1], "255"));
    uiStep(0, 2); // cancel -> 64
    uiStep(1, 1); // color order
    uiStep(1000, 1);
    uiView(view);
    assert(!strcmp(view.values[2], "GBR"));
    uiStep(1, 1); // timing
    uiStep(1000, 1);
    uiView(view);
    assert(!strcmp(view.values[3], "OLD 400K"));
    uiStep(0, 2);  // root
    uiStep(-2, 1); // switches
    uiStep(0, 1);  // switch 1
    uiStep(3, 1);  // LED assignment
    uiStep(-100, 0);
    uiView(view);
    assert(!strcmp(view.rows[3], "LED NO.") && !strcmp(view.values[3], "OFF"));
    uiStep(0, 2); // cancel
    uiView(view);
    assert(!strcmp(view.values[3], "1"));
    uiStep(1, 1); // Toggle, appended after LED assignment
    uiView(view);
    assert(!strcmp(view.rows[4], "TOGGLE") && !strcmp(view.values[4], "OFF"));
    uiStep(1, 1); // ON, accept
    uiView(view);
    assert(!strcmp(view.values[4], "ON"));
    uiStep(0, 2); // switch list
    uiStep(0, 2); // config root
    uiStep(4, 1); // ENCLOSURE at root index 10, after switches at 6
    uiView(view);
    assert(!strcmp(view.rows[view.selectedRow], "ENCLOSURE"));
    assert(!strcmp(view.values[view.selectedRow], "RIGHT"));
    uiStep(1000, 0);
    uiView(view);
    assert(!strcmp(view.values[view.selectedRow], "LEFT") && view.displayRotation == 0);
    uiStep(0, 2); // cancel restores 0
    uiView(view);
    assert(!strcmp(view.values[view.selectedRow], "RIGHT"));
    uiStep(0, 1);
    uiStep(-1000, 0);
    uiStep(1, 1); // select 180, accept
    uiStep(0, 2); // sync draft, back to setup
    assert(state.draft.enclosureVariant == 1 && state.saved.enclosureVariant == 0);
    uiStep(2, 1); // Save & exit
    uiView(view);
    assert(!state.setup && state.saved.enclosureVariant == 1 && view.displayRotation == 180);
    assert(state.saved.switches[0].toggle);
    // A new draft can select 0, but discard and browser ownership retain saved orientation.
    state.setup = true;
    state.draft = state.saved;
    state.revision++;
    uiStep(-2, 1); // EDIT CONFIG
    uiStep(10, 1); // rotation
    uiStep(-1, 1); // 0, accept
    uiStep(0, 2);  // sync draft
    assert(state.draft.enclosureVariant == 0 && state.saved.enclosureVariant == 1);
    state.owner = "browser";
    state.leaseUntil = 1000;
    uiView(view);
    assert(view.screen == foot::Screen::Browser && view.displayRotation == 180);
    state.owner.clear();
    uiStep(3, 1); // Discard & exit
    uiView(view);
    assert(!state.setup && state.draft.enclosureVariant == 1 && view.displayRotation == 180);
    puts(
        "LCD UI tests passed: switch counts/calibration, cancel, PC/CC labels and separate values, "
        "message/action row semantics, LED settings and assignment, saved enclosure variant");
}
