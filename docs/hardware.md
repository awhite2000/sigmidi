# SIGMIDI Foot Controller v0.1 — Hardware and wiring

Target: DFRobot DFR1075 FireBeetle 2 ESP32-C6, using its internal ADC, and Waveshare 24382 1.69-inch ST7789V2 color LCD, used in landscape at 280×240. The harness requires bench validation; verify against the actual board revision before assembly. All logic and analog circuits use 3.3 V and common ground. Only one footswitch needs to be detected at a time.

## Alternate power input

Use a **9 V DC center-negative 2.1 × 5.5 mm barrel supply** through the Pololu S13V10F5 (Pololu 4083 / Kamami 1178565). Its regulated VOUT goes to the DFR1075 **5 V input (VIN/VCC)** and GND goes to **GND**. Raw 9 V connects only to the converter input. See [power wiring, source selection, budget and mounting](power.md). USB programming remains available through the board's existing power-selection circuit. No firmware/GPIO changes are required.

## Wi-Fi configuration access

Use the ESP32-C6 onboard Wi-Fi radio for the configuration editor. No additional module, wiring, or GPIO is required. Wi-Fi is enabled explicitly for setup and disabled when returning to performance mode; see the firmware specification for connection and save behavior.

## GPIO assignments

Use GPIO numbers in firmware, not Arduino D-label numbers. Do not connect a second display through the GDI connector: some signals below share its nets.

| Function | ESP32-C6 GPIO | Connection |
| --- | --- | --- |
| Switch ladder | 1 / ADC1_CH1 | Ladder sense node |
| Pedal 1 | 2 / ADC1_CH2 | Direct passive pedal 1 TIP |
| Pedal 2 | 3 / ADC1_CH3 | Direct passive pedal 2 TIP |
| LCD DIN | 22 | SPI MOSI |
| LCD CLK | 23 | SPI SCK |
| LCD CS | 18 | Active-low chip select |
| LCD DC | 19 | Data/command |
| LCD RST | 14 | Active-low reset |
| LCD BL | 3V3 | Always-on backlight |
| Pedal 1 mode | 20 | 10k bias: HIGH in resistor mode, high impedance otherwise |
| Pedal 2 mode | 21 | 10k bias: HIGH in resistor mode, high impedance otherwise |
| Encoder A | 6 | Quadrature contact A |
| Encoder B | 7 | Quadrature contact B |
| Encoder click | 17 | Normally open push switch |
| Pololu 2535 LED data (optional) | 16 / TX | Directly to first Pololu 2535 DIN |

LCD VCC → 3V3 and GND → GND; use the factory four-wire SPI configuration. No MISO signal is needed. Connect BL to 3V3 for always-on backlight; no additional GPIO is allocated. The display is not touch-sensitive. The module uses its supplied GH1.25 eight-pin connector; follow the signal names on the module, rather than wire colors. Landscape orientation uses a 280×240 drawing area, MADCTL 0x70 (RGB), RGB565 pixels, inversion on, and column/row offsets (20, 0): controller columns 20–299 and rows 0–239. The driver runs SPI at 10 MHz and applies the landscape mapping after vendor initialization. The saved Enclosure variant selects Right (0° screen, Right switch order) or Left (180° screen, mirrored switch order) through software stripe/window mapping; controller register settings remain the same. New configurations default to the preferred Left enclosure with the screen and ribbon on the left. For an existing saved setup choose Left, using Wi-Fi Settings → Enclosure variant or LCD EDIT CONFIG → ENCLOSURE. Verify physical viewing direction and red/blue color order on the actual module. Leave GPIO0 for the board's battery measurement and GPIO9 for BOOT. The assignment avoids GPIO4/5/8/15 strapping functions and USB pins 12/13. Confirm GPIO2 and GPIO3 header locations against the board pinout; these are chip GPIO numbers.

## Rotary encoder

Add a passive incremental quadrature encoder with 20 detents per revolution and an independent momentary push switch. Confirm the selected part's pulses-per-revolution and detent phase relationship: 20 detents does not necessarily mean 20 complete quadrature cycles.

- Connect encoder common C to GND, A directly to D12 / GPIO6 (P1:12), and B directly to D11 / GPIO7 (P1:13).
- Connect one push-switch terminal directly to RX / GPIO17 (P2:18) and the other to GND.
- No external resistors or capacitors are required. Firmware enables the GPIO internal pull-ups for A, B and click, decodes quadrature transitions and debounces the click in software. Keep encoder wires short.
- Use GPIO6/7 for encoder input; external pin-based JTAG is unavailable. Use GPIO17 for the encoder click; UART0 RX is unavailable; do not attach a UART transmitter there. Use native USB for programming/debugging. Confirm header locations on the DFR1075 pinout.
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
| TIP directly to ADC | A1 / GPIO2 (P1:9) | A2 / GPIO3 (P1:8) |
| RING reference | 3V3 through 5.1 kΩ | 3V3 through 5.1 kΩ |
| SLEEVE | GND | GND |
| 10 kΩ from bias pin to TIP | SCL / GPIO20 (P1:4) | MISO / GPIO21 (P2:8) |

