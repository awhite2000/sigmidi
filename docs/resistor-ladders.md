# SIGMIDI Foot Controller v0.1 — Modular resistor ladder: four-switch base + two-switch sections

The base has four footswitches. Add 0–3 sections on its **right** in the preferred Left enclosure, each holding one upper and one lower switch. Three sections are the six-switch extension. Installed totals are **4, 6, 8 or 10**. Upper switches use **A, B, C, D, E from left to right**. Lower switches use **1, 2, 3, 4, 5 from left to right**. Labels and electrical tap IDs both stay fixed when sections are added on the right.

| Installed switches | Two-switch sections | Upper row, from left | Lower row, from left |
|---:|---:|---|---|
| 4 | 0 | A, B | 1, 2 |
| 6 | 1 | A, B, C | 1, 2, 3 |
| 8 | 2 | A, B, C, D | 1, 2, 3, 4 |
| 10 | 3 | A, B, C, D, E | 1, 2, 3, 4, 5 |

The Right alternative reverses each physical row and adds sections on the left. Electrical tap IDs, resistor values, LED assignments and MIDI actions are identical. Right-reference drawings: [4](../design/ladders/modular-right-4.svg), [6](../design/ladders/modular-right-6.svg), [8](../design/ladders/modular-right-8.svg), [10](../design/ladders/modular-right-10.svg).

## Electrical wiring

```text
BASE — four switches, permanently wired
3V3 -- 10k -- SENSE -- 1k -- T1 -- 1k -- T2 -- 1k -- T3 -- 1k -- T4 -- TAIL OUT
               |            |           |           |           |
              20k        upper R     upper L      lower R     lower L
               |          switch      switch      switch      switch
              GND           |           |           |           |
                           GND         GND         GND         GND
SENSE -------- GPIO1 / ADC1_CH1
SENSE -- 100nF -- GND

EACH TWO-SWITCH EXTENSION — add on the physical right (preferred Left enclosure)
TAIL IN -- 1k -- UPPER TAP -- 1k -- LOWER TAP -- TAIL OUT
                    |                 |
               upper switch      lower switch
                    |                 |
GND IN ------------ GND ------------- GND -------- GND OUT
```

Use **two ladder conductors** across each section joint: **TAIL** and **GND**. Base T4 connects to the nearest extension's TAIL IN; its TAIL OUT feeds the next extension to the right. The nearest extension has T5/T6, the next T7/T8, and the farthest T9/T10. Each switch is normally open and connects its own tap to ground. The switches stay monostable; press and release MIDI lists remain independent.

Fit the 10 kΩ pull-up, 20 kΩ idle resistor and 100 nF capacitor **once, in the base**. Fit four 1 kΩ series resistors in the base and two more per extension, all 1% metal film (0.1% optional). Do not connect an extension tap directly to 3V3 or duplicate the idle resistor. Leave the final TAIL OUT insulated and open: no terminating resistor, short or jumper. The extension ground return must connect to the MCU ground. Adding an open-ended section does not change any existing tap's nominal voltage or calibration.

Power off before adding/removing sections, then select the installed total in setup. This ladder **does not auto-detect section count**. Never hot-plug the ladder while performing MIDI. Only one simultaneous switch needs to be decoded. Encoder and expression inputs retain their existing separate connections.

## Tap-to-label mapping

Entries below are **label:tap** pairs in physical left-to-right order. For example, switch C is always T5, B is T1, and A is T2. Lower switch 1 is always T4. New sections add C/3, D/4 and E/5 without renaming existing switches.

| Total | Sections | Upper row taps | Lower row taps | Smallest nominal voltage gap | Drawing |
|---:|---:|---|---|---:|---|
| 4 | 0 | A:T2, B:T1 | 1:T4, 2:T3 | 142.2 mV | [Wiring](../design/ladders/modular-4.svg) |
| 6 | 1 | A:T2, B:T1, C:T5 | 1:T4, 2:T3, 3:T6 | 99.2 mV | [Wiring](../design/ladders/modular-6.svg) |
| 8 | 2 | A:T2, B:T1, C:T5, D:T7 | 1:T4, 2:T3, 3:T6, 4:T8 | 73.2 mV | [Wiring](../design/ladders/modular-8.svg) |
| 10 | 3 | A:T2, B:T1, C:T5, D:T7, E:T9 | 1:T4, 2:T3, 3:T6, 4:T8, 5:T10 | 56.2 mV | [Wiring](../design/ladders/modular-10.svg) |

