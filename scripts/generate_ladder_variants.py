#!/usr/bin/env python3
"""Generate wiring drawings and nominal ADC targets for legacy and chainable modular series-tap ladders."""
from pathlib import Path
from firmware_artifacts import project_version
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design' / 'ladders'


def millivolts(tap):
    # Independent closed-form divider: (tap * 1k) in parallel with 20k, below 10k.
    return 2200.0 if tap == 0 else 6600.0 * tap / (20 + 3 * tap)


def tap_for_number(count, number, left=False):
    if left:
        row_size = count // 2
        number = row_size + 1 - number if number <= row_size else count + row_size + 1 - number
    extensions = (count - 4) // 2
    row_size = count // 2
    lower = number > row_size
    column = (number - 1) % row_size
    return (5 + 2 * (extensions - 1 - column) + int(lower) if column < extensions
            else column - extensions + 1 + (2 if lower else 0))


def label_for_tap(tap):
    if tap <= 4:
        return ['B', 'A', '2', '1'][tap-1]
    return chr(ord('C') + (tap-5)//2) if tap % 2 else str(3 + (tap-6)//2)


def drawing(count, modular=False, left=True):
    width = 390 + 85 * count
    nodes = [350 + 85 * i for i in range(1, count + 1)]
    numbers = {tap_for_number(count, n): label_for_tap(tap_for_number(count, n)) for n in range(1, count + 1)} if modular else {n: n for n in range(1, count + 1)}
    height = 510 if modular else 340
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;font-size:15px;fill:#172b3b}path,line,rect.res{fill:none;stroke:#172b3b;stroke-width:2}.node{fill:#172b3b}</style>',
         f'<text x="24" y="30" style="font-size:22px">SIGMIDI v{project_version(ROOT)} · {count}-switch {"modular " if modular else "linear "}ladder</text>',
         '<text x="24" y="58">10 kΩ pull-up + 20 kΩ idle resistor + one 1 kΩ section per switch (1%)</text>',
         '<text x="24" y="115">3V3</text><path d="M65 110H105 M165 110H350"/>',
         '<rect class="res" x="105" y="101" width="60" height="18"/><text x="110" y="90">10 kΩ</text>',
         '<circle class="node" cx="220" cy="110" r="4"/>',
         '<path d="M220 110V155 M220 200V248 M208 248H232 M212 254H228 M216 260H224"/>',
         '<rect class="res" x="211" y="155" width="18" height="45"/><text x="238" y="211">20 kΩ</text>',
         '<path d="M290 110V155 M290 178V248 M278 248H302 M282 254H298 M286 260H294 M278 155H302 M278 178H302"/>',
         '<circle class="node" cx="290" cy="110" r="4"/><text x="303" y="174">100 nF</text>',
         '<path d="M185 110V280H26"/><circle class="node" cx="185" cy="110" r="4"/>',
         f'<text x="24" y="{315 if modular else 304}">SENSE → GPIO1; capacitor close to MCU. All ground symbols connect together.</text>']
    last = 350
    for i, x in enumerate(nodes, 1):
        s += [f'<path d="M{last} 110H{last+12} M{last+62} 110H{x}"/>',
              f'<rect class="res" x="{last+12}" y="102" width="50" height="16"/><text x="{last+17}" y="91">1 kΩ</text>',
              f'<circle class="node" cx="{x}" cy="110" r="4"/><text x="{x-12}" y="141">T{i}</text>',
              f'<path d="M{x} 110V160 M{x} 190V248 M{x-12} 248H{x+12} M{x-8} 254H{x+8} M{x-4} 260H{x+4} M{x} 190L{x+13} 165"/>',
              f'<text x="{x-17}" y="218">SW{numbers[i]}</text>']
        last = x
    s += [f'<text x="24" y="{340 if modular else 329}">Normally open switches; one press at a time. Final tap is un-terminated. Calibrate all installed switches and idle.</text>']
    if modular:
        for start, end, label in [(1, 4, 'BASE · four switches')] + [(i, i+1, f'EXT {(i-3)//2} · two switches') for i in range(5, count+1, 2)]:
            x0, x1 = nodes[start-1]-38, nodes[end-1]+38
            s += [f'<path d="M{x0} 264V270H{x1}V264"/><text x="{x0}" y="290">{label}</text>']
        s += [f'<text x="24" y="366" style="font-size:19px">Physical layout · {"Left (preferred): A / 1 start at the left" if left else "Right: A / 1 start at the right"}</text>']
        row_size = count//2
        for number in range(1, count+1):
            tap = tap_for_number(count, number, left=left)
            x = 100 + 130*((number-1)%row_size)
            y = 400 if number <= row_size else 460
            label = 'Base' if tap <= 4 else f'Ext {(tap-3)//2}'
            s += [f'<text x="{x}" y="{y}" style="font-size:20px">SW{label_for_tap(tap)} · T{tap}</text><text x="{x}" y="{y+20}">{label}</text>']
        s += ['<text x="24" y="505">At each extension: TAIL and GND only. Add 2 × 1 kΩ; no new pull-up, idle resistor or end termination.</text>']
    s += ['</svg>']
    return '\n'.join(s)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for count in range(4, 11):
        (OUT / f'ladder-{count}.svg').write_text(drawing(count))
    for count in [4, 6, 8, 10]:
        (OUT / f'modular-{count}.svg').write_text(drawing(count, modular=True))
        (OUT / f'modular-right-{count}.svg').write_text(drawing(count, modular=True, left=False))
    with (OUT / 'voltage-targets.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['layout', 'switch_count', 'tap', 'displayed_switch', 'series_ohms', 'nominal_mV_at_3V3'])
        for layout, counts in [('linear', range(4, 11)), ('modular', [4, 6, 8, 10])]:
            for count in counts:
                numbers = {tap_for_number(count, n): label_for_tap(tap_for_number(count, n)) for n in range(1, count+1)} if layout == 'modular' else {n:n for n in range(1, count+1)}
                for tap in range(count+1):
                    writer.writerow([layout, count, tap, numbers[tap] if tap else 'idle', tap*1000 if tap else '', f'{millivolts(tap):.3f}'])
    rows = []
    for n in [4, 6, 8, 10]:
        order = [tap_for_number(n, i, left=True) for i in range(1, n+1)]
        gap = min(abs(millivolts(a)-millivolts(b)) for a in range(n+1) for b in range(a+1, n+1))
        rows.append(f'| {n} | {(n-4)//2} | ' + ', '.join(f'{label_for_tap(t)}:T{t}' for t in order[:n//2]) + ' | ' + ', '.join(f'{label_for_tap(t)}:T{t}' for t in order[n//2:]) + f' | {gap:.1f} mV | [Wiring](../design/ladders/modular-{n}.svg) |')
    targets=[]
    names=['Base upper right','Base upper left','Base lower right','Base lower left'] + [f'Extension {i} {row}' for i in range(1,4) for row in ['upper','lower']]
    for tap in range(1,11):
        targets.append(f'| T{tap} | {label_for_tap(tap)} — {names[tap-1]} | {tap} kΩ | {millivolts(tap):.1f} mV |')
    text = """# SIGMIDI Foot Controller v0.1 — Modular resistor ladder: four-switch base + two-switch sections

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

Power off before adding/removing sections, then select the installed total in setup. This ladder **does not auto-detect section count**. Never hot-plug the ladder while performing MIDI. Only one simultaneous switch needs to be decoded. Encoder and expression inputs have separate connections.

## Tap-to-label mapping

Entries below are **label:tap** pairs in physical left-to-right order. For example, switch C is always T5, B is T1, and A is T2. Lower switch 1 is always T4. New sections add C/3, D/4 and E/5 without renaming existing switches.

| Total | Sections | Upper row taps | Lower row taps | Smallest nominal voltage gap | Drawing |
|---:|---:|---|---|---:|---|
""" + '\n'.join(rows) + """

## Nominal voltages at 3.300 V

Idle is **2200 mV** for every size. With tap `t` grounded, `Rbottom = (t × 1 kΩ) || 20 kΩ`; `V = 3300 × Rbottom / (10000 + Rbottom)` mV. Voltage is determined by tap ID; letter and numeric labels do not change the resistor values.

| Tap | Fixed physical switch | Series to ground | Target |
|---|---|---:|---:|
""" + '\n'.join(targets) + """

These are calculated targets, not measured thresholds. Capture idle and each installed switch after assembly with BLE and LCD active. Start at ±20 mV half-width and 10 ms debounce; verify noise, contact resistance, supply drift and resistor tolerance leave guard bands between every pair of measured windows. The smallest nominal gap is 142.2 mV at four switches and 56.2 mV at ten. Existing switches retain their calibrated centers after expansion; calibrate newly added taps before performance use.

## Software settings

- **New configurations:** modular wiring, ten installed switches and the Left enclosure by default. Select 4 for the base alone, then 6/8/10 as sections are added.
- **Wi-Fi:** Settings → Ladder wiring → Modular, then Number of footswitches → 4/6/8/10 → Save & exit.
- **LCD:** EDIT CONFIG → LADDER → MODULAR, SWITCHES → installed total, then SAVE & EXIT. The count advances in pairs.
- The performance display, LCD switch menus, browser editor and calibration labels all use these stable letter/number labels. Lists follow physical order, upper row first, left to right. User-edited switch names remain separate and are retained. MIDI Test operates the selected physical switch's message list and LED.
- MIDI lists, custom names, calibration and LED assignments remain attached to **physical tap IDs** when the count changes. For example, the base upper-left switch is A and the upper-right switch is B at every size; the lower-left/right pair is 1/2. Their actions stay unchanged. New sections appear at the right; hidden sections keep their saved data.
- Configuration schema **4** uses `ladderLayout` (`1` modular, `0` linear). The ten `switches` entries are stored in fixed T1–T10 order; `ladder` stores idle followed by T1–T10, regardless of visible ordering. Keep all entries in JSON backups. The MIDI total limit still includes inactive entries.
- Linear mode supports tap-numbered ladders, including odd counts, from 4 to 10. [4](../design/ladders/ladder-4.svg), [5](../design/ladders/ladder-5.svg), [6](../design/ladders/ladder-6.svg), [7](../design/ladders/ladder-7.svg), [8](../design/ladders/ladder-8.svg), [9](../design/ladders/ladder-9.svg), [10](../design/ladders/ladder-10.svg).

## Optional LED chain

For matching physical identity, wire Pololu 2535 data in fixed tap order: base LEDs T1 → T2 → T3 → T4, then extension T5 → T6, then T7 → T8, then T9 → T10. Default LED assignments are 1:1 with these taps; displayed switch labels are translated separately. Add +5V, GND and DATA for the LED chain in addition to the ladder tail; GND may share a suitably sized conductor. Connect LED DATA OUT to the next section DATA IN. Existing LED assignments need no changes when a section is added. Check total supply current using [LED wiring instructions](leds.md).

[All voltage targets and switch labels (CSV)](../design/ladders/voltage-targets.csv). Regenerate this document and the drawings with `python3 scripts/generate_ladder_variants.py`.
"""
    (ROOT / 'docs' / 'resistor-ladders.md').write_text(text)
    print(f'Generated four modular and seven linear ladder variants in {OUT}')


if __name__ == '__main__':
    main()
