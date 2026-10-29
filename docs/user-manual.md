# SIGMIDI Foot Controller

## User manual · Version 0.1

Play, edit and control Line 6 HX Stomp over BLE MIDI.

![Preferred Left enclosure](../previews/sigmidi-left-main.png)

The illustrated workflows use the current 280 x 240 device menus and the preferred Left enclosure. The Right enclosure uses the same controls and features, with the switch order reversed within each row.

| Start here | Page |
|---|---|
| Connect SIGMIDI and the BLE MIDI dongle | 2 |
| Perform: switches, LEDs and the main screen | 3 |
| Edit on the device / edit over Wi-Fi | 4 / 5 |
| Calibrate switches and expression pedals | 6 |
| HX Stomp programs / snapshots / parameters | 7 / 8 / 9 |
| Tap tempo, preset stepping and PC counters | 10 |
| Example stage layout and looper commands | 11 |
| MIDI command reference / troubleshooting and sources | 12 / 13 |

This guide describes firmware v0.1, configuration schema 6. Screen images are rendered from the production firmware with example settings. HX Stomp recipes are configuration examples; the SIGMIDI-to-dongle-to-HX Stomp connection has not been bench qualified. Line 6, HX Stomp and CME names belong to their respective owners.

<!-- page -->

# 1. Connect and get ready

## A direct wireless rig

![Direct BLE MIDI signal path](manual-signal-path.svg)

SIGMIDI sends MIDI control data; your guitar/audio connections remain on HX Stomp. An iPad is not required for this direct setup. The dongle must support the BLE MIDI **central** role and connect to a third-party BLE MIDI peripheral. A dongle that only advertises as a peripheral cannot form this direct link.

1. Power SIGMIDI through USB-C, or its fitted 9 V DC center-negative, 5.5 x 2.1 mm input. Power HX Stomp with its own suitable supply.
2. Connect the dongle's MIDI output to **HX Stomp MIDI IN**. For a CME WIDI Master, the large main adapter goes into HX Stomp MIDI OUT for power and the linked small adapter goes into MIDI IN. Follow the dongle maker's instructions. [S3]
3. Arrange for the dongle to connect as central to **SIGMIDI Foot Controller v0.1**. WIDI's third-party-controller auto-pairing is one example; actual interoperability must be tested. Close phone/tablet apps that might take over the dongle. [S3]
4. Wait for **MIDI READY** on SIGMIDI. **CONNECTED** alone means a connection exists but the receiver has not yet subscribed to MIDI notifications.
5. On HX Stomp, set the MIDI Base Channel to **1** and enable MIDI PC reception from the DIN MIDI input (MIDI or MIDI+USB, as offered by the installed firmware). All examples use channel 1. [S1, p.60]
6. Release all footswitches, then test one simple PC command as described on page 7. New SIGMIDI configurations contain no MIDI actions.

## First configuration

Choose the enclosure variant and installed switch count, calibrate the switch ladder, create actions, then **SAVE & EXIT**. MIDI performance is paused while setup is open. Only explicit Test commands transmit during setup.

For the four-switch Left base, the top row reads **A B** and the lower row **1 2**. Extensions add C/3, D/4 and E/5 to the right. The full Right enclosure reads **E D C B A / 5 4 3 2 1** from left to right. Select Left or Right once in Settings; this also selects the matching screen rotation.

**Connection checklist:** dongle powered; output directed to HX MIDI IN; compatible central role; correct channel; SIGMIDI shows MIDI READY; controller is out of setup.

<!-- page -->

# 2. Performance mode

![Performance screen with example actions and enabled pedals](../previews/01.png)

## Read the main screen

The large switch label and name identify the physically pressed switch. The message counts describe its configured Press and Release lists; they do not show a received HX preset name or confirm its state. At idle, the central panel reads READY. Pedal panels show each assigned CC and its current 0-127 output; OFF means disabled and --- means no valid reading.

| BLE badge | Meaning |
|---|---|
| OFFLINE | No BLE connection. Connect the receiving device. |
| CONNECTED | Connected, but MIDI notifications are not subscribed. |
| MIDI READY | The BLE transport can accept MIDI messages. |

