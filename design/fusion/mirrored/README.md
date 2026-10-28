# SIGMIDI Foot Controller v0.1 — Left-electronics mirrored enclosure variants

**Left is the preferred enclosure and the default for new firmware configurations.** These main and modular assemblies are independent of the original Right models. The original main enclosure, modular enclosure, print files and packages remain intact in their existing locations. Their delivery files are fingerprinted in `original-file-signatures.json`; the complete current native design, including all original and Left alternatives, is in `../sigmidi-foot-controller-0.1.f3d`. Superseded recovery snapshots were removed during project cleanup.

The main case stays **350 × 92 × 54 mm**, with its existing stepped top, 30 mm upper-row elevation, switch positions reflected left to right, 65 mm horizontal switch pitch, current 53 mm row pitch, walls, seams and 0.6 mm PETG fitting allowances. The row pitch reflects the latest LED-equipped enclosure. Encoder and display positions retain the latest clearances.

## Component order and actual parts

Looking from above, the electronics are on the left. Approximate X coordinates in the 350 mm chassis:

| Component | X position, mm | Position in depth |
|---|---:|---|
| Encoder | 12.5 | Lower row centreline |
| TRS ports | 22.725 / 39.275 | Rear panel |
| Display PCB centre | 42.598 | Lower deck |
| A | 42.6 | Raised row |
| 1 | 75.1 | Lower row |
| DFRobot board | 99.31 | Below raised row, USB-C to rear |
| B | 107.6 | Raised row |
| Pololu converter | 123.968 | Vented carrier |
| 9 V socket | 140.0 | Rear panel |
| 2 | 140.1 | Lower row |
| C / 3 | 172.6 / 205.1 | Raised / lower rows |
| D / 4 | 237.6 / 270.1 | Raised / lower rows |
| E / 5 | 302.6 / 335.1 | Raised / lower rows |

These are longitudinal coordinates across different rows/heights, not a single line of components. The DC input and switch 2 are effectively in the same column.

The **actual PCB models keep their handedness**. Their component faces remain upward, the LCD remains flush and readable, and USB-C/TRS/DC connectors still face the rear. In both mirrored alternatives the complete LCD is rotated **180° in its own plane**, with the **ribbon on the left**. Its asymmetric glass opening and seat follow that rotation (0.5 mm leftward adjustment); the glass stays flush at Z = 0. The four symmetric mount positions, hollow posts and M2×5 screws are unchanged. New firmware configurations already select Left, combining 180° screen rotation and the matching switch-list order. For an existing saved setup, select ENCLOSURE → LEFT and save. The original alternatives retain their existing display orientation. The TRS saddle follows the real socket body. The USB partition retains its protective pocket and print chamfers; its opening has a small additional clearance allowance. Power-wire clearance references run to the relocated pads. Wiring uses the actual printed pin names, never mirrored pin labels.

Labels are readable **Arial Bold, 8 mm high, recessed 0.8 mm**, now to the left of each LED. Main labels are A–E and 1–5, both left to right. The board, switch, LED and message identities are retained; this CAD alternative does not change the firmware's stored electrical tap assignments. Preserve those identities when wiring the mirrored panel.

## Main enclosure

`main/midi-foot-mirrored-main.f3d` and `.step` contain the complete mirrored ten-switch assembly. The four print parts are:

- `main/shell-left`: electronics side.
- `main/shell-right`: closed outer switch side.
- `main/base-left`: electronics base with the existing converter clips, PCB posts, vents and revised M2×5 LCD mounts.
- `main/base-right`: switch-side base.

The two `main/fit-coupon` files test the retained upper sliding joint before a full print. The **right** shell now lowers vertically onto the **left** shell. Base seams retain straight glue lips.

## Modular enclosure, extending right

`modular/midi-foot-mirrored-modular.f3d` and `.step` show the independent eight-switch example, **294.85 × 92 × 54 mm**. The fixed electronics module is on the left; extra switch-pair sections and the one-piece cap are added to the right.