## Nominal voltages at 3.300 V

Idle is **2200 mV** for every size. With tap `t` grounded, `Rbottom = (t × 1 kΩ) || 20 kΩ`; `V = 3300 × Rbottom / (10000 + Rbottom)` mV. Voltage is determined by tap ID; letter and numeric labels do not change the resistor values.

| Tap | Fixed physical switch | Series to ground | Target |
|---|---|---:|---:|
| T1 | B — Base upper right | 1 kΩ | 287.0 mV |
| T2 | A — Base upper left | 2 kΩ | 507.7 mV |
| T3 | 2 — Base lower right | 3 kΩ | 682.8 mV |
| T4 | 1 — Base lower left | 4 kΩ | 825.0 mV |
| T5 | C — Extension 1 upper | 5 kΩ | 942.9 mV |
| T6 | 3 — Extension 1 lower | 6 kΩ | 1042.1 mV |
| T7 | D — Extension 2 upper | 7 kΩ | 1126.8 mV |
| T8 | 4 — Extension 2 lower | 8 kΩ | 1200.0 mV |
| T9 | E — Extension 3 upper | 9 kΩ | 1263.8 mV |
| T10 | 5 — Extension 3 lower | 10 kΩ | 1320.0 mV |

These are calculated targets, not measured thresholds. Capture idle and each installed switch after assembly with BLE and LCD active. Start at ±20 mV half-width and 10 ms debounce; verify noise, contact resistance, supply drift and resistor tolerance leave guard bands between every pair of measured windows. The smallest nominal gap is 142.2 mV at four switches and 56.2 mV at ten. Existing switches retain their calibrated centers after expansion; calibrate newly added taps before performance use.

## Software and compatibility

- **New configurations:** modular wiring, ten installed switches and the Left enclosure by default. Select 4 for the base alone, then 6/8/10 as sections are added.
- **Wi-Fi:** Settings → Ladder wiring → Modular, then Number of footswitches → 4/6/8/10 → Save & exit.
- **LCD:** EDIT CONFIG → LADDER → MODULAR, SWITCHES → installed total, then SAVE & EXIT. The count advances in pairs.
- The performance display, LCD switch menus, browser editor and calibration labels all use these stable letter/number labels. Lists follow physical order, upper row first, left to right. User-edited switch names remain separate and are retained. MIDI Test operates the selected physical switch's message list and LED.
- MIDI lists, custom names, calibration and LED assignments remain attached to **physical tap IDs** when the count changes. For example, the base upper-left switch is A and the upper-right switch is B at every size; the lower-left/right pair is 1/2. Their actions stay unchanged. New sections appear at the right; hidden sections keep their saved data.
- Configuration **version 4** adds `ladderLayout` (`1` modular, `0` linear). The ten `switches` entries are stored in fixed T1–T10 order; `ladder` stores idle followed by T1–T10, regardless of visible ordering. Keep all entries in JSON backups. The MIDI total limit still includes inactive entries.
- Version 1–3 backups migrate to version 4 in **linear** mode, retaining their existing switch count (v1 defaults to ten), LED assignments, messages and calibration. They are not silently reinterpreted as modular wiring. Switching an old setup to modular requires the wiring above; verify every switch and LED before saving. Versions 1/2 also receive disabled LEDs with 1:1 assignments as before.
- Linear mode remains available for the original tap-numbered ladders, including odd counts, from 4 to 10. [4](../design/ladders/ladder-4.svg), [5](../design/ladders/ladder-5.svg), [6](../design/ladders/ladder-6.svg), [7](../design/ladders/ladder-7.svg), [8](../design/ladders/ladder-8.svg), [9](../design/ladders/ladder-9.svg), [10](../design/ladders/ladder-10.svg).

## Optional LED chain

For matching physical identity, wire Pololu 2535 data in fixed tap order: base LEDs T1 → T2 → T3 → T4, then extension T5 → T6, then T7 → T8, then T9 → T10. Default LED assignments remain 1:1 with these taps; displayed switch labels are translated separately. Add +5V, GND and DATA for the LED chain in addition to the ladder tail; GND may share a suitably sized conductor. Connect LED DATA OUT to the next section DATA IN. Existing LED assignments need no changes when a section is added. Check total supply current using [LED wiring instructions](leds.md).

[All voltage targets and switch labels (CSV)](../design/ladders/voltage-targets.csv). Regenerate this document and the drawings with `python3 scripts/generate_ladder_variants.py`.