## Momentary or toggle: choose per switch

| Mode | First press | Physical release | Next press |
|---|---|---|---|
| TOGGLE OFF | Send Press list | Send Release list | Send Press list again |
| TOGGLE ON | Send Press list; LED white | No action | Send Release list; LED dark |

With optional LEDs enabled, a momentary Press action lights white and a Release action lights yellow. Colors latch after the first accepted message. Empty momentary lists leave the color unchanged; empty toggle lists still turn the LED on/off. LED feedback reports local action delivery to BLE, not the actual HX block state.

Use one footswitch at a time. Holding a switch does not repeat its messages. Delayed lists run in order; a quick release cannot overtake the Press list. Release all switches after boot, setup exit or a BLE readiness change to rearm the scanner.

Click the encoder while switches and pending actions are idle to enter setup. Setup and BLE readiness transitions clear queued actions and LEDs and reset runtime toggle states to OFF. Reboot also starts toggles OFF. A preset or snapshot change on HX Stomp can change effects independently; reload a known state when necessary. SIGMIDI does not track incoming HX status.

<!-- page -->

# 3. Edit on the device

![Setup menu](../previews/02.png) ![Per-switch toggle setting](../previews/22.png)

## Encoder controls

| Gesture | Result |
|---|---|
| Turn | Move through items; while editing, change the value. |
| Click | Open an item or accept the edited value. |
| Hold about 0.7 seconds | Cancel the current value edit, or go back one level. |

From performance, click the encoder, choose **EDIT CONFIG > SWITCHES**, then select a switch. Configure NAME, PRESS, RELEASE, LED NO. and TOGGLE. The labels A-E / 1-5 remain attached to their physical switches when the enclosure variant changes. For long names, the Wi-Fi editor is quicker; on-device name editing advances character by character with clicks.

## Build an action list

1. Open **PRESS** or **RELEASE**. `PC24/2` means Program 24 on channel 2; `CC17:127/3` means CC17, value 127, on channel 3. `PC+/2` and `PC-/2` are counters on channel 2. Recipes below use channel 1.
2. Select an existing message for **EDIT MSG**, **INSERT BEFORE** or **DELETE MSG**. **APPEND MSG** adds a message at the end.
3. Set TYPE to **PC** or **CC**, then its channel. STATIC PC uses PROGRAM and has no Value field. CC uses CONTROL and VALUE. PC INCR/DECR have neither Program nor Value.
4. Set DELAY MS: this is the wait **before this message**, not a pause after the whole list. New messages default to 5 ms. **MOVE UP/DOWN** reorders an existing message; scroll if needed.
5. Back out to the list and use **TEST SEQ** while MIDI READY. Back out to setup and select **SAVE & EXIT** to store changes, or **DISCARD & EXIT** to keep the saved configuration.

Parameters are gray with white values; action commands are purple, PC summaries cyan and CC summaries orange. An active value edit is amber. Lists scroll beyond the seven visible rows.

Each Press/Release list allows 32 messages. The whole configuration allows 128 messages, including hidden extension mappings. Channels are 1-16; programs, CC numbers and values are 0-127; each delay is 0-10000 ms.

<!-- page -->

# 4. Edit over Wi-Fi

![Wi-Fi switch editor: toggle mode with separate ON and OFF message lists](manual-wifi-example.png)

## Open the editor

1. Enter setup on the controller and choose **WI-FI SETUP**.
2. Join the displayed `SIGMIDI-xxxx` network using the password on the LCD. Accept staying connected if your phone reports that the network has no internet.
3. Open **http://192.168.4.1/** and enter the same password to open the editor. Internet access is not needed.
4. Open a switch card. Set its name, **Toggle mode** and LED assignment. Edit On press/On release, or Toggle ON/Toggle OFF when toggle is enabled. Expand a message for its fields.

