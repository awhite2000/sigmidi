# SIGMIDI Foot Controller v0.1 — Firmware

The firmware uses ESP-IDF 5.3.1 on ESP32-C6. Release version is **0.1**; configuration schema is **5**. Default settings select Left enclosure, Modular wiring and ten switches. MIDI mappings are empty; pedals and LED feedback are disabled.

## MIDI actions

Each physical switch stores separate `press` and `release` lists. Each list supports up to 32 messages, with a limit of 128 messages across all ten stored switches. Every message has its own channel, type, number and delay. Channels are 1–16; PC programs, CC controllers and CC values are 0–127. Delay is 0–10000 ms. Added or inserted messages default to 5 ms.

A message object in an exported configuration has this form:

```json
{"type": 0, "pcMode": 0, "channel": 3, "number": 17, "value": 127, "delayMs": 5, "counterId": 0}
```

`type` is 0 for CC and 1 for PC. `number` holds the controller or program number. STATIC PC editors label it **Program** and hide **Value**; INCR/DECR PC editors hide both fields; CC editors show **Control** on LCD, **Controller** in the browser, and **Value**. PC display numbering is 0–127; `pcOffset` is a stored field without a display effect.

Action lists show compact entries such as `PC24/2`, `PC+/2`, `PC-/3` and `CC17:127/3`. Select an entry to edit, insert before it or delete it. Append adds at the end; ordering controls move messages within a list. An empty release list sends nothing.

The action engine snapshots both lists and the LED assignment at press. It preserves each switch's press-then-release order, including release during a delayed press. It schedules due messages without blocking input scans and supports 16 outstanding jobs. A full queue reports rejection. Holding a switch does not repeat its list.

## PC counters

PC messages have a **MODE** selector on the LCD and **PC mode** in Wi-Fi: **STATIC** (`pcMode: 0`), **INCR** (`1`) or **DECR** (`2`). STATIC sends the configured Program as before. Each INCR/DECR message has an independent counter, including messages on the same channel and separate press/release messages. New counters start at 0. INCR sends `(counter + 1) % 128`; DECR sends `(counter + 127) % 128`. On the first successful invocation after reboot, either mode sends its restored value unchanged (0 for a new counter). The second invocation of a new INCR sends 1; the second invocation of a new DECR sends 127. Values always use MIDI wire numbering 0–127.

The counter changes only after the BLE transport accepts that message. A failed send retries without another step. Successful sends immediately update retained RTC memory and its modified flag. A background FreeRTOS task checks every **300000 ms (5 minutes)**, writes a checksummed NVS blob only when modified and clears the flag only after a successful commit. If MIDI changes a counter during that flash write, the flag stays set for the next checkpoint. Write failures also leave it set for retry. Configuration saves and counter checkpoints use separate NVS keys.

ESP32-C6 has RTC FAST memory rather than a separate RTC SLOW bank. `RTC_NOINIT_ATTR` places the counter state in its available retained RTC/LP SRAM; [Espressif documents the C6 RTC mapping](https://docs.espressif.com/projects/esp-idf/en/v5.3/esp32c6/api-reference/system/sleep_modes.html#power-down-of-rtc-peripherals-and-memories). The state has a format marker and checksum. Startup restores valid retained state after a warm reset when available, otherwise the most recent valid flash checkpoint, otherwise 0. Power loss can lose changes since the last five-minute checkpoint.

No PC values are transmitted automatically on startup or BLE connection. Each message has a volatile first-invocation marker that resets on reboot and is set only after a successful send. Its first successful action sends the restored counter value **without stepping it or setting the modified flag**; later actions step before sending. Failed sends leave the marker unchanged. Press and release messages each have their own marker, and reconnection or a configuration reorder does not reset it.

`counterId` is a stable per-message identity, separate from array position; `nextCounterId` in the configuration allocates new identities monotonically. Reordering or inserting messages, switching enclosure variant, changing channel or hiding an extension preserves existing counters. Deleting a message removes its counter from the active set; a new message receives a new identity. IDs are included in JSON backups and hidden from both editors. Backups contain counter identities and mode, not live counter values; NVS stores values separately. Schemas 1–4 migrate to 5 with STATIC as the missing-mode default. Duplicated counter IDs and invalid mode values are rejected.

Explicit MIDI Test actions use the same counter behavior. Counters for unsaved test-only messages are discarded with the draft and are not reused by later newly created messages.

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

Pedal ADC samples are read every 5 ms and filtered with 0.75 of the prior reading plus 0.25 of the new reading. TIP voltages are used directly, without gain correction. For an enabled resistor input, GPIO20/21 drives HIGH through a 10 kΩ bias resistor. Potentiometer, disabled and boot states leave that GPIO at high impedance with both internal pulls off; it is never driven LOW. Resistor conversion uses a nominal 3.3 V bias and 10 kΩ resistor; potentiometer mode uses captured heel/toe voltages. A 5.1 kΩ ring resistor limits reference current. Capture pedal endpoints after rewiring and use firmware built for this passive interface. Resistor reference/gain correction and nonzero resistance-minimum calibration are not implemented.

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

`core.cpp` implements validation, tap mapping, scanning and scheduling; `config.cpp` serializes configuration; `hardware.cpp` handles GPIO/ADC/LCD/encoder; `ui.cpp` and `display.cpp` implement menus and graphics; `wifi.cpp` hosts the editor; `storage.cpp` persists settings and periodic counter checkpoints in NVS; `counters.cpp` implements counter identities, retained state and first-invocation behavior.

Run `scripts/test.sh` for host tests. Display previews use the production renderer and menu harness. Firmware compilation and host tests do not qualify actual LCD timing, Wi-Fi/BLE coexistence, iPad delivery or input noise. See [bring-up checks](bringup.md).
