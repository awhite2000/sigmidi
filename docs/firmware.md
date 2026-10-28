# SIGMIDI Foot Controller v0.1 — Firmware behavior and architecture

Project/firmware release: **0.1**. Configuration schema version **4** is independent and retained for saved-setting compatibility.

All implementation choices below are proposed defaults. The confirmed requirements are in the root README.

## MIDI model

Store user-facing channels as 1–16 and encode them as 0–15 in status bytes. CC controller numbers and values are 0–127. PC values on the wire are 0–127; a selectable display offset may show 1–128 for applications using that convention, without changing stored MIDI values.

Each message has its own channel. A sequence can therefore combine, for example, bank selection on channel 2, PC on channel 2, and a CC on channel 5. Preserve the configured order. Empty release lists mean no release action.

Initial implementation limits: 32 messages per edge per switch, 128 messages total across all switches, with an optional delay before each message. Delays must use a scheduler; never block input scans or display updates with a sleep.

Example switch configuration (illustrative JSON, not an implemented file format):

```json
{
  "id": 1,
  "name": "Lead",
  "onPress": [
    { "type": "cc", "channel": 2, "controller": 0, "value": 0, "delayBeforeMs": 0 },
    { "type": "pc", "channel": 2, "program": 24, "delayBeforeMs": 0 },
    { "type": "cc", "channel": 5, "controller": 64, "value": 127, "delayBeforeMs": 0 }
  ],
  "onRelease": [
    { "type": "cc", "channel": 5, "controller": 64, "value": 0, "delayBeforeMs": 0 }
  ]
}
```

## Configurable switch count

Version-4 configuration adds `ladderLayout`: 1 for the modular four-switch base plus left-side pairs, 0 for legacy linear wiring. Modular counts are 4, 6, 8 and 10; linear mode supports 4–10, including odd counts. New defaults use modular wiring with ten switches selected. Set four for the base alone.

ADC codes, `switches[0..9]`, `ladder[1..10]`, MIDI engine inputs and the zero-based `/api` test switch index refer to permanent electrical taps. `switchTap` and `switchNumber` translate between tap identity and internal browsing position; `switchLabel` supplies the visible right-to-left letter/number labels. Both editors list switches and calibration in displayed order but write to the corresponding physical storage slot. Performance status includes the displayed label. The four-switch base owns T1 upper-left, T2 upper-right, T3 lower-left, T4 lower-right. Sections added to the left append T5/T6, T7/T8 and T9/T10 electrically; each pair is upper/lower. For ten switches, left-to-right labels are E,D,C,B,A / 5,4,3,2,1, corresponding to T9,T7,T5,T1,T2 / T10,T8,T6,T3,T4. Labels remain stable as sections are added. `switchNumber` returns an internal browsing position; `switchLabel` supplies the visible label. The HTTP status adds `keyLabel`; numeric `key` remains an internal position for compatibility.

Changing the count only changes visibility and internal browsing positions; it does not shuffle arrays. Actions, names, LED assignments and calibrated centers follow their physical switches, including when hidden and later re-enabled. Scanner decoding uses only idle plus T1..TN; inactive engine inputs and MIDI tests are rejected. Save & Exit applies changes after stable idle rearming.

Versions 1–3 migrate to version 4 in **linear** mode to preserve existing wiring and array interpretation. V1 receives a ten-switch count; v2/v3 retain their counts; v1/v2 receive disabled LEDs and 1:1 tap assignments. V3 retains its LED configuration. V4 requires an integer layout field, explicit count and LED fields. Validation checks non-overlapping active windows, finite/ranged centers for every slot, and MIDI validity/capacity across all stored mappings. [Wiring and voltage targets](resistor-ladders.md) explain two-conductor extension links and unchanged resistor values.

Wi-Fi switch/idle calibration, acceptance half-width and pedal heel/toe voltage fields show whole millivolts. Rendering and saving untouched fields preserve the stored measurement precision; explicit edits use 1 mV steps and commit rounded values. Captures retain their measured precision while displaying rounded millivolts. Non-voltage pedal parameters retain their original precision.

## Enclosure variant

Select **Right · Screen on right** or **Left · Screen on left** under Wi-Fi **Settings → Enclosure variant**. On the encoder, use **EDIT CONFIG → ENCLOSURE**, choose **RIGHT** or **LEFT**, click to accept, hold to return, and choose **SAVE & EXIT**. This single selector replaces the separate display orientation control.

