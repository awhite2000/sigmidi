# SIGMIDI Foot Controller v0.1 — Pololu 2535 switch indicators (optional)

The specified part is **[Pololu 2535](https://www.pololu.com/product/2535)**: a 10-pack of 5 mm diffused through-hole RGB LEDs with the WS2811 driver integrated into each LED. Fit one LED per installed footswitch (4/6/8/10 modular). Each package is one addressable pixel; no separate WS2811 IC or per-color current-limiting resistors are required. In modular wiring, initial assignments are physical tap T1 → LED 1 through T10 → LED 10. Route data through the four base switches first (upper-right B, upper-left A, lower-right 2, lower-left 1 in the preferred Left enclosure), then each right extension upper/lower pair, nearest section first. Displayed labels stay fixed as sections are added: base A/B and 1/2 from left to right, followed by C/3, D/4 and E/5 on extensions to the right. LED identity stays attached to the physical switch. See [modular ladder and LED ordering](resistor-ladders.md). Chain order is electrical DIN/DOUT order; use the per-switch assignment if the physical wiring order differs. Assignment 0 disables that switch's indicator. Duplicate assignments share a pixel; the most recent performed action wins.

The chain is **disabled by default**, with brightness **64/255**. With it enabled, a press action sets the assigned LED to **white**; a release action sets it to **yellow**. Colors remain until the next action or a reset condition. Each LED is independent, so operating another switch does not erase previous indicators.

A performed action means the BLE transport accepts its first MIDI message for notification. LEDs do not claim acknowledgement by the receiving iPad. Empty lists leave the LED unchanged, failed sends wait without changing it, and rejected/unarmed switch events do not light it. Delayed press and release lists retain FIFO order; LED changes occur when their respective first messages are accepted, not at the raw switch edge. The switch-to-LED assignment is captured with the MIDI lists on press. Explicit MIDI Test actions also drive the selected LED.

Firmware sends an all-off frame during startup, then clears the indicators on setup entry/exit, BLE readiness changes, or changes to saved LED settings, switch count or assignments. Draft changes take effect for normal operation after saving. Save the global chain settings before explicit MIDI tests; a test uses the draft switch's assignment. With a missing or disabled chain the controller continues operating normally. LED output failures do not abort MIDI processing.

## Variant and lead identification

Use these settings for **every Pololu 2535 LED**: **5 V supply, RGB byte order, PROTOCOL 2535 (800 kbit/s)**. The 400 kbit/s and legacy profiles are not the settings for this part. Each LED draws approximately **50 mA at full white**, so ten require approximately **0.5 A** before controller/display load. These specifications and the lead diagram come from [Pololu's product documentation](https://www.pololu.com/product/2535).

Identify leads before trimming. In the [manufacturer's side-view diagram](https://a.pololu-files.com/picture/0J5433.1200.jpg), with the **lens pointing left, leads pointing right and the flat side at the bottom**, the leads are **top to bottom**:

| Position in that view | Signal | Connection |
| --- | --- | --- |
| Top, farthest from flat side | DIN | Buffer output for LED 1; preceding LED's DOUT for LEDs 2–N |
| Second | +5 V | Regulated LED supply, in parallel to every LED |
| Third | GND | Common ground, in parallel to every LED and the controller |
| Bottom, nearest flat side | DOUT | Next LED's DIN; leave the final LED's DOUT unconnected |

This side view is not a bottom view; turning the LED over reverses the visible order. The four leads are power/data connections, not the red/green/blue/common terminals of an analog RGB LED.

## Wiring

Use **GPIO16 / IO16 / TX** on the DFR1075 header for LED data. The project's console uses USB Serial/JTAG, leaving that UART TX pad available. Keep the existing switch, LCD, pedal and encoder wiring. The pin assignment follows the [DFRobot board documentation](https://wiki.dfrobot.com/dfr1075/) and its [V1.1 schematic](../design/fusion/datasheets/dfr1075-schematic-v11.pdf).

For the Pololu 2535 chain, use one gate of an **SN74AHCT125 powered at 5 V** to translate the 3.3 V GPIO. Its TTL-compatible input accepts the ESP32 signal; ordinary 5 V HC logic does not give the same input-level guarantee. Pin numbers below apply to the standard 14-pin D/N/PW packages. [TI datasheet](https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf).

```text
DFR1075 GPIO16 ────────────── SN74AHCT125 1A (pin 2)
                    │        1OE (pin 1) ───────── GND
                   10kΩ      VCC (pin 14) ──────── regulated +5 V
                    │        GND (pin 7) ───────── common GND
                   GND       100 nF between pins 14 and 7, close to IC

SN74AHCT125 1Y (pin 3) ── 330Ω ── DIN [LED 1] DOUT ── DIN [LED 2] ... [LED N]
LED supply +5 V ─────────────────── LED 1 V+ ────── LED 2 V+ ─── ... LED N V+
Common GND ──────────────────────── LED 1 GND ───── LED 2 GND ── ... LED N GND
             └── DFR1075 GND
```

Place the 330 Ω data resistor near the first LED's DIN; this is within Pololu's suggested 100–1000 Ω range. Pololu specifies at least 10 µF across the supply; this design uses **470 µF at the chain entry**, plus **100 nF directly across +5 V/GND at each LED** for local bypassing. Use capacitors rated at least 10 V, observing electrolytic polarity. Tie unused AHCT125 output-enable pins 4, 10 and 13 high to 5 V, and unused data-input pins 5, 9 and 12 to GND; leave their outputs unconnected. Keep data wiring short and route it alongside a ground return. The 10 kΩ pulldown holds the buffer input low while the MCU is resetting; software sends an all-off frame during initialization.

Power this chain from a **regulated 5.0 V rail that does not exceed 5 V at the LEDs**, with common ground to the controller. Do not use a 12 V LED supply or the DFR1075 3V3 output. Allow at least **1 A for the LED rail**, plus controller/display headroom if sharing a supply. The default 64/255 brightness gives about 0.13 A for ten white LEDs by PWM scaling, plus driver overhead; size the supply for the full-white setting. Avoid joining independent positive supply outputs together. Make or change wiring only with power off.

**Power-on blue is normal for this variant.** Pololu states that these LEDs illuminate blue until the first color command. A brief blue indication can occur before firmware initializes, even with LED feedback disabled. The initial black frame clears it; frames are also refreshed approximately every 250 ms so an independently restarted LED supply receives the intended colors again. A startup indication before firmware runs cannot be eliminated by a software setting. [Pololu power-up behavior](https://www.pololu.com/product/2535).

## Configuration

- LCD: **EDIT CONFIG → LED CHAIN**: ENABLED, BRIGHTNESS, RGB ORDER, PROTOCOL. Under **switches → switch number → LED NO.**, choose 1–10 or OFF.
- Wi-Fi: **Settings → Pololu 2535 LED chain (optional)**. Each switch has an **LED assignment** selector.
- Global brightness is an integer 0–255. Initial RGB values are white `(brightness, brightness, brightness)` and yellow `(brightness, brightness, 0)`; colors are fixed for this first implementation.
- For this part select **RGB**, the initial setting. Other channel orders remain available only for alternative hardware. Do not use a WS2812B GRB preset for the Pololu 2535.

| Protocol selector | Rate | 0 high / low | 1 high / low | Reset low |
| --- | --- | --- | --- | --- |
| 2535 (initial) | 800 kbit/s, Pololu 2535 | 0.35 / 0.90 µs | 0.90 / 0.35 µs | 350 µs |
| OLD 800K | 800 kbit/s, legacy two-speed WS2811 | 0.25 / 1.00 µs | 0.60 / 0.65 µs | 350 µs |
| OLD 400K | 400 kbit/s, legacy two-speed WS2811 | 0.50 / 2.00 µs | 1.20 / 1.30 µs | 350 µs |

The **2535** profile follows [Pololu's protocol](https://www.pololu.com/product/2535): 1.25 µs per bit, most-significant bit first, with RGB channel order. The 350 µs reset is longer than its required 50 µs. The two OLD profiles remain for other hardware and follow the [older two-speed Worldsemi datasheet](https://www.mouser.com/datasheet/3/1348/1/WS2811.pdf). Existing saved settings are retained; select RGB and 2535 if a previous configuration used another profile. No JSON schema change is needed.

Schema version **3** adds a required global object and required `led` field in each of the ten switch entries:

```json
"leds": {"enabled": false, "brightness": 64, "colorOrder": 0, "protocol": 0}
```

Each switch initially has `"led": 1`, `"led": 2`, etc. All ten stored assignments are retained when reducing the active switch count. Version-1 and version-2 backups/NVS migrate automatically, preserving MIDI lists, pedal settings and ladder calibration while adding disabled LEDs and 1:1 assignments. Version 1 also receives a ten-switch count. Version 4 adds modular labels; v1–3 data migrates in Linear mode. Older firmware cannot read version-4 backups.

## Implementation and bench check

`leds.cpp` stores the latched colors and generates RGB bytes and MSB-first timing symbols. `led_hardware.cpp` uses ESP-IDF's RMT copy encoder at 20 MHz resolution, 96 symbols of hardware memory, priority-3 IRAM-safe interrupts, and a separate task. Ten pixel addresses are always transmitted, clearing unused trailing indicators when the count is reduced. Extra addresses are ignored by a shorter chain. Frames are sent at startup, on changes and every 250 ms to restore the LEDs after an LED-rail power cycle. A frame takes about 0.65 ms at 800 kbit/s or 0.95 ms at 400 kbit/s including the reset; it does not wait inside the MIDI/state mutex. [ESP-IDF RMT documentation](https://docs.espressif.com/projects/esp-idf/en/v5.3.1/esp32c6/api-reference/peripherals/rmt.html).

1. With power disconnected, wire each Pololu 2535 using the flat-side orientation above, then apply 5 V power. Select RGB and 2535, enable the chain and Save. A blue power-on interval can precede the firmware's black frame; setup clearing should then leave the LEDs off.
2. With BLE MIDI subscribed, configure one press and one release MIDI message for switch 1. Press for white and release for yellow; verify the MIDI monitor receives both messages. Test every installed switch against its assigned pixel.
3. Check empty release lists leave the previous color unchanged. Check a delayed press followed by an early release gives the same press/release order as MIDI; rejected sends must not show a performed-action color.
4. Change an assignment and brightness, save, and repeat. Test BLE disconnect/reconnect, setup entry/exit, MIDI Test actions and power cycling.
5. Check the data waveform and reset interval at DIN with the actual module, including BLE traffic, Wi-Fi MIDI tests and flash saves. Also power-cycle just the LED supply and check that periodic refresh restores the intended colors. Host tests and compilation do not qualify physical timing, supply integrity or iPad delivery.

## Chassis mounting — LEDs below switches

The current Fusion chassis is **350 × 92 mm**, with one optional LED directly below each switch on its own panel level. Upper LED centers are 14.7 mm in front of their switch centers; lower LEDs are 17.2 mm in front. Switch pitch remains 65 mm. The upper deck is extended 8 mm, increasing the row spacing to 53 mm, and the front apron adds another 6 mm. The upper row remains 30 mm higher. The MCU and rear USB subsequently move 65 mm right under raised SW4; the TRS later moves beside SW5, with its ports 3 mm lower; the latest revision shifts it 10 mm left to midpoint X319 and 1 mm inward to match its reinforced rear wall. In the LED enclosure enlargement, the lower controls, display and their supports move 8 mm toward the front.

Each port has a **5.4 mm bore**, **6.4 mm × 0.8 mm flange recess**, and a **0.8 mm exterior breakaway cover**. Internal Ø10.4 mm seats extend 4.9 mm below the roof, with the flange shoulder 7.1 mm below the panel surface. The LED flange bottom sits 7.9 mm below the surface, leaving **0.8 mm nominal dome exposure** against the **1 mm maximum**, based on the reference 8.7 mm package height. Check the actual package and adjust the shoulder depth before printing if needed. Leave the covers intact when omitting LEDs. When installing, open and finish the bores before fitting electronics, seat the LED flanges from inside, and secure them with suitable adhesive after verifying fit. The hidden `LED01`–`LED10` Fusion components represent the installed option; print only the shell/base solids, which retain their covers. The installed preview temporarily removes covers to show the LEDs.

The reference flange, package height and lead dimensions are conservative modeling assumptions, because Pololu publishes a nominal 5 mm lens rather than a complete dimensioned package drawing. Confirm these against the purchased LEDs before printing. Four-lead solder/heatshrink spaces and two wire buses with a descent and crossover are reserved inside the enclosure. The lower bus sits at Y83.5–85.5 mm and Z−12 to −9 mm, below the recessed seats and clear of the front overlap rib. In the current encoder-right layout, the right crossover uses X338.5–342.5 mm at Z−17 to −14 mm, clearing the shifted display posts and staying 3 mm below the encoder housing. The front-right M2 boss is at Y85 mm; the lower bus passes 3 mm above it. The upper descent now occupies Y30.4–34.4 mm, 3 mm forward of the relocated TRS housing/saddle; a short turn joins the upper bus, and the low crossover begins at Y31.4. Run the crossover below the stepped roof; keep wiring clear of the display, MCU and removable-base interface. See `design/fusion/print/pololu-led-mounts.json` for exact placements and check results.

The LED seat print refinement adds 45° root tapers in each shell’s end-down print direction and 45° teardrop ceilings inside the seats. The circular front membranes remain 0.8 mm thick; LED positions and nominal 0.8 mm dome exposure are unchanged. See `design/fusion/print/led-support-comparison.json` for the slicer check.

The DFR1075 is subsequently moved 8.299886 mm right to retain 5 mm to SW10. Its adjacent support is now on the left at X232; the USB pocket and mounting posts follow. LED positions and wire corridors remain unchanged and are checked against this placement. See `design/fusion/print/mcu-switch10-clearance.json`.

## Alternate DC source

The optional 9 V center-negative barrel input and Pololu 4083 can provide the LED rail as well as the controller, subject to its **1 A total output limit**. Branch LED power and return at the regulator/distribution point; do not route LED current through the DFRobot header. USB-only use does not imply that this external rail is powered. See [power wiring and current budget](power.md).