Use 1% resistors. A 5.1 kΩ ring resistor limits a ring-to-ground short to about 0.65 mA at 3.3 V. It also limits a 10 kΩ potentiometer's nominal full-travel voltage to `3300 × 10000 / (5100 + 10000) = 2185 mV`; lower-resistance pots have a lower full-travel voltage. TIP is measured directly without a gain correction. A 10 kΩ pot's maximum source impedance is approximately 3.78 kΩ; validate acquisition settling and noise on the actual harness.

For an enabled **two-wire variable resistor**, firmware drives the bias pin HIGH through its 10 kΩ resistor. The external resistance connects TIP to SLEEVE. Use `Rpedal = 10000 × Vtip / (3300 - Vtip)` with nominal millivolts, then normalize against the configured maximum resistance (positive, at most 10 kΩ). A 10 kΩ resistor gives nominal 1650 mV. The GPIO HIGH voltage and resistor tolerance affect resistance accuracy. Open circuit approaches the 3.3 V supply; firmware guards the denominator near that value. A TS plug may ground RING safely through the 5.1 kΩ reference resistor.

For a **three-wire potentiometer**, connect the outer legs to RING and SLEEVE and the wiper to TIP. Firmware leaves the bias GPIO at high impedance with both internal pulls disabled. Capture the actual heel and toe voltages before use; these endpoints set the position scale independently of pot resistance. A floating wiper is not a dependable unplug detector. The external pedal contains only the resistor or potentiometer, without any powered electronics.

Boot and disabled-input states also leave the bias GPIO at high impedance. The firmware preloads HIGH before enabling its output and never drives the bias LOW. Change mode with the pedal unplugged. This wiring requires the passive-input firmware; the earlier active-interface firmware drives the bias incorrectly and applies an incompatible 1.5× conversion. Repeat pedal endpoint calibration after rewiring; switch actions, ladder calibration and LED identities remain unchanged. Internal weak pull-ups are not used as precision resistance references.

## ADC and prototype validation

Use calibrated ESP32-C6 ADC readings with attenuation selected for at least the connected-pedal 0–2.2 V operating span. Current ESP32-C6 datasheets specify an ATTEN3 calibrated range up to 3.3 V for qualifying chip date codes, with up to ±40 mV total error. The 2.2 V ceiling retains headroom; per-switch calibration remains necessary because absolute ADC error can exceed half the smallest ladder gap. Reserve margin for reference and resistor tolerance; check the current ESP-IDF C6 ADC limits. Schedule ladder samples every 1–2 ms and each pedal initially at 200 samples/s. Measure multiplexer settling, noise, and endpoint error; tune filtering from observations. Connect only unpowered passive pedals. This minimal two-resistor interface adds no external ESD protection; its noise and transient performance must be checked on hardware.

Before building the harness, verify idle and all N installed ladder states, individual press/release detection, and all four combinations of pedal modes. Test with BLE and LCD active, USB and intended battery/power operation, and the longest intended pedal cables. Inspect the regulator rating for the actual DFR1075 revision. No external ADC or GPIO expander is included.

## Optional switch LEDs

The optional chain uses one [Pololu 2535 5 mm LED](https://www.pololu.com/product/2535) per switch, initially paired in switch-number order. Use **5 V, RGB byte order and the 2535 (800 kbit/s) profile**. The side-view lead order is DIN / +5 V / GND / DOUT, from the side opposite the flat toward the flat; follow the orientation diagram in the LED guide. GPIO16/TX is reserved for its hardware-timed data output; the firmware console remains on USB. Connect GPIO16 directly to the first DIN, each DOUT to the next DIN, and every LED to the regulated 5 V supply and common ground. The chain contains only LEDs and wires. Ten LEDs draw about 0.5 A at full white; a separate LED supply should allow at least 1 A plus controller headroom. When using the optional Pololu 4083 source, its 1 A rating is the total controller-plus-LED budget; follow the limitations in the [power guide](power.md). Never power this part above 5 V. Chain output is disabled by default, with 64/255 brightness and white/yellow press/release colors. Pololu LEDs power up blue until a data command; firmware clears them at initialization and refreshes the chain every 250 ms. See [exact lead orientation, wiring and configuration](leds.md).

## Sources

- [DFRobot DFR1075 documentation](https://wiki.dfrobot.com/dfr1075/): board pinout, onboard battery sensing, SPI/GDI signal assignments, and revision details.
- [Waveshare 24382 product](https://www.waveshare.com/1.69inch-lcd-module.htm), [module wiki](https://www.waveshare.com/wiki/1.69inch_LCD_Module) and [mechanical drawing](https://files.waveshare.com/upload/4/41/1.69inch_LCD_Module_2Ddrawing.pdf): ST7789V2, interface configuration, wiring and PCB dimensions.
- [Espressif ESP32-C6 GPIO reference](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c6/api-reference/peripherals/gpio.html): ADC channels and restricted pins.
- [ESP32-C6 datasheet](https://documentation.espressif.com/esp32-c6_datasheet_en.html): ADC ranges, calibration error and date-code qualifications.