| Variant | Screen | LCD rotation | Upper/lower labels from left to right (10 switches) |
|---|---|---:|---|
| Right | Right | 0° | E D C B A / 5 4 3 2 1 |
| Left | Left | 180° | A B C D E / 1 2 3 4 5 |

For 4/6/8/10 modular switches the Left variant lists upper taps T2,T1,T5,T7,T9 as applicable, then lower taps T4,T3,T6,T8,T10. Right reverses each row. Switch labels remain attached to those taps. The ten `switches` slots, eleven ladder centers, per-switch LED assignments, pedal settings and hidden mappings are never reordered or renamed by changing variants. Calibration and MIDI Test actions translate the visible selection back to the correct physical tap. In legacy linear mode each row is reversed too; for odd counts the upper row contains the extra switch.

Draft switch and calibration lists update immediately in either editor. The physical LCD direction and performance/status browsing position follow the **saved** variant: Wi-Fi **Save** applies it on the next frame; encoder **SAVE & EXIT** applies it on leaving setup. Discard restores the saved variant. Browser ownership uses the same saved LCD direction. A direction change forces a complete redraw, including when other screen content is unchanged. NVS and JSON export/import retain the variant across restarts.

New configurations default to **Left** (`enclosureVariant = 1`), with the screen on the left and 180° display rotation. Saved configurations retain their selected variant.

The optional version-4 integer field `enclosureVariant` accepts `0` (Right) or `1` (Left). New exports include this field only, with no independent `displayRotation` or `mirroredLayout` setting. Existing v1–v4 records without the selector migrate from an old `displayRotation`: 180 becomes Left, 0 becomes Right. If both are absent in an existing record, retain Right for backward compatibility. An explicit new selector takes precedence over a legacy rotation field. Types and ranges are validated; the existing migrations for wiring, switch count and LEDs still apply.

The driver retains its ST7789V2 landscape setup, 280×240 dimensions, RGB565 colors and (20, 0) offsets. Left reverses both axes of each DMA stripe and writes it to the opposite vertical window, using the existing 8,960-byte buffer. Host tests reconstruct all controller pixels and exercise ADC-to-MIDI/LED identity, both row orders for 4/6/8/10, mapped LCD and Wi-Fi edits/tests, strict JSON migration, save/reload and inactive data retention. Physical display and wiring checks remain part of board bring-up.

## Switch processing and ordering

- Sample the ladder approximately every 1–2 ms with calibrated non-overlapping voltage windows and guard bands. Use a stable-state debounce window, initially 10 ms.
- Accept one switch from idle. A stable different valid code ends the active action once and inhibits further presses until stable idle; a stable idle ends it normally. Brief guard-band readings retain state; an invalid reading persisting 50 ms ends the action once and latches a fault until idle. Never infer a new press from a guard band.
- Simultaneous footswitch presses are outside the supported operating requirements. After boot or reconnect require stable idle for the whole ladder before arming.
- Emit one event per debounced edge. Holding a switch does not repeat its sequence.
- At boot, establish the initial physical state without firing messages. A switch held at boot must first be released before it is armed for normal press/release actions.
- Snapshot the configured actions at press, including the release actions, so edits while held cannot substitute an unrelated release sequence.
- Preserve FIFO order for each switch: its press sequence completes before its release sequence starts, even if release occurs during a delay. Document that long press sequences can delay release messages.
- Across switches, schedule the earliest due message first; break ties by event capture order and then switch number. Preserve each individual sequence's order.
- Bound the queue. Reserve enough capacity for the accepted press and its optional release before accepting a press event. Report rejected actions visibly; do not send a partial press sequence because of a predictable capacity shortage.

## Pedal processing

Each input stores its electrical mode, configured maximum resistance (positive, at most 10 kΩ), endpoint calibration, curve, curve strength, inversion, MIDI channel, CC number, and output range. Reject invalid or coincident calibration endpoints.

Processing order:

1. Acquire calibrated internal-ADC samples, undo the 2:3 input scaling, and apply modest noise filtering. Schedule both pedals around the higher-priority ladder scans; start at 200 samples/s per pedal and measure settling after channel changes.
2. For resistor mode, convert voltage to resistance using the calibrated divider model.
3. Normalize between calibrated endpoints; for resistor mode, allow the configured maximum resistance to define the upper endpoint. Clamp valid travel to 0–1.
4. Apply inversion and the selected curve.
5. Scale and round into the configured 0–127 MIDI output range.
6. Send CC only when the quantized output changes, with hysteresis and a maximum update rate (initially 50 messages/s per pedal). Coalesce pending pedal changes so the latest value wins, while guaranteeing the final stable value is sent.

