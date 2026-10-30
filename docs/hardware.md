# SIGMIDI Foot Controller v0.1 — Hardware and wiring

Target: Arduino Nano ESP32 (ABX00083, ESP32-S3), using its internal ADC, and Waveshare 24382 1.69-inch ST7789V2 color LCD, used in landscape at 280×240. The harness requires bench validation; verify against the actual board revision before assembly. All logic and analog circuits use 3.3 V and common ground. Only one footswitch needs to be detected at a time.

## Alternate power input

Use a **9 V DC center-negative 2.1 × 5.5 mm barrel supply**. The positive sleeve feeds **Nano VIN** and Pololu VIN; the negative centre feeds common GND. The Pololu S13V10F5 (4083 / Kamami 1178565) supplies regulated **5 V to the optional LEDs**, not Nano VIN. Nano VIN requires 6–21 V. USB can power the Nano independently; do not tie external 5 V to USB VBUS. See [power wiring](power.md). The Nano has no LiPo charging circuit.

## Wi-Fi configuration access

Use the Nano ESP32 onboard Wi-Fi radio for the configuration editor. No additional module, wiring, or GPIO is required. Wi-Fi is enabled explicitly for setup and disabled when returning to performance mode; see the firmware specification for connection and save behavior.

## GPIO assignments

The firmware uses **ESP32 GPIO numbers**, independently of Arduino IDE pin-numbering preferences. The Nano's board labels and corresponding GPIOs are:

| Function | Nano label | ESP32-S3 GPIO | Connection |
|---|---|---:|---|
| Switch ladder | A0 | 1 / ADC1_CH0 | Ladder sense |
| Pedal 1 | A1 | 2 / ADC1_CH1 | Direct TIP |
| Pedal 2 | A3 | 4 / ADC1_CH3 | Direct TIP |
| Pedal 1 bias | D2 | 5 | 10 kΩ to pedal 1 TIP |
| Pedal 2 bias | D3 | 6 | 10 kΩ to pedal 2 TIP |
| Encoder A | D4 | 7 | Contact A |
| Encoder B | D5 | 8 | Contact B |
| Encoder click | D6 | 9 | Contact to GND |
| Optional LED DIN | D7 | 10 | Direct to first Pololu 2535 DIN |
| LCD CLK | D8 | 17 | SPI clock (routed through GPIO matrix) |
| LCD DC | D9 | 18 | Data/command |
| LCD CS | D10 | 21 | Active-low select |
| LCD DIN | D11 | 38 | SPI MOSI |
| LCD RST | D12 | 47 | Active-low reset |
| USB VBUS sense | A4 | 11 | 100 kΩ / 150 kΩ divider below |
| LCD VCC and BL | 3V3 | — | Always-on backlight |
| All grounds | GND | — | Common return |

The display's eight-pin connector stays in physical order **BL, RST, D/C, CS, SCL/CLK, SDA/DIN, GND, VCC**. Connect to the signals above. The Nano's D13/default SPI-clock pin is deliberately unused because it also drives the onboard LED. GPIO19/20 are exclusively USB D−/D+ inside the USB-C connection. Avoid GPIO0/3/45/46 strapping pins and leave unused Nano pins disconnected. The three analog inputs all use ADC1, including during Wi-Fi operation. Pin constants and uniqueness checks are in `src/board.hpp`.

The electrical diagrams show the component-side Nano top view with USB-C up: JP1 left, pads 1–15 downward; JP2 right, pads 15–1 downward. These are the official schematic pad IDs. Board labels and GPIO names are both retained. The physical installation is component-side up on four integral base posts, with USB-C to the rear. Rotate the reference to match the chassis when identifying pads.

### USB VBUS detection

Install these **two resistors even if you initially use only BLE**:

```text
Nano VBUS (USB 5 V) --- R50 100 kΩ ---+--- A4 / GPIO11
                                      |
                                  R51 150 kΩ
                                      |
                                     GND
```

Use 1% resistors. The divider gives about 3.0 V with a 5 V USB supply and discharges the sense input when unplugged. Never connect 5 V directly to GPIO11. This monitors host VBUS while the controller remains powered through VIN; it does not supply power or join external 5 V to USB. Native USB MIDI uses the existing USB-C connector and needs no external USB adapter.

