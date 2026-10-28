# SIGMIDI Foot Controller v0.1 — Pololu 2535 switch indicators (optional)

The specified part is **[Pololu 2535](https://www.pololu.com/product/2535)**: a 10-pack of 5 mm diffused through-hole RGB LEDs with the WS2811 driver integrated into each LED. Fit one LED per installed footswitch (4/6/8/10 modular). Each package is one addressable pixel; no separate WS2811 IC or per-color current-limiting resistors are required. In modular wiring, initial assignments are physical tap T1 → LED 1 through T10 → LED 10. Route data through the four base switches first (upper-right B, upper-left A, lower-right 2, lower-left 1 in the preferred Left enclosure), then each right extension upper/lower pair, nearest section first. Displayed labels stay fixed as sections are added: base A/B and 1/2 from left to right, followed by C/3, D/4 and E/5 on extensions to the right. LED identity stays attached to the physical switch. See [modular ladder and LED ordering](resistor-ladders.md). Chain order is electrical DIN/DOUT order; use the per-switch assignment if the physical wiring order differs. Assignment 0 disables that switch's indicator. Duplicate assignments share a pixel; the most recent performed action wins.

The chain is **disabled by default**, with brightness **64/255**. With it enabled, a press action sets the assigned LED to **white**; a release action sets it to **yellow**. Colors remain until the next action or a reset condition. Each LED is independent, so operating another switch does not erase previous indicators.

A performed action means the BLE transport accepts its first MIDI message for notification. LEDs do not claim acknowledgement by the receiving iPad. Empty lists leave the LED unchanged, failed sends wait without changing it, and rejected/unarmed switch events do not light it. Delayed press and release lists retain FIFO order; LED changes occur when their respective first messages are accepted, not at the raw switch edge. The switch-to-LED assignment is captured with the MIDI lists on press. Explicit MIDI Test actions also drive the selected LED.

Firmware sends an all-off frame during startup, then clears the indicators on setup entry/exit, BLE readiness changes, or changes to saved LED settings, switch count or assignments. Draft changes take effect for normal operation after saving. Save the global chain settings before explicit MIDI tests; a test uses the draft switch's assignment. With a missing or disabled chain the controller continues operating normally. LED output failures do not abort MIDI processing.

## Variant and lead identification

Use these settings for **every Pololu 2535 LED**: **5 V supply, RGB byte order, PROTOCOL 2535 (800 kbit/s)**. The alternate timing profiles are not the settings for this part. Each LED draws approximately **50 mA at full white**, so ten require approximately **0.5 A** before controller/display load. These specifications and the lead diagram come from [Pololu's product documentation](https://www.pololu.com/product/2535).

Identify leads before trimming. In the [manufacturer's side-view diagram](https://a.pololu-files.com/picture/0J5433.1200.jpg), with the **lens pointing left, leads pointing right and the flat side at the bottom**, the leads are **top to bottom**:

| Position in that view | Signal | Connection |
| --- | --- | --- |
| Top, farthest from flat side | DIN | DFRobot TX / GPIO16 directly for LED 1; preceding LED's DOUT for LEDs 2–N |
| Second | +5 V | Regulated LED supply, in parallel to every LED |
| Third | GND | Common ground, in parallel to every LED and the controller |
| Bottom, nearest flat side | DOUT | Next LED's DIN; leave the final LED's DOUT unconnected |

This side view is not a bottom view; turning the LED over reverses the visible order. The four leads are power/data connections, not the red/green/blue/common terminals of an analog RGB LED.

## Wiring

Use **GPIO16 / IO16 / TX** on the DFR1075 header for LED data. The project's console uses USB Serial/JTAG, leaving that UART TX pad available. The data GPIO is independent of switch, LCD, pedal and encoder connections. The pin assignment follows the [DFRobot board documentation](https://wiki.dfrobot.com/dfr1075/) and its [V1.1 schematic](../design/fusion/datasheets/dfr1075-schematic-v11.pdf).

The LED chain contains only the Pololu 2535 LEDs and wiring. Connect the DFRobot data output directly to the first LED's DIN. Supply every LED from the regulated 5 V rail and common ground, in parallel. The WS2811 driver is already inside each LED; no additional driver, buffer, series resistor, pulldown or capacitor is fitted in the chain.

```text
DFRobot TX / GPIO16 (P2:17) -------- LED1 DIN
LED1 DOUT ------------------------ LED2 DIN
LED2 DOUT ------------------------ LED3 DIN ... final LED DOUT open
Regulated +5V -------------------- every LED's 5V lead
Supply GND ----------------------- every LED's GND lead
DFRobot GND (P1:3 or P2:4) -------- supply GND
```

Each LED box in the electrical diagram uses the actual package side-view lead order: lens left, flat down, with DIN / 5V / GND / DOUT on the right from top to bottom. Use the flat-side reference before cutting or bending leads. The source photograph is included unchanged in the diagram. A raised wire hop crosses the +5 V rail without connecting to it.

The GPIO signal is 3.3 V while LED power is 5 V. The Pololu product page does not specify a guaranteed 3.3 V DIN threshold; verify direct-drive operation with the purchased LED batch and actual harness. Keep the data wire short and alongside a ground return. Firmware sends an all-off frame at initialization; no added component holds the data input low during MCU reset.

Power this chain from a **regulated 5.0 V rail that does not exceed 5 V at the LEDs**, with common ground to the controller. Do not use a 12 V LED supply or the DFR1075 3V3 output. For a dedicated supply, allow at least **1 A for the LED rail** plus any shared controller load. The Pololu 4083 has a **1 A total** limit; validate the combined load as described in the power guide. The default 64/255 brightness gives about 0.13 A for ten white LEDs by PWM scaling, plus driver overhead; size the supply for the full-white setting. Avoid joining independent positive supply outputs together. Make or change wiring only with power off.

**Power-on blue is normal for this variant.** Pololu states that these LEDs illuminate blue until the first color command. A brief blue indication can occur before firmware initializes, even with LED feedback disabled. The initial black frame clears it; frames are also refreshed approximately every 250 ms so an independently restarted LED supply receives the intended colors again. A startup indication before firmware runs cannot be eliminated by a software setting. [Pololu power-up behavior](https://www.pololu.com/product/2535).

## Configuration

- LCD: **EDIT CONFIG → LED CHAIN**: ENABLED, BRIGHTNESS, RGB ORDER, PROTOCOL. Under **switches → switch number → LED NO.**, choose 1–10 or OFF.
- Wi-Fi: **Settings → Pololu 2535 LED chain (optional)**. Each switch has an **LED assignment** selector.
- Global brightness is an integer 0–255. Initial RGB values are white `(brightness, brightness, brightness)` and yellow `(brightness, brightness, 0)`; colors are fixed.
- For this part select **RGB**, the initial setting. Other channel orders are available for alternative hardware. Do not use a WS2812B GRB preset for the Pololu 2535.

| Protocol selector | Rate | 0 high / low | 1 high / low | Reset low |
| --- | --- | --- | --- | --- |
| 2535 (default) | 800 kbit/s, Pololu 2535 | 0.35 / 0.90 µs | 0.90 / 0.35 µs | 350 µs |
| OLD 800K | 800 kbit/s, two-speed WS2811 | 0.25 / 1.00 µs | 0.60 / 0.65 µs | 350 µs |
| OLD 400K | 400 kbit/s, two-speed WS2811 | 0.50 / 2.00 µs | 1.20 / 1.30 µs | 350 µs |

The **2535** profile uses 1.25 µs bits, most-significant bit first, RGB order and a 350 µs reset. OLD 800K and OLD 400K are selectable timing profiles for other two-speed WS2811 hardware. Use 2535 for the specified Pololu part.

Configuration schema **4** stores global settings and a `led` assignment in each of ten switch entries:

```json
"leds": {"enabled": false, "brightness": 64, "colorOrder": 0, "protocol": 0}
```

Assignment 0 disables an indicator; 1–10 selects a pixel. Defaults pair taps T1–T10 with pixels 1–10. Hidden switch assignments remain stored when the installed count is reduced.

## Implementation and bench check

`leds.cpp` stores the latched colors and generates RGB bytes and MSB-first timing symbols. `led_hardware.cpp` uses ESP-IDF's RMT copy encoder at 20 MHz resolution, 96 symbols of hardware memory, priority-3 IRAM-safe interrupts, and a separate task. Ten pixel addresses are always transmitted, clearing unused trailing indicators when the count is reduced. Extra addresses are ignored by a shorter chain. Frames are sent at startup, on changes and every 250 ms to restore the LEDs after an LED-rail power cycle. A frame takes about 0.65 ms at 800 kbit/s or 0.95 ms at 400 kbit/s including the reset; it does not wait inside the MIDI/state mutex. [ESP-IDF RMT documentation](https://docs.espressif.com/projects/esp-idf/en/v5.3.1/esp32c6/api-reference/peripherals/rmt.html).

1. With power disconnected, wire each Pololu 2535 using the flat-side orientation above, then apply 5 V power. Select RGB and 2535, enable the chain and Save. A blue power-on interval can precede the firmware's black frame; setup clearing should then leave the LEDs off.
2. With BLE MIDI subscribed, configure one press and one release MIDI message for switch 1. Press for white and release for yellow; verify the MIDI monitor receives both messages. Test every installed switch against its assigned pixel.
3. Check empty release lists leave the previous color unchanged. Check a delayed press followed by an early release gives the same press/release order as MIDI; rejected sends must not show a performed-action color.
4. Change an assignment and brightness, save, and repeat. Test BLE disconnect/reconnect, setup entry/exit, MIDI Test actions and power cycling.
5. Check the data waveform and reset interval at DIN with the actual module, including BLE traffic, Wi-Fi MIDI tests and flash saves. Also power-cycle just the LED supply and check that periodic refresh restores the intended colors. Host tests and compilation do not qualify physical timing, supply integrity or iPad delivery.

## Chassis mounting

Each optional LED sits below its switch on the same panel level. Upper centers are 14.7 mm in front of the switch centers; lower centers are 17.2 mm in front. The main body is 350 × 92 × 54 mm, with 65 mm switch pitch, 53 mm row spacing and 30 mm elevation. Left labels read A–E / 1–5 left to right; Right reverses each row.

Each port has a 5.4 mm bore, 6.4 × 0.8 mm flange recess and 0.8 mm exterior breakaway cover. Internal Ø10.4 mm seats extend 4.9 mm below the roof. The flange shoulder is 7.1 mm below the surface; nominal flange bottom is 7.9 mm below it. The reference 8.7 mm package gives **0.8 mm dome exposure**, within the 1 mm maximum. Verify actual flange, height and lead dimensions before printing.

Leave covers intact when omitting LEDs. Open and finish holes before fitting electronics, seat flanges from inside and secure after checking fit. Root tapers and teardrop ceilings provide 45° print support. Use the manufacturer's lead orientation; route insulated data and power buses through the reserved interior corridors, clear of fasteners, PCB components, spring clips, grilles and the removable-base interface. Print the shell/base solids, not the fitted LED or wiring reference bodies.

## Supply

Use regulated 5 V. With the Pololu 4083 converter, **1 A is the total budget for controller and LEDs**. Branch LED current at the supply point and return it directly there. A dedicated LED supply can be sized for at least 1 A plus any shared controller load. See [power wiring and limits](power.md).