Use **Append message**, **Insert before**, **Delete** and the up/down buttons to construct the list in execution order. PC mode offers STATIC, INCR and DECR; compact summaries show PC+ and PC-. **Test press** and **Test release** send the selected draft list to the connected receiver. They can change the HX sound and advance PC counters; they do not advance the performance toggle latch.

## Save, leave and back up

**Save** stores the draft and stays in setup. **Save & exit** stores it and resumes performance; Wi-Fi then turns off. **Discard changes** restores the saved draft. **Reload draft** fetches the controller's current draft. Use **Export JSON** for a configuration backup and **Import JSON** to load one, then save it on the controller. Live PC counter values are stored separately and are not included in JSON backups.

One browser owns editing at a time. While a browser owns the draft, the LCD shows BROWSER EDITING. Holding the encoder takes ownership back and discards the draft. Finish or export browser edits first. Normal footswitch and pedal MIDI remain paused until you exit setup.

<!-- page -->

# 5. Calibrate switches and pedals

![Left enclosure calibration menu](../previews/12.png) ![Left enclosure switch list](../previews/11.png)

## Set the physical layout first

In Wi-Fi **Settings**, choose **Enclosure variant**, **Ladder wiring** and **Number of footswitches**. Modular wiring supports 4, 6, 8 or 10 switches. Adding an extension does not change the configured count automatically. Reducing the count hides unused mappings without deleting them. Changing Left/Right reorders the menus and rotates the display; it does not move MIDI actions, calibration or LED assignments between switches.

## Calibrate the switch ladder

In Wi-Fi **Calibration**, capture Idle with no switch held. Hold just one named switch and capture its voltage, then release it. Repeat for every installed switch. Choose an Acceptance half-width that contains the stable readings without overlapping neighboring switches; it must be less than half the smallest center-to-center voltage gap. Save and exit, then check every switch in performance mode. The LCD also exposes the ladder centers and window under EDIT CONFIG.

## Use a passive expression pedal

Each input accepts a passive variable resistor or potentiometer up to 10 kOhm. Unplug the pedal before changing its electrical mode. Select the input in **Pedals**, choose two-wire resistor mode or potentiometer mode, save and exit, reconnect, then return to calibration. For a resistor, set its maximum resistance. For a potentiometer, read the input's live mV at both travel endpoints and enter those measurements in Heel/Toe manually; stored Toe voltage must be at least 50 mV above Heel voltage. The v0.1 pedal Capture buttons apply a legacy scale factor, so use manual entry from the live readings for this passive interface. If the physical direction is reversed, assign the low/high voltage endpoints in that order and use Invert to obtain the desired direction.

Set Enabled, MIDI channel, CC, output minimum/maximum and Linear or Logarithmic response. Example: channel 1, CC1, range 0-127 controls HX EXP1; CC2 controls EXP2. The HX preset must already assign the intended parameter to that expression controller. [U]

For a fixed parameter assignment, use CC21 instead and assign that CC on HX Stomp as on page 9. Start with a Linear curve. Move the pedal after returning to performance: a stationary pedal does not repeatedly send its value. Calibrate both inputs independently. Optional LEDs are enabled under LED chain; for Pololu 2535 use RGB, the 2535 timing profile and suitable brightness.

<!-- page -->

# 6. Prepare existing HX Stomp patches

## Know the address of the sound you want

On HX Stomp, open its Preset list from Play view and read the **PC:xxx** helper text. Use that value directly as SIGMIDI PROGRAM: do not add 1 or derive it from an assumed A/B/C bank formula. The Line 6 illustration identifies **Pastor of Muppets** with PC061, but use your unit's actual readout if its preset has moved. [S1, pp.13,65]

The following real patch names are useful starting points: **Pastor of Muppets** appears in the owner's manual; **Placater Dirty** and **Outtake** are named factory-preset examples in Line 6's tutorial index. Factory content and installed locations vary. [S1; S2]

## Reproducible practice copies