Define the response mathematically so "logarithmic" is unambiguous. Proposed normalized log curve:

```text
linear: y = x
log:    y = ln(1 + k*x) / ln(1 + k), k > 0
```

Both have exact endpoints at 0 and 1. A measured logarithmic potentiometer may need an inverse curve to produce a linear physical response; distinguish the requested output response from compensation for the pedal's physical taper. Consider an inverse-log option after prototype testing.

On a confirmed pedal fault, stop transmitting that pedal and show the fault. Do not infer a fault solely from reaching a valid endpoint.

## BLE MIDI

Operate as a standard BLE MIDI peripheral, advertising the MIDI service, rather than sending raw MIDI over a generic Bluetooth serial service. Use a maintained compatible transport implementation for timestamps, characteristic behavior, notifications, and MTU handling. Verify the chosen implementation against the ESP32-C6 target before adopting it.

Show disconnected, connected, and MIDI-ready states; accept transmission only once the central has subscribed to notifications. Drop actions while disconnected rather than replaying them on reconnect. Clear pending sequences and pedal updates on connection loss. Re-arm switches after they are released; do not transmit a release whose press was dropped. Surface a connection loss because remote MIDI state may remain latched. Provide an explicit user action to resend current pedal values or a configured recovery sequence; do not automatically replay old switch actions.

Initial iPad connection should use the MIDI application's BLE MIDI connection interface where available. Test reconnection on the actual iPad/application combination; do not assume generic Bluetooth pairing alone makes a MIDI port available.

## Modules

| Module | Responsibility |
| --- | --- |
| Board support | Verified GPIO map, SPI LCD, internal ADC and peripheral initialization |
| Switch scanner | Ladder ADC windows, debounce, active-switch state, event generation |
| Pedal service | ADC conversion scheduling, mode control, calibration, curves, CC coalescing |
| Action engine | Configuration snapshots, queue capacity, sequence order and delays |
| BLE transport | MIDI encoding, timestamped BLE packets, connection/readiness state |
| Wi-Fi editor | Setup access point, embedded browser assets, configuration API and edit-session ownership |
| Configuration store | Versioned data, validation, explicit saves, recovery from interrupted writes |
| Encoder input | Quadrature decoding, detent normalization, click debounce and long-press recognition |
| LCD UI | Performance screen, switch editing, pedal setup, diagnostics |

Screen redraws and flash saves must not block switch processing. Store validated settings persistently with versioning and an atomic or recoverable save process. Save on an explicit user operation, not continuously as pedals move. Start with an empty MIDI mapping so flashing the controller does not unexpectedly operate an attached instrument.

## Proposed LCD and encoder workflow

Performance view shows BLE state, active switch name and two pedal value indicators. Click the encoder to enter setup when the footswitch ladder is idle and any accepted release sequence has completed. Suppress performance MIDI in setup, except for an explicit Test action.

- Rotate: move one menu item per detent, or adjust the selected value by one unit per detent. Start without acceleration.
- Short click: select an item, enter value editing, or accept an edited value into the working configuration.
- Hold for 700 ms: cancel the current value edit or go back one menu level. Emit the short-click event only on release if no long-press event fired.
- Provide visible Back, Save & Exit, and Discard & Exit items. Saving persists the complete validated working configuration; backing out does not silently save it. After exit, require the footswitch ladder to reach stable idle before rearming performance actions.

Use seven-row scrolling lists on the 280×240 landscape display. Editing a switch exposes separate press/release lists with add, delete, reorder, channel, CC/PC data, and optional delay. Pedal settings expose electrical mode, maximum resistance where applicable, calibration, curve, inversion, channel, CC, and output range. Require an explicit test action before transmitting from an editor.

Decode A/B with a quadrature state table, reject invalid transitions, and accumulate valid transitions into one logical step per physical detent according to the selected encoder datasheet. Capture transitions promptly using GPIO interrupts or sufficiently fast polling; queue navigation events for the UI rather than drawing from an interrupt. Do not apply the click's 20 ms stable-state debounce independently to A/B, which can lose rotation steps. Initialize from the actual A/B state at startup. A held click at boot must be released before producing a click action.