LCD VCC → 3V3 and GND → GND; use the factory four-wire SPI configuration. No MISO signal is needed. Connect BL to 3V3 for always-on backlight; no additional GPIO is allocated. The display is not touch-sensitive. The module uses its supplied GH1.25 eight-pin connector; follow the signal names on the module, rather than wire colors. Landscape orientation uses a 280×240 drawing area, MADCTL 0x70 (RGB), RGB565 pixels, inversion on, and column/row offsets (20, 0): controller columns 20–299 and rows 0–239. The driver runs SPI at 10 MHz and applies the landscape mapping after vendor initialization. The saved Enclosure variant selects Right (0° screen, Right switch order) or Left (180° screen, mirrored switch order) through software stripe/window mapping; controller register settings remain the same. New configurations default to the preferred Left enclosure with the screen and ribbon on the left. For an existing saved setup choose Left, using Wi-Fi Settings → Enclosure variant or LCD EDIT CONFIG → ENCLOSURE. Verify physical viewing direction and red/blue color order on the actual module. The pin assignment reserves native USB and boot straps.

## Rotary encoder

Add a passive incremental quadrature encoder with 20 detents per revolution and an independent momentary push switch. Confirm the selected part's pulses-per-revolution and detent phase relationship: 20 detents does not necessarily mean 20 complete quadrature cycles.

- Connect encoder common C to GND, A directly to D4 / GPIO7, and B directly to D5 / GPIO8.
- Connect one push-switch terminal directly to D6 / GPIO9 and the other to GND.
- No external resistors or capacitors are required. Firmware enables the GPIO internal pull-ups for A, B and click, decodes quadrature transitions and debounces the click in software. Keep encoder wires short.

- Use a bare contact encoder or a module explicitly compatible with 3.3 V; verify terminal identification from the selected encoder datasheet.

Validate one menu step per physical detent in both directions, including slow turns, quick turns, reversal, and rotation while clicking. The encoder operates independently of the footswitch ladder.

## Modular series-tap resistor ladder

Use a four-switch base plus 0–3 two-switch extensions for 4/6/8/10 total. Extensions go to the right in the preferred Left enclosure and to the left in Right. Keep the 10 kΩ pull-up, 20 kΩ idle resistor and 100 nF capacitor in the electronics base. Each extension adds two 1 kΩ series sections and carries TAIL and GND onward.

Tap identity is fixed: A=T2, B=T1, 1=T4, 2=T3; extensions add C/3=T5/T6, D/4=T7/T8 and E/5=T9/T10. Select Modular wiring and the installed count. [Wiring, resistor values, labels and voltage targets](resistor-ladders.md).

The schematic below shows electrical tap order, independently of physical row order. Each SWn connects tap Tn to ground.

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

Each input supports a two-wire variable resistor or a three-wire potentiometer, independently selected. TRS wiring: tip = signal, ring = reference, sleeve = ground. Verify actual pedal polarity; provide a tip/ring swap adapter where needed. Two-wire pedals connect signal to ground through their variable resistance. A TS plug may short ring to sleeve, so the reference output must tolerate that condition.

Each input needs **only two resistors inside the controller**, with no op-amp, MOSFET, clamp circuit, divider or external filter capacitor:

| Connection | Pedal 1 | Pedal 2 |
| --- | --- | --- |
| TIP directly to ADC | A1 / GPIO2 | A3 / GPIO4 |
| RING reference | 3V3 through 5.1 kΩ | 3V3 through 5.1 kΩ |
| SLEEVE | GND | GND |
| 10 kΩ from bias pin to TIP | D2 / GPIO5 | D3 / GPIO6 |

Use 1% resistors. A 5.1 kΩ ring resistor limits a ring-to-ground short to about 0.65 mA at 3.3 V. It also limits a 10 kΩ potentiometer's nominal full-travel voltage to `3300 × 10000 / (5100 + 10000) = 2185 mV`; lower-resistance pots have a lower full-travel voltage. TIP is measured directly without a gain correction. A 10 kΩ pot's maximum source impedance is approximately 3.78 kΩ; validate acquisition settling and noise on the actual harness.