Back up HX Stomp first. Copy those existing patches to unused locations and keep the originals intact. For the numerical recipes below, use spare locations whose HX MIDI readouts are PC010, PC011 and PC012. These are chosen lesson destinations, not claims about factory locations. If these slots are occupied, choose others and replace every corresponding PC number in the recipes. If a named patch is absent, substitute an existing patch and inspect its available blocks before assigning controls.

| Existing patch copied to a spare location | Lesson PC readout | SIGMIDI name | Press message |
|---|---|---|---|
| Pastor of Muppets | PC010 | MUPPETS | `PC10/1` |
| Placater Dirty | PC011 | PLACATER | `PC11/1` |
| Outtake | PC012 | OUTTAKE | `PC12/1` |

## Configure a preset switch

For switch **A**, set NAME to MUPPETS and TOGGLE OFF. In PRESS, append PC, mode STATIC, channel 1, Program 10 and Delay 5 ms. Leave RELEASE empty. Save and exit. One press loads the practice copy; releasing sends nothing. Repeat on B with Program 11 and on extension C with Program 12.

To recall the manual's unmodified example directly, use `PC61/1` only if your current HX readout confirms PC061 for Pastor of Muppets. Program changes select a whole preset; they do not require per-block CC assignments.

**Use valid MIDI numbers.** The supplied reference's CC128 row is a joke, not a usable message. CC numbers stop at 127. The guide uses only valid messages; the full curated command list is on page 12.

<!-- page -->

# 7. Snapshots and ordered actions

![Action list showing compact PC and CC messages](../previews/03.png) ![CC editor with channel, control and value](../previews/05.png)

## Select a snapshot in the current preset

Configure a momentary switch with a single Press CC and an empty Release list. The supplied reference uses **CC69** for snapshot selection: 0 selects Snapshot 1, 1 selects Snapshot 2 and 2 selects Snapshot 3. [U]

| Example switch name | Press list | Delay | Release list |
|---|---|---|---|
| SNAP 1 | `CC69:0/1` | 5 ms | Empty |
| SNAP 2 | `CC69:1/1` | 5 ms | Empty |
| SNAP 3 | `CC69:2/1` | 5 ms | Empty |

HX Stomp has three snapshots per preset. Do not use value 3 as a fourth snapshot on this model, despite that row in the supplied CC table. Prepare and save the intended sound in each snapshot first. [S1, p.43]

## Recall a preset and then its snapshot

For A, build a Press list with these two entries in order. TOGGLE stays OFF and RELEASE stays empty.

| Order | Type / mode | Channel | Program or Controller | Value | Delay before |
|---|---|---|---|---|---|
| 1 | PC / STATIC | 1 | Program 10 | Hidden | 5 ms |
| 2 | CC | 1 | Controller 69 | 1 | 5 ms |

The compact list reads `PC10/1`, then `CC69:1/1`. This loads the MUPPETS practice copy and selects its prepared Snapshot 2. The wait before the second message is relative to the preceding accepted message. Recent HX documentation describes buffering CC69 during preset loading; verify the result on your firmware. Increase the second delay if the complete rig needs more time. [S1, p.66]

Use the same pattern for the other copies, changing only Program and the snapshot value. Editing a preset or snapshot on HX can change block states, so SIGMIDI's latched LEDs must not be treated as snapshot or effect feedback.

<!-- page -->

# 8. Control effects and parameters

## Recipe A: latch an existing effect on and off

In the MUPPETS practice copy, choose the Harmony Delay block shown in Line 6's example, if present. Otherwise choose an existing delay block. Assign its **Bypass MIDI In** to an unused CC20 and save the HX preset. Incoming low values bypass the assigned block; high values enable it. Make the starting state bypassed. [S4]

| SIGMIDI switch 1 | Setting |
|---|---|
| NAME / TOGGLE | DELAY / ON |
| PRESS | CC, channel 1, Controller 20, Value 127, Delay 5 ms |
| RELEASE | CC, channel 1, Controller 20, Value 0, Delay 5 ms |
| Compact lists | `CC20:127/1` / `CC20:0/1` |

