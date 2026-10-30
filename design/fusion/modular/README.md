# SIGMIDI Foot Controller v0.1 — Right modular enclosure

Right has the electronics on the right and extends to the left. The preferred [Left modular enclosure](../mirrored/README.md) extends rightward. Each two-switch section holds one raised and one lower switch at 65 mm section pitch, 32.5 mm stagger, 53 mm row spacing and 30 mm elevation. Depth is 92 mm and body height 54 mm.

## Parts

| Part | Purpose |
|---|---|
| `electronics-shell`, `electronics-base` | Four-switch electronics section; matching main Right electronics parts |
| `pair-shell` | Repeatable C/3 upper section |
| `pair-shell-D` | Repeatable D/4 upper section |
| `pair-shell-at-cap-C`, `pair-shell-at-cap`, `pair-shell-at-cap-E` | Cap-adjacent C/3, D/4 or E/5 upper section |
| `pair-base` | Universal removable floor for any two-switch section |
| `left-cap` | 8.5 mm one-piece cap with integral floor |

STL/3MF files are oriented for printing. `midi-foot-modular.f3d` and `.step` contain the eight-switch assembly; individual marked upper-shell variants have CAD files where listed. Fit coupons are provided.

| Switches | Repeatable upper sections | Cap-adjacent upper | Pair bases | Width |
|---:|---|---|---:|---:|
| 4 | None | None | 0 | 164.85 mm |
| 6 | None | `pair-shell-at-cap-C` | 1 | 229.85 mm |
| 8 | `pair-shell` | `pair-shell-at-cap` | 2 | 294.85 mm |
| 10 | `pair-shell`, `pair-shell-D` | `pair-shell-at-cap-E` | 3 | 359.85 mm |

Every size uses the electronics shell/base and one left cap. The electronics section labels are **B A / 2 1** from left to right; extensions add C/3, D/4 and E/5 on the left. Arial Bold labels are 8 mm high and recessed 0.8 mm.

## Assembly and fasteners

Upper sections have continuous vertical drop-down hooked joints with 0.20 mm inclined clearance. Assemble the upper chain from electronics outward. The cap approaches from the left while raised 2 mm, then seats downward by 2 mm.

Glue the removable base chain separately at straight butt seams with 2 mm-high internal glue lands and 45° runouts. Align flat floor surfaces. Keep the 0.30 mm seam between the cap's integral floor and the removable pair base free of glue. Positioning ribs are 1.8 mm thick, 3 mm high, with 0.5 mm lead-ins and 0.20 mm wall clearance.

Each pair uses two M2×6 countersunk base screws; electronics use four. The eight-switch assembly uses eight base screws. The display uses four M2×5 countersunk screws, with 1.39 mm nominal engagement in its blind studs. MCU hardware is M1.6.

Release the Nano from its adapters and withdraw its USB-C connector from the pocket partition before lowering the populated floor. Leave power-wire slack between the rear socket and the converter on the base. [Power wiring](../power.md) and [LED installation](../leds.md) apply to every size.

## Printing

Use **Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers**, 6 mm brim. Pair shells print right-edge down; the cap prints closed-left-end down. Bases print outside-floor down without supports. Upper parts use automatic snug supports at 40°. Print coupons first; follow the [tolerance guide](../printing-tolerances.md).

Remove the twelve rear vent films before operation. Open LED covers only for fitted indicators. Provide at least 3 mm free space under the base vents. The converter's 1 A output limit covers the complete controller and LED load.

[Populated assembly](modular-assembled.png) · [Exploded view](modular-exploded.png) · [Cap/base fit](cap-floor-underside.png) · [Print orientations](new-parts-print-orientations.png) · [Two-screw mounts](pair-two-screw-mounts.png).

Mesh and slicing reports describe nominal geometry and toolpaths. Printed fit, load strength and thermal operation require physical checks.

## Current slicer estimates

| Part | Quantity | Print size X × Y × Z | Estimated time each |
|---|---:|---|---|
| pair-shell | 1 | 52 × 92 × 69 mm | 2h 37m 4s |
| pair-shell-at-cap | 1 | 52 × 92 × 69 mm | 2h 36m 36s |
| pair-base | 2 | 64.75 × 92 × 21 mm | 42m 38s |
| left-cap | 1 | 54 × 92 × 8.5 mm | 36m 32s |
| electronics-shell | 1 | 52 × 92 × 160.35 mm | 6h 20m 1s |
| electronics-base | 1 | 156.1 × 92 × 21 mm | 2h 3m 57s |

Estimated total: **15h 39m, 312 g**, including brims and supports, excluding fit coupons. Separate prints with the supplied PETG profile.