For an enabled **two-wire variable resistor**, firmware drives the bias pin HIGH through its 10 kΩ resistor. The external resistance connects TIP to SLEEVE. Use `Rpedal = 10000 × Vtip / (3300 - Vtip)` with nominal millivolts, then normalize against the configured maximum resistance (positive, at most 10 kΩ). A 10 kΩ resistor gives nominal 1650 mV. The GPIO HIGH voltage and resistor tolerance affect resistance accuracy. Open circuit approaches the 3.3 V supply; firmware guards the denominator near that value. A TS plug may ground RING safely through the 5.1 kΩ reference resistor.

For a **three-wire potentiometer**, connect the outer legs to RING and SLEEVE and the wiper to TIP. Firmware leaves the bias GPIO at high impedance with both internal pulls disabled. Capture the actual heel and toe voltages before use; these endpoints set the position scale independently of pot resistance. A floating wiper is not a dependable unplug detector. The external pedal contains only the resistor or potentiometer, without any powered electronics.

Boot and disabled-input states also leave the bias GPIO at high impedance. The firmware preloads HIGH before enabling its output and never drives the bias LOW. Change mode with the pedal unplugged and repeat endpoint calibration after rewiring. ADC voltages are used directly without a gain multiplier. Internal weak pull-ups are not used as precision resistance references.

## ADC and prototype validation

Use calibrated ESP32-S3 ADC1 readings at 12 dB attenuation, 12-bit resolution and the ESP-IDF curve-fitting scheme, with one calibration handle per input. Connected pedals and idle ladder remain within the nominal 0–2.2 V design span. Calibrate actual switch centres and pedal endpoints on the installed Nano. Absolute ADC error, acquisition settling and noise still require bench checks. Ladder scans run about every 1 ms; pedal sampling starts at 200 samples/s. Connect only unpowered passive pedals. The two-resistor pedal interface adds no external ESD protection.

Before building the harness, verify idle and all N installed ladder states, individual press/release detection, and all four combinations of pedal modes. Test with BLE and LCD active, USB and 9 V power operation, and the longest intended pedal cables. Check the Nano and LED supply budgets. No external ADC or GPIO expander is included.

## Optional switch LEDs

The optional chain uses one [Pololu 2535 5 mm LED](https://www.pololu.com/product/2535) per switch, initially paired in switch-number order. Use **5 V, RGB byte order and the 2535 (800 kbit/s) profile**. The side-view lead order is DIN / +5 V / GND / DOUT, from the side opposite the flat toward the flat; follow the orientation diagram in the LED guide. D7 / GPIO10 is reserved for its hardware-timed data output. The application exposes USB MIDI rather than a serial console. Connect GPIO10 directly to the first DIN, each DOUT to the next DIN, and every LED to the regulated 5 V supply and common ground. The chain contains only LEDs and wires. Ten LEDs draw about 0.5 A at full white; a separate LED supply should allow at least 1 A plus controller headroom. When using the optional Pololu 4083 source, its 1 A rating is the total controller-plus-LED budget; follow the limitations in the [power guide](power.md). Never power this part above 5 V. Chain output is disabled by default, with 64/255 brightness and white/yellow press/release colors. Pololu LEDs power up blue until a data command; firmware clears them at initialization and refreshes the chain every 250 ms. See [exact lead orientation, wiring and configuration](leds.md).

## Sources

- [Arduino Nano ESP32 documentation](https://docs.arduino.cc/hardware/nano-esp32/) and [physical pinout](https://docs.arduino.cc/resources/pinouts/ABX00083-full-pinout.pdf).
- [Espressif USB device stack](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html): native USB and self-powered VBUS detection.
- [Waveshare 24382 module wiki](https://www.waveshare.com/wiki/1.69inch_LCD_Module): ST7789V2, interface configuration and physical connector.

The [electrical diagrams](../design/electrical/README.md) and [KiCad schematic](../design/kicad/README.md) use this Nano GPIO/power map and preserve physical pin order. The enclosure uses the [direct Nano base mounts](../design/fusion/nano-esp32/README.md).
