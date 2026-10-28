# SIGMIDI Foot Controller v0.1 — Firmware

The firmware uses ESP-IDF 5.3.1 on ESP32-C6. Release version is **0.1**; configuration schema is **4**. Default settings select Left enclosure, Modular wiring and ten switches. MIDI mappings are empty; pedals and LED feedback are disabled.

## MIDI actions

Each physical switch stores separate `press` and `release` lists. Each list supports up to 32 messages, with a limit of 128 messages across all ten stored switches. Every message has its own channel, type, number and delay. Channels are 1–16; PC programs, CC controllers and CC values are 0–127. Delay is 0–10000 ms. Added or inserted messages default to 5 ms.

A message object in an exported configuration has this form:

```json
{"type": 0, "channel": 3, "number": 17, "value": 127, "delayMs": 5}
```

`type` is 0 for CC and 1 for PC. `number` holds the controller or program number. PC editors label it **Program** and hide **Value**; CC editors show **Control** on LCD, **Controller** in the browser, and **Value**. PC display numbering is 0–127; `pcOffset` is a stored field without a display effect.

Action lists show compact entries such as `PC24/2` and `CC17:127/3`. Select an entry to edit, insert before it or delete it. Append adds at the end; ordering controls move messages within a list. An empty release list sends nothing.

The action engine snapshots both lists and the LED assignment at press. It preserves each switch's press-then-release order, including release during a delayed press. It schedules due messages without blocking input scans and supports 16 outstanding jobs. A full queue reports rejection. Holding a switch does not repeat its list.

## Switch count, wiring and identity

Modular wiring supports **4/6/8/10** switches. Linear wiring supports **4–10**, including odd counts. The count is selected explicitly; the ladder does not detect extensions automatically.

Storage uses permanent electrical taps T1–T10. `switches` has ten entries; `ladder` has idle followed by ten tap centers. Both editors translate displayed positions back to those taps. Reducing the count hides unused inputs while keeping their saved data. Validation includes MIDI messages in hidden entries.

For the modular base, **A=T2, B=T1, 1=T4, 2=T3**. Extensions add C/3=T5/T6, D/4=T7/T8 and E/5=T9/T10. See [wiring and calibration targets](resistor-ladders.md).

| Enclosure | Electronics | LCD rotation | Ten-switch rows, left to right |
|---|---|---:|---|
| Left, default | Left | 180° | A B C D E / 1 2 3 4 5 |
| Right | Right | 0° | E D C B A / 5 4 3 2 1 |

One `enclosureVariant` field controls both display rotation and list order: 1=Left, 0=Right. Actions, calibration and LED assignments stay on their physical taps. Choose it in Wi-Fi **Settings → Enclosure variant** or LCD **EDIT CONFIG → ENCLOSURE**, then save.

The scanner reads the ladder approximately every 1 ms, using calibrated voltage windows and a default 10 ms debounce. It accepts one switch from stable idle. A different stable code ends the active switch and inhibits presses until idle. Persistent invalid readings latch a fault until idle. Boot, setup exit and BLE readiness changes require idle rearming. Simultaneous switch decoding is unsupported.

## Pedals

Each input has enable, resistor/potentiometer mode, maximum resistance, heel/toe calibration, inversion, curve, channel, CC and output range. The maximum resistance is positive and at most 10 kΩ. Potentiometer endpoints must be distinct.

Pedal ADC samples are read every 5 ms and filtered with 0.75 of the prior reading plus 0.25 of the new reading. Conversion undoes the input's 2:3 voltage scaling. Resistor mode uses a nominal 3.3 V reference and 10 kΩ pull-up; potentiometer mode uses captured heel/toe voltages. Resistor reference/gain correction and nonzero resistance-minimum calibration are not implemented.

Normalized output uses `y=x` for Linear or `y=ln(1+k*x)/ln(1+k)` for Log, with positive curve strength `k`. Inversion and the configured MIDI range determine the output value. CC transmission is change-driven, hysteretic and limited to one update per 20 ms per pedal. Invalid samples suppress that pedal's output. A stationary pedal does not continuously transmit CC.