First press enables the delay and lights white. Lifting your foot does nothing. The next press bypasses the delay and extinguishes the LED. Optional LEDs must be enabled. This uses a direct block assignment, so it does not depend on HX's current footswitch mode. CC20 is a chosen user assignment, not a universal delay command.

## Recipe B: momentary parameter lift

In the PLACATER practice copy, select an existing amp's Drive parameter. Assign it to MIDI CC21 in Controller Assign, set Min to 3.0 and Max to 5.0 (or valid nearby values for that block), and save. If CC21 is already used, choose another free, non-reserved CC and change both ends. [S4]

Set an available SIGMIDI switch to NAME DRIVE LIFT, TOGGLE OFF, Press `CC21:127/1` and Release `CC21:0/1`, each with 5 ms delay. Holding the switch requests the maximum Drive; release returns to the minimum. MIDI Value 127 means the assigned maximum, not Drive 127. The same method can use an existing Outtake delay's Mix, with a proposed Min 20% and Max 35% instead; these are example settings, not claims about its factory blocks or values.

## Make the assignment on HX Stomp

For bypass, open Bypass Assign and select the block's MIDI In CC. For a parameter, hold its parameter knob to open Controller Assign, choose MIDI CC, set CC#, then Min/Max. Learn is an alternative: send the intended CC while Learn is active. Save the HX preset as well as SIGMIDI's configuration. [S4]

Do not use a reserved global CC for these assignments. The supplied reference's CC75-77 controls whichever parameter knobs are currently displayed; that is convenient for editing but less predictable than a dedicated per-parameter CC for a live show. [U]

<!-- page -->

# 9. Tap, step and count programs

## Trigger an HX command once per press

Keep TOGGLE OFF and RELEASE empty for these commands. Adding an unconditional release message can trigger a second command. All rows below use channel 1 and 5 ms delay. [U]

| Name | Press message | Use |
|---|---|---|
| TAP | `CC64:127/1` | Tap repeatedly to set HX tempo. SIGMIDI does not send MIDI clock. |
| TUNER | `CC68:127/1` | Trigger tuner screen on/off; this is not a value-based LED latch. |
| PREVIOUS | `CC72:0/1` | Request previous HX preset. |
| NEXT | `CC72:127/1` | Request next HX preset. |

HX footswitch emulation CC49-53 acts on the switch's current assigned function, which can depend on the HX footswitch mode. Use a direct PC, snapshot CC or assigned block/parameter CC when you want the same result regardless of that mode. [U]

## When to use PC+ and PC-

PC INCR and DECR are absolute program-number counters stored **separately for each configured message**. They are not an up/down pair tracking the current HX preset. To step relative to whatever preset HX is actually using, prefer the two CC72 recipes above.

![Independent PC+ and PC- action entries](../previews/19.png) ![Incremental PC editor](../previews/20.png)

For a PC+ action, set TYPE PC, MODE INCR and CHANNEL 1. There is no Program or Value field. Its compact name is `PC+/1`; DECR gives `PC-/1`. A new counter starts at 0. First successful invocation after reboot sends the stored value unchanged. Later INCR sends 1, 2 and onward, wrapping 127 to 0; DECR steps downward and wraps 0 to 127. A separate new PC- therefore sends 0 first, then 127, regardless of what PC+ has sent.

No PC is sent automatically at startup. Changed counter values are retained immediately and checkpointed to flash every five minutes when needed. Power loss can lose changes since that checkpoint. Reordering messages preserves identities; inserting a new counter message creates its own counter. Test actions can advance these counters. JSON backups include the configuration, not the live values.

<!-- page -->

# 10. An example stage layout

## Start with four switches, extend when needed

This layout uses the practice addresses on page 7. All MIDI channels are 1 and all new-message delays are 5 ms. Add the snapshot message after A's PC in the order shown. Except DELAY, leave TOGGLE OFF and RELEASE empty. Use the Left layout for A-E / 1-5 from left to right; Right reverses the physical order within each row.

