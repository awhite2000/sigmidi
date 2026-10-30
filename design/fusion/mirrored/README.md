# SIGMIDI Foot Controller v0.1 — Left enclosure

**Left is the preferred enclosure and firmware default.** Its display, encoder and electronics are on the left; switch-pair extensions attach on the right. Main and modular assemblies have independent CAD files and matching print parts. The [full Fusion archive](../sigmidi-foot-controller-0.1.f3d) includes all component hierarchies and part libraries.

The complete Fusion archive and enclosure packages include [Arduino Nano ESP32 direct mounting](../nano-esp32/README.md) in all four assemblies. Four reinforced posts are integral to each electronics base and support the board component-side up. Upper shells, USB pockets, switch positions and mating edges are unchanged.

## Dimensions and components

The main body measures **350 × 92 × 54 mm**, with 65 mm switch pitch, 32.5 mm stagger, 53 mm row spacing and 30 mm upper-deck elevation. Roofs are 3 mm and sides at least 2 mm. The 25 × 20.183 mm icon between A and B is raised 0.6 mm on the full roof, giving 54.6 mm local height. [Icon detail](main/embossed-icon.png).

| Component | Approximate X, mm | Location |
|---|---:|---|
| Encoder | 12.5 | Lower row centreline |
| Dual TRS ports | 22.725 / 39.275 | Rear panel |
| Display PCB centre | 42.598 | Lower deck |
| A / 1 | 42.6 / 75.1 | Raised / lower row |
| Nano ESP32 | 99.31 | Below raised row, USB-C to rear |
| B / 2 | 107.6 / 140.1 | Raised / lower row |
| Pololu converter | 123.968 | Vented base clip mount |
| 9 V socket | 140.0 | Rear panel |
| C / 3 | 172.6 / 205.1 | Raised / lower row |
| D / 4 | 237.6 / 270.1 | Raised / lower row |
| E / 5 | 302.6 / 335.1 | Raised / lower row |

Coordinates span different rows and heights. The Waveshare 24382 PCB has its ribbon on the left, glass flush at Z0 and four hollow mounts for M2×5 screws. The Nano uses its manufacturer PCB model, component-side up on four integral base posts; the display uses its actual PCB shape. USB-C, TRS and DC ports face the rear. Wiring follows physical pin labels.

Switch labels read **A B C D E / 1 2 3 4 5** across the rows. Arial Bold outlines are 8 mm high, recessed 0.8 mm to the left of each LED, leaving 2.2 mm roof backing. Electrical tap IDs determine MIDI actions, calibration and LED assignments. Select **ENCLOSURE → LEFT** in firmware for 180° LCD rotation and matching menu order.

## Main enclosure

`main/midi-foot-mirrored-main.f3d` and `.step` contain the complete ten-switch assembly as named bodies in assembly coordinates. The full project archive provides the native component hierarchy.

| Print part | Role |
|---|---|
| `main/shell-left` | Electronics upper shell |
| `main/shell-right` | Outer switch upper shell |
| `main/base-left` | Electronics floor, PCB posts, converter clips and vents |
| `main/base-right` | Switch-side floor |

Print one of each. Upper joints use a vertical drop-down hook: the right shell lowers onto the left. Inclined-face clearance is 0.20 mm; exterior seams are 0.25 mm. Glue the base separately using straight internal glue lips. The base supports the shell perimeter and uses 1.8 mm positioning ribs with 0.20 mm wall clearance.

## Modular enclosure

The four-switch electronics section has **A B / 1 2**. Add zero to three 65 mm two-switch sections, then the integral-floor right cap.

| Switches | Repeatable uppers | Cap-adjacent upper | Pair bases | Width |
|---:|---|---|---:|---:|
| 4 | None | None | 0 | 164.85 mm |
| 6 | None | `pair-shell-at-right-cap-C` | 1 | 229.85 mm |
| 8 | `pair-shell-C` | `pair-shell-at-right-cap-D` | 2 | 294.85 mm |
| 10 | `pair-shell-C`, `pair-shell-D` | `pair-shell-at-right-cap-E` | 3 | 359.85 mm |

Use one `right-cap` and the electronics shell/base at every size. Every pair uses the same `pair-base`. The cap is 8.5 mm wide and approaches from the right while raised 2 mm, then seats down by 2 mm. Keep its fixed-floor/removable-base butt seam free of glue; clearance is 0.30 mm.

`modular/midi-foot-mirrored-modular.f3d` and `.step` contain the eight-switch example. Electronics shell/base and fit coupons are byte-identical to their corresponding `main/` files.

## Printing and assembly

Use **Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers** with the supplied profiles. Main shells print on their outer ends, seams upward. Pair shells print left mating edge down, right edge upward. The cap prints closed-right-end down. Bases print outside-floor down, mounts upward, without supports. Upper parts use automatic snug supports at 40°. Test both fit coupons first. [Tolerances](../printing-tolerances.md).

Glue upper and removable-base chains separately. Each pair base uses two M2×6 screws; electronics use four. The main and eight-switch modular assemblies each use eight base screws. The display uses four M2×5 countersunk screws; the Nano uses four M1.6x5 PCB screws directly into the base posts. Check the display's 1.39 mm nominal stud engagement against its actual blind holes.

Remove all twelve 0.6 mm rear vent membranes before operation. Optional LED holes have 0.8 mm covers; leave them closed when omitting LEDs. Provide at least 3 mm clearance below the base vents. The converter uses 4.8 mm-wide PETG clips and has 8.65 mm free space below its lowest component. Its regulated 5 V / nominal 1 A output supplies the optional LED rail; Nano VIN takes the 9 V input directly. [Power](../power.md) · [LEDs](../leds.md).

For base removal, release the Nano from its four posts and withdraw USB-C from the protective pocket partition. Leave slack in wires between upper-shell sockets and base electronics.

## Deliverables and verification

- [Main package](mirrored-main-mk3s-petg-06.zip): ten-switch CAD, oriented print parts, profiles, renders and reports.
- [Modular package](mirrored-modular-mk3s-petg-06.zip): eight-switch example, pair/cap parts and label variants.
- [Main top view](main/top.png), [assembly](main/assembled.png), [exploded view](main/exploded.png), [display mounting](main/display-underside.png).
- [Modular top view](modular/top.png), [assembly](modular/assembled.png), [exploded view](modular/exploded.png).
- [Current CAD/print package verification](../nano-esp32/package-verification.json), [Nano fit](../nano-esp32/assembly-clearance.json), [post wall sections and support-free slicing](../nano-esp32/print-verification.json). Upper print files retain their original verified hashes; native difference checks isolate the base changes to the Nano mounting areas.

Current assembly exports include the components-up Nano and fitted hardware. Their solid counts are recorded in [export verification](../nano-esp32/exports.json); print only the designated enclosure STLs/3MFs. Nominal geometry and toolpaths are checked. Printed tolerances, strength and thermal performance require hardware tests.