## Wi-Fi configuration editor

The controller hosts a responsive browser editor with the same configuration model and validation rules as the LCD menus. Support iPad Safari as the primary browser. Serve all HTML, CSS, JavaScript, and fonts from onboard flash; setup works without internet or a cloud account.

### Connection and setup lifecycle

1. Select **Wi-Fi Setup** with the encoder. Enter setup only after the ladder is idle and accepted action sequences have completed. Suspend normal switch/pedal MIDI, retaining only explicitly requested MIDI tests.
2. Start a WPA2-protected access point named `SIGMIDI-xxxx`, with a generated device-specific password. Display the SSID, password, and browser address on LCD pages. Proposed fixed address: `http://192.168.4.1`; configure the device IP and DHCP server consistently. Joining an existing router is outside the initial scope.
3. Join this network on the iPad and open the displayed address in Safari. The network intentionally has no internet. A captive-portal helper may be added, but the full Safari page and direct IP address are the required access path.
4. Edit a draft, then choose **Save**, **Discard**, or **Save & Exit**. Saving validates the entire configuration and persists it atomically before activating it. Saving alone keeps setup open. Returning to performance disables Wi-Fi and rearms footswitches only after stable idle.
5. A browser disconnect leaves the last saved configuration intact. Retain the draft in RAM for reconnection while setup remains active; show its unsaved state locally. Power loss discards only unsaved edits. The encoder always provides a way to discard the draft and exit setup.

For Save & Exit, return the save result before shutting down the access point; schedule shutdown after a short grace period. If the browser loses the response, show the saved configuration revision on the LCD so success can be checked locally. Do not report a successful save before the persistent write completes.

### Editor capabilities

- Name each active switch (six to ten); edit, add, remove, and reorder press and release messages, including CC/PC type, channel, values, and delay.
- Edit both pedal configurations: electrical mode, maximum resistance, calibration endpoints, linear/log curve and strength, inversion, channel, CC number, and output range.
- Provide guided pedal and ladder calibration with live readings. Starting calibration is explicit; changing electrical pedal mode follows the unplug/change/reconnect workflow. Keep temporary calibration/mode changes scoped to setup, restore saved settings on discard, and suppress pedal MIDI during calibration.
- Edit global settings exposed locally, such as debounce and PC display numbering. Provide device status, BLE readiness, validation errors, and explicit MIDI Test actions.
- Export/import versioned JSON backups. Exclude Wi-Fi credentials and session tokens. Validate imports on the device before replacing the draft; incompatible versions and invalid values leave existing settings intact.

### Shared state and implementation

Use one server-side draft and one writer at a time. A browser edit session temporarily makes local configuration editing read-only, while preserving the encoder's status and exit controls. Additional browser sessions can view status; they must explicitly acquire ownership after the current writer exits or its lease expires. Each write includes the draft revision; reject stale writes instead of silently overwriting newer edits.

Separate stored configuration from runtime state. Bound request sizes, message counts, and telemetry rates; initially stream or poll status at no more than 10 Hz. Share the schema and server-side validation with local editing. Require an authenticated setup session and CSRF protection for mutations; never use a universal default access-point password. The HTTP editor is available only on the locally enabled setup network.

Keep BLE available for explicit MIDI testing where coexistence permits, but do not promise performance latency while Wi-Fi is active. ESP32-C6 shares its radio between Wi-Fi and BLE; Espressif lists restrictions for SoftAP/BLE coexistence. Validate connection and test-message delivery with the selected ESP-IDF version and actual iPad. Normal performance uses Wi-Fi off. No additional hardware is needed.

## Acceptance criteria

- iPad Safari can connect to the protected setup access point and edit every configuration field without internet. Save, discard, import/export, reconnect, conflicting editors, invalid requests, and interrupted saves preserve the documented state.
- Exiting Wi-Fi setup stops the server/access point and restores normal BLE MIDI operation; editing or calibration emits no unintended MIDI.
- Encoder movement produces exactly one navigation step per detent in either direction; reversal and contact bounce do not create extra steps. Click and long press are mutually exclusive, and Save/Discard behave as labeled.