| Switch | Name | Press list | Release list / mode |
|---|---|---|---|
| A | MUPPETS | `PC10/1`, `CC69:1/1` | Empty; momentary |
| B | PLACATER | `PC11/1` | Empty; momentary |
| 1 | DELAY | `CC20:127/1` | `CC20:0/1`; Toggle ON |
| 2 | TAP | `CC64:127/1` | Empty; momentary |
| C | OUTTAKE | `PC12/1` | Empty; momentary |
| 3 | SNAP 3 | `CC69:2/1` | Empty; momentary |
| D | SNAP 1 | `CC69:0/1` | Empty; momentary |
| 4 | PREVIOUS | `CC72:0/1` | Empty; momentary |
| E | SNAP 2 | `CC69:1/1` | Empty; momentary |
| 5 | NEXT | `CC72:127/1` | Empty; momentary |

The base needs only A, B, 1 and 2. A six-switch unit adds C/3; eight adds D/4; ten adds E/5. Configure CC20 in every HX preset where DELAY should work. Otherwise it may do nothing or control a different existing assignment. Snapshot switches act within the currently loaded preset.

## Optional looper substitutions

If the current HX preset contains a suitable Looper block, replace spare switches with these Press-only CC commands. Use TOGGLE OFF and an empty Release list unless you deliberately want alternate explicit commands. The supplied reference defines the following values. [U]

| Control | CC / value | Control | CC / value |
|---|---|---|---|
| Record | 60 / 127 | Overdub | 60 / 0 |
| Play | 61 / 127 | Stop | 61 / 0 |
| Play once | 62 / 127 | Undo/redo | 63 / 127 |
| Forward | 65 / 0 | Reverse | 65 / 127 |
| Full speed | 66 / 0 | Half speed | 66 / 127 |

Before a show, load each intended preset and test every assigned switch and pedal. Saving both devices and exporting the SIGMIDI JSON gives you a repeatable starting point. After a setup/reset, explicitly establish the required HX block states rather than relying on a dark SIGMIDI toggle LED to prove that the block is bypassed.

<!-- page -->

# 11. MIDI reference for these recipes

The supplied table is the starting reference [U]. The table below retains its useful commands while omitting the invalid CC128 joke and unused entries. Values are MIDI data values, not parameter percentages. All messages also need the correct MIDI channel.

| Message | Value | Intended function |
|---|---|---|
| PC, STATIC | Program 0-127 | Recall the preset identified by HX's PC helper readout. |
| CC1 / CC2 | 0-127 | Emulate EXP1 / EXP2. The preset's assignments decide the destination. |
| CC20 (chosen) | 0 / 127 | Assigned delay block bypass / enable in this guide. |
| CC21 (chosen) | 0 / 127 | Assigned parameter Min / Max in this guide. |
| CC49 / 50 / 51 / 52 / 53 | 0-127 | Emulate HX FS1 / FS2 / FS3 / FS4 / FS5. |
| CC60 | 0-63 / 64-127 | Looper overdub / record. |
| CC61 | 0-63 / 64-127 | Looper stop / play. |
| CC62 / CC63 | 64-127 | Looper play once / undo-redo. |
| CC64 | 64-127 | Tap tempo. |
| CC65 | 0-63 / 64-127 | Looper forward / reverse. |
| CC66 | 0-63 / 64-127 | Looper full / half speed. |
| CC68 | 0-127 | Trigger tuner screen on/off. |
| CC69 | 0 / 1 / 2 | HX Stomp Snapshot 1 / 2 / 3. |
| CC69 | 8 / 9 | Next / previous snapshot. |
| CC70 | 0-63 / 64-127 | All bypass / active processing. |
| CC71 | 0-127 | MODE command; behavior depends on the device's available modes. |
| CC72 | 0-63 / 64-127 | Previous / next preset. |
| CC73 | 0-127 | Toggle HX Play/Edit view. |
| CC75 / 76 / 77 | 0-127 | Global control of displayed parameter knobs 1 / 2 / 3. |
| CC81 | 0-63 / 64-127 | Page Left / Page Right. |