Change electrical mode with the pedal unplugged: save and exit setup, reconnect, then calibrate. The mode GPIOs follow saved settings on setup exit.

## BLE MIDI

The device advertises **SIGMIDI Foot Controller v0.1** using the standard BLE MIDI service. `ble.cpp` implements timestamped PC/CC notifications through ESP-IDF NimBLE. MIDI readiness requires the central to subscribe to notifications. Connection loss clears queued actions; reconnecting does not replay switch events. The transport does not implement persistent bonding. Connect through the iPad MIDI application's BLE MIDI interface.

## Encoder and LCD

Rotate to navigate or change a value; click to select or accept. Hold for 700 ms to cancel an edit or return one level. The encoder uses quadrature decoding with four valid transitions per detent by default; `EDGES_PER_DETENT=2` supports an appropriate half-cycle encoder.

Click from performance to enter setup when the ladder and action engine are idle. **Save & Exit** validates and persists the draft; **Discard & Exit** returns to saved settings. Setup suppresses normal switch/pedal MIDI; explicit Test actions are available when BLE MIDI is ready.

The 280×240 ST7789V2 driver uses RGB565, (20,0) controller offsets, 10 MHz SPI and an 8,960-byte buffer for 16-row stripes. Left rotation maps both axes in software. The renderer draws outside the shared-state mutex and skips identical views.

The performance view shows BLE state, active switch/name and two pedal bars. Setup has seven-row scrolling lists, breadcrumbs and a scrollbar. Editable values align at X164; names are gray, values white, actions purple and the active edit amber. PC entries are cyan and CC entries orange. Content avoids the display's rounded corners.

## Wi-Fi editor

Choose **Wi-Fi Setup**, join the password-protected `SIGMIDI-xxxx` access point and open **http://192.168.4.1/**. The LCD shows the SSID and a generated 16-character password. The browser asks for the same password to acquire editing. The editor is served from flash and works without internet.

The browser and LCD share one validated draft. One browser writer owns a renewable 60-second lease; writes carry the draft revision and session credentials. Conflicting writes are rejected. Holding the encoder can revoke browser ownership and discard the draft. Requests are bounded to 32 KiB.

**Save** persists the draft and keeps setup open. **Save & Exit** also returns to performance; the access point shuts down after a short response grace period. **Discard** cancels unsaved edits. Exports/imports use versioned JSON, exclude Wi-Fi credentials and session tokens, and validate the whole configuration before applying it.

The editor exposes switch lists, pedal settings, live ADC readings, ladder capture, pedal heel/toe capture, LED assignments, count and enclosure settings. Calibration voltage fields show whole millivolts. Untouched fields and captures keep stored measurement precision; explicit voltage edits use 1 mV steps.

## LED feedback

The optional Pololu 2535 chain defaults to RGB, protocol 2535, brightness 64/255 and tap-to-pixel assignments 1:1. Assignment 0 disables a switch's indicator. Feedback triggers when the first message in a phase is accepted by the BLE transport: white for press, yellow for release. Empty phases and rejected sends do not trigger it. This indicates local queuing, not acknowledgement from the iPad.

`leds.cpp` holds colors; `led_hardware.cpp` transmits through RMT in a separate task. Ten pixel addresses are sent, with unused outputs cleared. Frames refresh at startup, on changes and every 250 ms. Setup/readiness transitions and saved LED/count/mapping changes clear the state. LED driver faults report a notice while MIDI processing continues. See [wiring and commissioning](leds.md).

## Implementation and verification

`core.cpp` implements validation, tap mapping, scanning and scheduling; `config.cpp` serializes configuration; `hardware.cpp` handles GPIO/ADC/LCD/encoder; `ui.cpp` and `display.cpp` implement menus and graphics; `wifi.cpp` hosts the editor; `storage.cpp` persists settings in NVS.

Run `scripts/test.sh` for host tests. Display previews use the production renderer and menu harness. Firmware compilation and host tests do not qualify actual LCD timing, Wi-Fi/BLE coexistence, iPad delivery or input noise. See [bring-up checks](bringup.md).