- All ten switches work individually; bounce does not duplicate press or release edges. Simultaneous footswitch detection is not an acceptance criterion.
- Press and optional release sequences preserve order and per-message channels, including release during a delayed press sequence.
- CC and PC boundary values encode correctly; invalid channels/data are rejected.
- Both pedal modes work independently, including one input of each type; changing modes changes the electrical pull-up state.
- Resistor-mode calibration reaches full MIDI output at configurable maxima below 10 kΩ as well as at 10 kΩ.
- Linear/log curves, inversion, and endpoint calibration behave as documented; a stationary pedal produces no sustained CC stream.
- Pedal traffic does not starve switch actions, screen updates, or connection handling.
- Queue overflow is visible and predictable; disconnect does not replay stale actions after reconnect.
- Saved settings survive power cycles and interrupted writes; invalid configuration has a visible recoverable fallback.
- Measure end-to-end latency and jitter on the target iPad under simultaneous switch, pedal, and screen activity. Set final performance targets from those results.

## Sources

- [MIDI Association BLE MIDI specification](https://midi.org/midi-over-bluetooth-low-energy-ble-midi): transport interoperability requirements.
- [Espressif BLE MIDI documentation](https://docs.espressif.com/projects/esp-iot-solution/en/latest/bluetooth/ble_midi.html): an implementation reference; target/version compatibility still needs checking.
- [Apple MIDI Bluetooth documentation](https://developer.apple.com/documentation/coremidi/midi-bluetooth): Core MIDI BLE connection behavior and pairing-related reconnection support.

- [Espressif ESP32-C6 RF coexistence](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-guides/coexist.html): shared radio and Wi-Fi/BLE coexistence restrictions.

## Waveshare 24382 graphics implementation

The ST7789V2 driver maps the 280×240 landscape image to columns 20–299 and rows 0–239, uses RGB565 and sends 16-row stripes at 10 MHz. One DMA stripe occupies 8,960 bytes; the renderer does not allocate a full framebuffer. A changed view triggers a redraw outside the shared state mutex; unchanged views are skipped.

`uiView()` produces the same view model for hardware rendering and host previews. The performance screen uses a large switch number/name, BLE status and two CC-value bars. Setup shows seven highlighted rows with a scrollbar and breadcrumb; editing has a distinct amber marker. Compact message lists color PC cyan and CC orange. PC editors show PROGRAM and omit VALUE; CC editors show CONTROL and VALUE. Editable rows place names on the left and values in a shared column at X164. Long text values wrap within that column. Labels use short forms such as DELAY MS, MAX OHMS and LOG CURVE. Menu actions (DELETE, MOVE UP, APPEND MSG, TEST SEQ and save/exit actions) use purple text, distinct from gray parameter names and white values; the active value turns amber during editing. New messages retain the 5 ms default delay before sending. Wi-Fi setup shows SSID, password and local URL; browser ownership has its own status view. Content stays away from the physically rounded screen corners.

Run `scripts/preview_display.py` with Python/Pillow, a C++17 compiler and the installed ESP-IDF cJSON sources to regenerate native-size previews from the real UI and renderer. Host rendering tests verify display windows, stripe/frame equivalence and buffer boundaries; they do not validate the physical LCD controller.

## Optional WS2811 feedback

Schema 3 stores global `leds` settings (enabled, brightness, color order, protocol) and each switch's `led` assignment, with 0 meaning unassigned. Initial settings disable the chain, set brightness to 64/255, and pair switches 1–10 with pixels 1–10. Press and release colors are white and yellow. Older versions migrate with these LED defaults.

The MIDI engine snapshots the LED assignment with the press/release lists, and emits one action callback when a phase's first message is accepted by the BLE transport. Further messages do not retrigger it. Empty phases, queue rejection and failed sends have no performed-action callback. This preserves delayed press/release ordering. Feedback indicates local BLE queuing, not acknowledgement from the iPad. Explicit MIDI tests use the same first-success rule.

The shared LED state clears on setup/readiness transitions and saved LED/count/mapping changes. Its hardware task snapshots a frame under the mutex and transmits outside it, independently of the LCD. The default Pololu 2535 profile uses RGB order and RMT at 20 MHz to generate 0.35/0.90 µs zero pulses and 0.90/0.35 µs one pulses, with a 350 µs low reset. Other legacy WS2811 profiles remain selectable; an IRAM-safe copy encoder and internal symbol buffer preserve timing during flash writes. Frames are sent on changes and refreshed every 250 ms because the Pololu 2535 powers up blue before receiving data; this also restores colors after the LED supply restarts. LED driver failure reports a notice while MIDI continues. See [wiring, settings and bench checks](leds.md).