**Model and firmware matter.** Standard HX Stomp has three snapshots; the fourth-snapshot text in the supplied table is not used here. Treat reserved CCs as unavailable for custom assignments. The reference's CC74 reservation conflicts with Line 6's 3.15 release note describing a preset-save command; this guide deliberately assigns neither CC74 nor undocumented reserved commands. Consult your firmware's documentation before using them. [S1, p.43; S5]

SIGMIDI v0.1 sends PC and CC only, with per-message channels and delays. It does not generate MIDI clock, SysEx, note messages or an automatic program-state synchronization with HX Stomp. The displayed PC offset setting does not change the wire number: enter the 0-127 PC readout itself.

<!-- page -->

# 12. Troubleshooting and sources

| Symptom | Check or corrective action |
|---|---|
| OFFLINE / no dongle pairing | Dongle power, MIDI connections, central-role capability and third-party pairing procedure. Disconnect competing phone/tablet clients. |
| CONNECTED but no MIDI | The central must subscribe to BLE MIDI notifications. Reconnect through its MIDI connection procedure. |
| MIDI READY, HX does nothing | Exit setup; confirm channel 1, HX MIDI PC Rx for DIN, correct MIDI IN direction and a nonempty action. Test one command first. |
| Wrong preset | Read PC:xxx on HX. Do not add 1. Check your copied patch's actual location. |
| CC changes nothing / wrong parameter | Assign that CC in this preset and save HX. Check range, block selection and duplicate assignments. |
| Toggle LED disagrees with sound | LEDs are local, not HX feedback. Preset changes and manual HX operation can change state. Re-establish a known starting state. |
| New PC+ does not step first time | Intended: first invocation after reboot sends its stored number unchanged. PC+ and PC- have separate counters. |
| Switch absent or misidentified | Check count, Modular/Linear setting and enclosure variant. Capture Idle and one physical switch at a time. |
| Pedal OFF / --- / no change | Enable it, check mode and endpoint range, then move it after leaving setup. Stationary pedals do not keep transmitting. |
| Wi-Fi editor unavailable | Start WI-FI SETUP on LCD, join its displayed network and use HTTP at 192.168.4.1. Save & exit turns Wi-Fi off. |
| LED stays dark | Check the optional LED setting, assigned LED number (not None), brightness and wiring. MIDI must be ready for performance actions. |

## Source notes and scope

**[U] User-supplied HX Stomp MIDI CC reference image.** Used for the command/value recipes and reference table. It includes inconsistencies noted on pages 7, 8 and 12; CC128 is not a valid MIDI controller number.

**[S1]** [Line 6 HX Stomp 3.80 Owner's Manual](https://line6.com/data/6/0a00051afdda673cccdb61c9c/application/pdf/HX%20Stomp%203.80%20Owner%27s%20Manual%20-%20English%20.pdf), pp.13,43,60,65-67: address readouts, snapshot count, receive settings and preset/snapshot sequencing.

**[S2]** [Line 6 HX Stomp tutorials by Jason Sadites](https://kb.line6.com/hx-stomp-tutorials-by-jason-sadites): published Placater Dirty and Outtake factory-preset examples.

**[S3]** [CME WIDI Master start guide](https://www.cme-pro.com/widi-master-start-guide-bluetooth-midi/): adapter connections and third-party BLE controller pairing. This is an example dongle workflow, not a claim of tested SIGMIDI compatibility.

**[S4]** [Line 6 HX Stomp Owner's Manual, MIDI assignment instructions](https://line6.com/data/6/0a020a4010c935bb66a4c0c44f/application/pdf/HX), p.48: block bypass and parameter CC assignment.

**[S5]** [Line 6 firmware release notes, 3.15 features](https://line6.com/software/index.html?hardware=HX+Stomp&name=Firmware&submit_form=set): global parameter controls and the CC74 preset-save note.

SIGMIDI behavior and illustrations were checked against this project's current firmware, menus and documentation on 29 October 2026. The examples leave existing firmware and hardware configuration untouched; validate the full wireless rig before relying on it live. Further project guides: Firmware, Bring-up, Resistor ladder, LEDs and Web flasher under docs/.