| Total switches | Repeatable upper shells | Right-cap-adjacent upper | Universal pair bases | Right cap |
|---:|---|---|---:|---:|
| 4 | None | None | 0 | 1 |
| 6 | None | C/3 | 1 | 1 |
| 8 | C/3 | D/4 | 2 | 1 |
| 10 | C/3 and D/4 | E/5 | 3 | 1 |

For four switches, the cap mates directly to the electronics module. Select `pair-shell-C` or `pair-shell-D` for repeatable sections and `pair-shell-at-right-cap-C`, `-D` or `-E` for the last pair. All use the same `pair-base`. The `right-cap` has its integrated floor and no base screws. Its existing narrow 8.5 mm section and side-entry relief are retained. Follow the cap's retained lift/side-entry movement, reflected to approach from the right.

The electronics shell/base and the fit coupons in `modular/` are byte-identical aliases of the corresponding new `main/` print files, not the original right-electronics files. New mirrored parts mate with one another; keep them in their own assembly.

Each switch-pair base uses two M2×6 screws; the electronics base uses four. The eight-switch example uses eight base screws. The display uses four **M2×5 countersunk screws**; MCU fasteners are unchanged.

## Printing and checks

The supplied profile targets **Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers**. The left shell sits on its left outer end, the right shell on its right outer end, with seams upward. Pair shells sit on their left mating edge with their right edge upward. The right cap sits on its closed right end. Bases sit outside-floor down, mounts upward. Import the supplied oriented STL or editable 3MF; do not apply a second mirror in the slicer. Keep the existing removable rear vent films and optional LED hole covers until commissioning.

Native fit, base withdrawal, readable text, interchangeable electronics parts, mesh integrity and actual slicing are recorded in `variant-creation.json`, `export-verification.json`, `print-export.json`, `mesh-audit.json`, `slice-verification.json` and `verification-summary.json`. Intentional overlap between fitted LED references and the optional breakaway covers is identified separately. Printed strength, thermal behaviour and physical fitting still depend on the printer and assembly.

The rotated LCD pose and fit are recorded in `display-rotation.json`. The current native design is preserved in `../sigmidi-foot-controller-0.1.f3d`.

Previews: `main/display-ribbon-left.png`, `main/display-underside.png`, `main/assembled.png`, `main/top.png`, `main/internal.png`, `main/exploded.png`, `main/base-mounts.png`, `modular/assembled.png`, `modular/top.png` and `modular/exploded.png`.

## Delivery packages

`mirrored-main-mk3s-petg-06.zip` contains the main ten-switch assembly and its oriented print files. `mirrored-modular-mk3s-petg-06.zip` contains the eight-switch example, right-extending parts, cap, label variants and interchangeable electronics parts. Both include this shared guide and verification reports. Extract both into one directory for the complete alternative set; each archive contains the files for its selected assembly. The source project also retains the individual CAD/mesh files and `delivery-verification.json` with package hashes.

## SIGMIDI presentation

The project is named **SIGMIDI Foot Controller**. [Branded enclosure renderings](../../../previews/README.md#sigmidi-enclosure-presentation-sheets) cover both orientations and the main and modular assemblies. Native CAD filenames, document names and historical verification records retain their original identifiers for traceability.

## Embossed SIGMIDI icon

Both preferred Left assemblies carry the supplied icon on the electronics upper shell, between A and B. The mark is **25 × 20.183 mm**, proportionally scaled, with **0.6 mm raised relief**. Its centre is X75.1, Y−18 mm in assembly coordinates, on the Z30 mm roof. It is shifted 6.5 mm toward the front from the switch centreline to stay entirely on the flat deck. The original full 3 mm roof remains below it. The nominal 54 mm case height becomes 54.6 mm locally at the icon; controls and all mounting features keep their positions.

The main `shell-left` and modular `electronics-shell-left` remain interchangeable. Right enclosures and extension-pair shells are unchanged. [Native fit and solid checks](embossed-icon-25mm.json) record the placement, absence of hardware collisions and unchanged unrelated components. [Icon close-up](main/embossed-icon.png).

Complete assembly F3D/STEP deliveries use named bodies flattened into assembly coordinates, including hidden hardware. The open Fusion document retains the editable component hierarchy. [Complete export checks](emboss-complete-cad.json) account for every solid body.
