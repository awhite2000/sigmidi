# SIGMIDI Foot Controller v0.1 — KiCad schematic

Open `sigmidi-foot-controller.kicad_pro` in KiCad 10, then open its schematic. The project is an editable, single-sheet A0 assembly schematic created through Konnect MCP 0.13.0 from the current [electrical netlist](../electrical/netlist.json) and connected wire diagram.

The schematic contains all 44 physical components, 39 named nets and 138 connected terminals. Its two `PWR_FLAG` markers describe the external supply to ERC; they are not additional physical components. Board internals are omitted.

## Physical pin order

- **DFRobot DFR1075:** top view with USB-C up. P2 has 18 pins on the left, P1 has 14 on the right and starts four pin pitches lower. Every printed pad label remains visible. Connected pads also show their GPIO/logical name and header identifier. Unused pads have no external signal callouts and are marked with no-connect crosses.
- **Waveshare 24382:** its external P2 connector retains physical order 1–8: BL, RST, D/C, CS, SCL/CLK, SDA/DIN, GND, VCC.
- **Pololu 2535:** side view with lens left, flat down and leads to the right. Leads run top-to-bottom DIN, 5V, GND, DOUT. All ten optional pixels use their function names as pin identifiers; no unverified numeric pin numbering is introduced.
- **ACJS-MHDC:** both pedal ports share one symbol. Terminals 10/11/12 are pedal 1 sleeve/ring/tip; 4/5/6 are pedal 2 sleeve/ring/tip. Normal contacts are unused; pad 13 is mechanical and unconnected.
- **Encoder:** A/B/C/SW1/SW2 are functional terminal names. Verify their physical arrangement against the selected encoder before assembly.

[Physical pin records](verification/physical-pin-map.json) and [placed-pin readback](verification/pin-locations.json) preserve the source mappings and measured schematic coordinates. No PCB footprints are assigned. The empty `.kicad_pcb` is the project placeholder created by Konnect, not a PCB layout.

## Editing and exports

`SIGMIDI.kicad_sym` contains project-local external module, dual socket, encoder and pixel symbols. The portable `sym-lib-table` resolves it through `${KIPRJMOD}`. Resistors, capacitors and footswitches use standard KiCad library symbols, embedded in the schematic.

Large physical pin labels, titles, references and values are ordinary schematic text annotations for readability. When moving a component, select its associated annotations and wires as well. The native symbol pin numbers, names and electrical types remain available for connectivity and editing. Small native pin labels remain alongside the larger annotations.

- [SVG preview](sigmidi-foot-controller.svg)
- [PNG preview](sigmidi-foot-controller.png)
- [PDF export](../../output/pdf/sigmidi-kicad-schematic.pdf)
- [KiCad XML netlist](sigmidi-foot-controller.net)

Crossings without a junction dot are not connected. The complete circuit uses actual wires; matching labels name nets rather than replacing connections.

## Verification

KiCad 10.0.7 ERC reports **0 errors and 0 warnings**, without suppressing rules. Konnect reports zero floating wire ends, unconnected component pins, shorted named nets, orphan items and symbol overlaps. All 46 placed symbols (44 components and two ERC markers) have resolved bounds. Annotation checking finds no duplicate or unassigned references.

The independent source comparison checks all 44 components, all 39 nets, every one of the 138 connected terminals, all 21 unused terminals, both DFRobot header sequences and their four-pitch offset, and the display pin sequence:

```bash
python3 scripts/verify_kicad_netlist.py
```

[Verification evidence](verification/checks.json) binds those results and the exports to their file hashes. The native PNG and the rendered one-page PDF were visually inspected. This is an assembly schematic; PCB fabrication, electrical bench qualification and exact unspecified encoder/socket mechanical pin layouts are outside this deliverable.
