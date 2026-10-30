# SIGMIDI Foot Controller v0.1 — KiCad schematic

`sigmidi-foot-controller.kicad_pro` is an editable KiCad 10 assembly project. The single A0 landscape sheet contains **46 physical components, 41 named nets and 143 connected terminals**. Two additional PWR_FLAG symbols declare externally supplied power; they are not purchased parts. All connections use continuous wires. Net labels name those wires, and dots identify junctions. Purchased boards stop at their external pins.

- [Browser preview](../../previews/kicad-schematic.html)
- [Vector schematic](sigmidi-foot-controller.svg) and [PDF](../../output/pdf/sigmidi-kicad-schematic.pdf)
- [Electrical drawing and connection schedule](../electrical/README.md)
- `SIGMIDI.kicad_sym` and the project-relative `sym-lib-table` provide the custom external-module symbols.

## Physical pin references

U1 is Arduino Nano ESP32 ABX00083, component-side top view with USB-C up. Its **JP1 is on the left, pads 1–15 top to bottom; JP2 is on the right, pads 15–1 top to bottom**. Pad IDs come from Arduino schematic V0.3; physical positions and D/A labels come from its official top-view pinout. The datasheet's functional-table row numbering is not used as JP2 pad numbering. VBUS is named VUSB in the pinout, and RST is RESET. Every printed header label remains visible, including unused pins; connected pins also show the ESP32 GPIO. The firmware uses GPIO numbers independently of Arduino's pin-numbering preference.

The Waveshare 24382 external P2 connector retains **1 BL, 2 RST, 3 D/C, 4 CS, 5 SCL/CLK, 6 SDA/DIN, 7 GND, 8 VCC**. SCL/SDA are SPI signals. The display's internal FPC and circuitry are omitted.

Pololu 2535 LEDs use the actual package lead order: lens left, leads right, flat side down; top to bottom DIN, 5V, GND, DOUT. DIN/DOUT/+5V/GND are functional terminal identifiers, not invented package pad numbers. LED1 receives D7/GPIO10 directly; there are no added LED-chain parts. The final DOUT is marked NC.

J2 is ACJS-MHDC: manufacturer TOP is pedal 1 (10 sleeve, 11 ring, 12 tip); BOTTOM is pedal 2 (4 sleeve, 5 ring, 6 tip). Normal contacts are NC and pad 13 is mechanical. SW11 uses functional A/B/C/SW1/SW2 names; confirm the selected encoder terminal layout before soldering. The passive encoder uses internal GPIO pull-ups without external R/C.

Nano VIN receives the barrel sleeve's +9V. The Pololu converter's 5V output powers optional LEDs only. USB VBUS stays separate and feeds R50 100k / R51 150k, with their junction at A4/GPIO11. ADC inputs are A0/GPIO1, A1/GPIO2 and A3/GPIO4; pedal bias outputs are D2/GPIO5 and D3/GPIO6.

## Validation and scope

The saved schematic is checked through Konnect and direct KiCad ERC/XML exports. `verification/checks.json` records the latest findings, tool versions and source/output hashes. `verification/pin-locations.json` records queried symbol coordinates. `verification/physical-pin-map.json` ties accepted terminal IDs and labels to those positions. Run `scripts/verify_kicad_netlist.py` to compare every exported net against the electrical drawing and verify physical Nano/LCD pin order independently of placement requests.

No PCB footprints are assigned. The empty `.kicad_pcb` is a project placeholder; no routed board, manufacturable PCB or hardware qualification is claimed. Standard resistor, capacitor and push-switch symbols are used for discrete parts. Custom symbols describe purchased modules and functional terminals. Component fit, noise, power behaviour and direct LED data levels require bench verification.

All protected KiCad source changes go through Konnect MCP. Regenerate the SVG/PNG/PDF/netlist there, then run `scripts/preview_kicad.py` to publish the verified preview.
