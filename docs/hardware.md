# SIGMIDI Foot Controller v0.1 — Proposed hardware and wiring

Target: DFRobot DFR1075 FireBeetle 2 ESP32-C6, using its internal ADC, and Waveshare 24382 1.69-inch ST7789V2 color LCD, used in landscape at 280×240. This is a prototype wiring proposal; verify against the actual board revision before assembly. All logic and analog circuits use 3.3 V and common ground. Only one footswitch needs to be detected at a time.

## Alternate power input

Use a **9 V DC center-negative 2.1 × 5.5 mm barrel supply** through the Pololu S13V10F5 (Pololu 4083 / Kamami 1178565). Its regulated VOUT goes to the DFR1075 **5 V input (VIN/VCC)** and GND goes to **GND**. Raw 9 V connects only to the converter input. See [power wiring, source selection, budget and mounting](power.md). USB programming remains available through the board's existing power-selection circuit. No firmware/GPIO changes are required.

## Wi-Fi configuration access

Use the ESP32-C6 onboard Wi-Fi radio for the configuration editor. No additional module, wiring, or GPIO is required. Wi-Fi is enabled explicitly for setup and disabled when returning to performance mode; see the firmware specification for connection and save behavior.

## GPIO assignments

Use GPIO numbers in firmware, not Arduino D-label numbers. Do not connect a second display through the GDI connector: some signals below share its nets.

| Function | ESP32-C6 GPIO | Connection |
| --- | --- | --- |
| Switch ladder | 1 / ADC1_CH1 | Ladder sense node |
| Pedal 1 | 2 / ADC1_CH2 | Scaled buffered pedal 1 signal |
| Pedal 2 | 3 / ADC1_CH3 | Scaled buffered pedal 2 signal |
| LCD DIN | 22 | SPI MOSI |
| LCD CLK | 23 | SPI SCK |
| LCD CS | 18 | Active-low chip select |
| LCD DC | 19 | Data/command |
| LCD RST | 14 | Active-low reset |
| LCD BL | 3V3 | Always-on backlight |
| Pedal 1 mode | 20 | Pull-up MOSFET control |
| Pedal 2 mode | 21 | Pull-up MOSFET control |
| Encoder A | 6 | Quadrature contact A |
| Encoder B | 7 | Quadrature contact B |
| Encoder click | 17 | Normally open push switch |
| Pololu 2535 LED data (optional) | 16 / TX | Through 5 V SN74AHCT125 and 330 Ω to first pixel DIN |

LCD VCC → 3V3 and GND → GND; use the factory four-wire SPI configuration. No MISO signal is needed. Connect BL to 3V3 for always-on backlight; no additional GPIO is allocated. The display is not touch-sensitive. The module uses its supplied GH1.25 eight-pin connector; follow the signal names on the module, rather than wire colors. Landscape orientation uses a 280×240 drawing area, MADCTL 0x70 (RGB), RGB565 pixels, inversion on, and column/row offsets (20, 0): controller columns 20–299 and rows 0–239. The driver runs SPI at 10 MHz and applies the landscape mapping after vendor initialization. The saved Enclosure variant selects Right (0° screen, original switch order) or Left (180° screen, mirrored switch order) through software stripe/window mapping; controller register settings remain the same. New configurations default to the preferred Left enclosure with the screen and ribbon on the left. For an existing saved setup choose Left, using Wi-Fi Settings → Enclosure variant or LCD EDIT CONFIG → ENCLOSURE. Verify physical viewing direction and red/blue color order on the actual module. Leave GPIO0 for the board's battery measurement and GPIO9 for BOOT. This proposal also avoids GPIO4/5/8/15 strapping functions and USB pins 12/13. Confirm GPIO2 and GPIO3 header locations against the board pinout; these are chip GPIO numbers.

## Rotary encoder

Add a passive incremental quadrature encoder with 20 detents per revolution and an independent momentary push switch. Confirm the selected part's pulses-per-revolution and detent phase relationship: 20 detents does not necessarily mean 20 complete quadrature cycles.

- Connect encoder common C to ground, A to GPIO6, and B to GPIO7.
- Connect one push-switch terminal to GPIO17 and the other to ground.
- Fit a 10 kΩ pull-up to 3V3 on each of A, B, and click. Add 1 kΩ series resistance between each contact node and its GPIO. Optionally fit 1 nF from each A/B GPIO to ground; use 100 nF at the click GPIO. Keep encoder wires short.
- Reserve GPIO6/7 for the encoder instead of external pin-based JTAG. Reserve GPIO17 instead of UART0 RX; do not attach a UART transmitter there. Use native USB for programming/debugging. Confirm header locations on the DFR1075 pinout.
- Use a bare contact encoder or a module explicitly compatible with 3.3 V; verify terminal identification from the selected encoder datasheet.

Validate one menu step per physical detent in both directions, including slow turns, quick turns, reversal, and rotation while clicking. The encoder operates independently of the footswitch ladder.

## Modular series-tap resistor ladder

Use the four-switch base plus 0–3 two-switch sections to its left, for 4/6/8/10 total. Keep the 10 kΩ pull-up, 20 kΩ idle resistor and 100 nF capacitor in the base only. Base taps T1/T2 are upper-left/upper-right, T3/T4 lower-left/lower-right. Each extension adds two 1 kΩ sections and passes **TAIL + GND** to the next: upper/lower T5/T6, then T7/T8, then T9/T10. Leave the last tail open. Software labels upper switches A–E and lower switches 1–5 from the right; menus follow physical left-to-right order, upper row first. Select Modular wiring and the installed total in setup. [Full wiring, BOM, numbering maps and voltage targets](resistor-ladders.md).

The following ten-switch schematic lists **electrical taps** T1–T10 in chain order; its SW labels are legacy linear numbers. Use the modular diagrams above for physical switch numbers. Resistor values and voltage targets are identical.

Use 1% metal-film resistors (0.1% optional) and normally open switches. Build this exact series-tap topology rather than ten independent parallel resistor branches:

```text
3V3 -- 10k -- SENSE -- 1k -- T1 -- 1k -- T2 -- ... -- 1k -- T10
               |            |           |                    |
              20k          SW1         SW2                  SW10
               |            |           |                    |
              GND          GND         GND                  GND

SENSE ---------------- GPIO1
SENSE -- 100nF -------- GND
```

There are ten 1 kΩ series sections: SENSE–T1 through T9–T10. No extra connection terminates T10. Each switch connects only its tap to ground. The permanent 20 kΩ resistor keeps the idle input below the ADC measurement ceiling. Place the 100 nF capacitor close to GPIO1. Start with 10 ms debounce and check the settling and noise on the assembled harness.

With switch n closed, the lower resistance is `(n × 1k) || 20k`. Ideal voltages at 3.300 V are:

| Switch | Series resistance to grounded tap | Sense voltage |
| --- | --- | --- |
| 1 | 1 kΩ | 0.287 V |
| 2 | 2 kΩ | 0.508 V |
| 3 | 3 kΩ | 0.683 V |
| 4 | 4 kΩ | 0.825 V |
| 5 | 5 kΩ | 0.943 V |
| 6 | 6 kΩ | 1.042 V |
| 7 | 7 kΩ | 1.127 V |
| 8 | 8 kΩ | 1.200 V |
| 9 | 9 kΩ | 1.264 V |
| 10 | 10 kΩ | 1.320 V |
| None | Open taps | 2.200 V |

These are calculated targets, not measured ADC thresholds. Capture each switch and idle during calibration; use narrow acceptance windows with guard bands, not a nearest-value classifier across the entire ADC range. The smallest nominal separation is about 56 mV. Verify separation with resistor tolerances, contact resistance, supply variation, BLE traffic, and LCD activity. Require measured noise/drift plus component uncertainty to remain comfortably within half the adjacent separation; otherwise revise the ladder before enclosure assembly.

Operation is one footswitch at a time. Simultaneous presses are outside the requirements, so no combination decoding is needed. Firmware waits for stable idle before accepting the next press.

## Two selectable pedal inputs

Each input supports a two-wire variable resistor or a three-wire potentiometer, independently selected. Proposed TRS convention: tip = signal, ring = reference, sleeve = ground. Verify actual pedal polarity; provide a tip/ring swap adapter where needed. Two-wire pedals connect signal to ground through their variable resistance. A TS plug may short ring to sleeve, so the reference output must tolerate that condition.

For each input:

1. Provide ring reference from 3V3 through 1 kΩ, limiting a ring-to-ground short to approximately 3.3 mA.
2. Connect tip through 1 kΩ to the signal sensing node; add a 100 nF capacitor and appropriately selected low-leakage ESD/clamp protection at this interface.
3. Feed the sensing node into one channel of a unity-gain-stable, rail-to-rail input/output buffer, provisionally MCP6002 powered at 3.3 V. One dual package handles both pedals; add 100 nF supply bypass.
4. Buffer output → 10 kΩ → ADC node → 20 kΩ → ground. Add 100 nF at the ADC node. This scales nominal 0–3.3 V to 0–2.2 V without loading the pedal with the scaling divider. Firmware reconstructs the buffer voltage as `Vsignal = 1.5 × Vadc`; calibrate actual gain and endpoint headroom.
5. Connect a selectable 10 kΩ pull-up from 3V3 to the tip side of the 1 kΩ input resistor. Switch it with a P-channel MOSFET: source to 3V3, drain to the 10 kΩ resistor, gate through 1 kΩ to the mode GPIO, and gate-to-source 100 kΩ. HIGH disables the pull-up (potentiometer mode); LOW enables it (resistor mode). Select a MOSFET specified for operation at −3.3 V gate drive and low leakage.

The pull-up is disconnected by default at reset. Change mode with the pedal unplugged, configure GPIO HIGH before enabling output, then restore the validated mode. Ring reference is current-limited but remains powered; it is not switched by the mode control.

In resistor mode the DC buffer input approximates the tip voltage. For pull-up `Rp = 10k`, use `Rpedal = Rp × Vsignal / (Vref − Vsignal)`. Account for leakage and reference tolerance; guard the denominator near open circuit. Normalize resistance against calibrated minimum and configured maximum (positive, at most 10 kΩ), then apply the response curve. Open circuit approaches 3.3 V before scaling, whereas a 10 kΩ pedal approaches 1.65 V.

In potentiometer mode the pull-up is disabled. Calibrate heel/toe voltages; ring series resistance reduces full-travel voltage depending on the pot resistance. Total resistance is metadata, not the ideal position scale. A floating wiper is not a reliable disconnect detector: add a switched jack contact if dependable unplug detection is required.

## ADC and prototype validation

Use calibrated ESP32-C6 ADC readings with attenuation selected for at least the 0–2.2 V operating span. Current ESP32-C6 datasheets specify an ATTEN3 calibrated range up to 3.3 V for qualifying chip date codes, with up to ±40 mV total error. The proposed 2.2 V ceiling retains headroom; per-switch calibration remains necessary because absolute ADC error can exceed half the smallest ladder gap. Reserve margin for reference and resistor tolerance; check the current ESP-IDF C6 ADC limits. Schedule ladder samples every 1–2 ms and each pedal initially at 200 samples/s. Measure multiplexer settling, noise, and endpoint error; tune filtering from observations. Protect external jacks against ESD and insertion transients within chip absolute maximum ratings.

Before building the harness, verify idle and all N installed ladder states, individual press/release detection, and all four combinations of pedal modes. Test with BLE and LCD active, USB and intended battery/power operation, and the longest intended pedal cables. Inspect the regulator rating for the actual DFR1075 revision. No external ADC or GPIO expander is included.

## Optional switch LEDs

The optional chain uses one [Pololu 2535 5 mm LED](https://www.pololu.com/product/2535) per switch, initially paired in switch-number order. Use **5 V, RGB byte order and the 2535 (800 kbit/s) profile**. The side-view lead order is DIN / +5 V / GND / DOUT, from the side opposite the flat toward the flat; follow the orientation diagram in the LED guide. GPIO16/TX is reserved for its hardware-timed data output; the firmware console remains on USB. Use a 5 V AHCT logic buffer, a 330 Ω data resistor, a regulated 5 V LED supply and common ground. Ten LEDs draw about 0.5 A at full white; a separate LED supply should allow at least 1 A plus controller headroom. When using the optional Pololu 4083 source, its 1 A rating is the total controller-plus-LED budget; follow the limitations in the [power guide](power.md). Add 470 µF at the chain entry and 100 nF per LED. Never power this part above 5 V. Chain output is disabled by default, with 64/255 brightness and white/yellow press/release colors. Pololu LEDs power up blue until a data command; firmware clears them at initialization and refreshes the chain every 250 ms. See [exact lead orientation, wiring and configuration](leds.md).

## Sources

- [DFRobot DFR1075 documentation](https://wiki.dfrobot.com/dfr1075/): board pinout, onboard battery sensing, SPI/GDI signal assignments, and revision details.
- [Waveshare 24382 product](https://www.waveshare.com/1.69inch-lcd-module.htm), [module wiki](https://www.waveshare.com/wiki/1.69inch_LCD_Module) and [mechanical drawing](https://files.waveshare.com/upload/4/41/1.69inch_LCD_Module_2Ddrawing.pdf): ST7789V2, interface configuration, wiring and PCB dimensions.
- [Espressif ESP32-C6 GPIO reference](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/peripherals/gpio.html): ADC channels and restricted pins.
- [ESP32-C6 datasheet](https://documentation.espressif.com/esp32-c6_datasheet_en.html): ADC ranges, calibration error and date-code qualifications.
- [Microchip MCP6002](https://www.microchip.com/en-us/product/MCP6002): proposed analog buffer; check electrical characteristics when finalizing the schematic.
