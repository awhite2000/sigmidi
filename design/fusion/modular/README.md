# SIGMIDI Foot Controller v0.1 — Right chainable two-switch enclosure — current alternative

**The preferred assembly is the [Left enclosure](../mirrored/README.md).** This page retains the original Right-variant technical details and deliverables.

Current fit: **0.20 mm normal clearance at the upper hooked joint** (was 0.30 mm) and **0.20 mm clearance between locating ribs and shell walls** (was 0.35 mm). Ribs remain 1.8 mm thick. The 0.25 mm glued seams, 0.30 mm cap-floor butt clearance and existing screw holes are retained. Use the supplied **0.6 mm nozzle / PETG / 0.3 mm layer** 3MFs and profile. Print the two matching fit coupons before the full shells; flow, first-layer setup and PETG shrinkage affect the final fit. See [fit and assembly checks](../snug-06-tolerances.json) and [coupon/calibration instructions](../printing-tolerances.md).


Current base revision: front positioning ribs are **1.8 mm thick**, matching the rear ribs, with 3 mm height and 0.5 mm top lead-ins. Four unobstructed gaps are joined into three continuous runs. Screw-boss/web and MCU/USB reliefs remain open. The same refined pair base fits every modular pair. See [fit verification](../positioning-rib-refinement.json).


An obsolete outboard TRS-port relief is also closed using the nominal 2 mm rear-wall profile. The enclosure-wide wall audit reinforces blind base-screw pilot caps from 0.5 to 2 mm in all seven upper-shell print shapes, with 45° shoulders and unchanged screw bores. The modular end cap front wall is restored from 1.66 to 2.19 mm, and an unused slit in the main left base is closed with the original 2 mm floor. Exterior surfaces, hardware positions, joints and functional clearances are preserved. Intentional LED/vent covers, joint and glue-land runouts, recessed text edges, countersinks and flexible clips keep their specified geometry. See [reinforcement checks](../enclosure-wall-reinforcement.json), [wall audit](../wall-thickness-audit.json) and [toolpath checks](../enclosure-wall-slice.json).

The rear upper-shell corners have continuous **2 mm R6/R4 walls** from Z−15 to Z−9.2, filling obsolete screw-boss reliefs that left only 0.34 mm at the main back-right corner. The matching back-left relief and modular end-cap relief are also filled. Exterior surfaces, screw mounts and pilots, joints, base seating and hardware positions are preserved. See [wall checks](../upper-corner-walls.json), [0.6 mm slice checks](../upper-corner-slice.json) and [section view](../upper-corner-wall-detail.png).

The Pololu mount uses two **4.8 mm-wide spring leaves** (previously 2.4 mm), retaining 1.6 mm bending thickness, the existing hook geometry and 0.6 mm outward insertion travel. Each root has a 0.8 mm, 45° outward gusset rising from the reinforced floor at Z−21. Both main and modular electronics bases use this mount; board position, all vents and the repaired corner are retained. See [wide clip checks](../wide-pololu-clips.json) and [mount detail](../clip-mount.png).

The front-right base corner has a continuous 2 mm floor, with the inherited narrow cut filled in both the main and modular electronics bases. The rounded perimeter, screw holes, vents and mounts are preserved. See [repair checks](../base-corner-repair.json) and [corner detail](../base-corner-detail.png).

Each 65 mm-pitch module holds one raised rear switch and one lower front switch, retaining the 32.5 mm stagger, 53 mm row spacing and 30 mm elevation. The main 350 mm enclosure remains a separate assembly. Both now use straight base glue lips and full-outline 2 mm bearing floors.


## Recessed switch labels

The upper shells have recessed **Arial Bold** switch labels beside the optional LEDs: upper **E D C B A** and lower **5 4 3 2 1**, read left to right from the front. Every glyph's actual outline is 8 mm high and its recess is 0.8 mm deep, leaving 2.2 mm of the 3 mm top panel below it. The glyph's left edge is 6 mm right of the LED center, providing at least 3 mm horizontal clearance from the 6 mm LED flange. Counter shapes in A, B, D and 4 remain intact. Switch holes, LED seats and breakaway covers, roof-to-wall blends, shell joints, base parts and hardware positions are retained. See [label checks](../recessed-switch-labels.json) and [label view](../switch-labels.png).

## Parts

| File | Quantity for the shown 8-switch assembly | Purpose |
|---|---:|---|
| `pair-shell` | 1 | Standard upper switch-pair section |
| `pair-shell-at-cap` | 1 | Leftmost upper section with cap-entry relief |
| `pair-base` | **2** | Universal removable base for either upper section |
| `left-cap` | 1 | 8.5 mm one-piece end cap, with integral floor |
| `electronics-shell` | 1 | Byte-identical main right shell |
| `electronics-base` | 1 | Byte-identical main right base |

Each file has an oriented STL and an editable 3MF. The two compatible `fit-coupon` parts are also supplied. **There is no separate `pair-base-at-cap` file:** use the same `pair-base` at every pair position. It has the same two M2×6 clearances, locating ribs and transition support as before, and now measures 64.75 × 92 × 21 mm in print orientation.

The leftmost upper shell still differs: its cap-facing receiver permits a side approach with the cap raised 2 mm, followed by a 2 mm downward seat. The cap's full 2 mm floor remains integral, ends at X128.6, and clears the universal base starting at X128.9 by 0.30 mm. The cap needs no base screws or detachable floor.

| Total switches | Standard upper sections | Cap-adjacent upper sections | Universal pair bases | Overall width |
|---:|---:|---:|---:|---:|
| 6 | 0 | 1 | 1 | 229.85 mm |
| 8 | 1 | 1 | 2 | 294.85 mm |
| 10 | 2 | 1 | 3 | 359.85 mm |

All configurations also use one end cap and one electronics shell/base pair. Depth is 92 mm and assembled height 54 mm, excluding actuators. The main 10-switch enclosure remains 350 mm wide; the modular 10-switch version is wider because of its extra end cap.

## Choose the engraved upper shells

The fixed electronics section is marked **B A / 2 1**. Each section on its left adds C/3, D/4, then E/5. The integral end cap and all bases remain unmarked and unchanged. Use the following shells for the existing 6/8/10-switch modular assemblies; each pair still uses the same universal `pair-base`.

| Total switches | Rightmost pair next to electronics | Middle pair | Leftmost pair beside cap |
|---:|---|---|---|
| 6 | — | — | `pair-shell-at-cap-C` (C/3) |
| 8 | `pair-shell` (C/3) | — | `pair-shell-at-cap` (D/4) |
| 10 | `pair-shell` (C/3) | `pair-shell-D` (D/4) | `pair-shell-at-cap-E` (E/5) |

STL and 3MF files are supplied for all five marked upper sections. The three additional alternatives also have individual Fusion/STEP source files. The live Fusion document keeps those alternatives under the hidden **ALT Engraved pair print variants - NOT assembly** component, outside both assembled models. The illustrated eight-switch assembly uses C/3 and D/4. Print only the upper-shell variants required by the chosen count; the 65 mm section geometry and cap-entry reliefs retain their prior fit.

## Joining and mounting

Glue the upper chain right-to-left using the unchanged vertical drop-down upper joints. Fit the one-piece cap using its raised side approach and downward seat. Assemble the removable floor chain separately by gluing the **straight butt seams**, aligning the flat outside floors. All base dovetails are removed; 2 mm-high continuous internal glue lands have 45° inward runouts.

Keep the universal base-to-fixed-cap floor seam free of glue. Lift the assembled removable floor from below and seat the upper walls on it, using the retained locating ribs. Each switch-pair section uses two M2×6 countersunk screws; the electronics section uses four. The shown 8-switch base therefore uses eight screws. Display hardware uses four M2×5; MCU M1.6 hardware is unchanged.

The optional lower LED bus retains its 0.7 mm rearward doglegs across the shell joints. Component, wire, screw and support positions are unchanged. The existing MCU connector withdrawal step is still required before removing the populated floor; see the main print instructions.

## Auxiliary DC power

The electronics shell/base include the same rear DC inlet, raised PETG snap mount and board ventilation grilles as the main enclosure. Socket center is native X210, Z0; input is **9 V DC, center-negative, 5.5 × 2.1 mm**. Fit the 18 mm socket (8 mm thread + 4 mm flange/body + 6 mm terminals, 2 mm nut) and the Pololu S13V10F5 #4083 (Kamami 1178565). Flange Ø12 mm and nut 13 mm AF are conservative assumed envelopes. The regulator is raised 6 mm, leaving 8.65 mm below its lowest component. Spread the two leaves, lower the PCB onto three bare-edge seats and release them; no adhesive, screws or separate printed carrier are required. Use at least 3 mm free space beneath the floor grilles, and verify retention and temperatures on the actual PETG print.

Connect socket sleeve to converter VIN, center to GND, and converter VOUT/GND to DFRobot VIN/5 V and GND. Leave slack across the detachable floor. See package `power.md` and the power reports/close-ups. All module widths and switch positions remain unchanged. The regulator's **1 A rating is shared** by all loads; it has no reverse-input-polarity protection.

The cooling layout now has six base slots beneath/around the Pololu mount, seven beneath DFRobot and three four-row rear exhaust columns. The rear pattern is now raised 17 mm, leaving a 7.6 mm solid top rim and at least 3 mm clearance to switch bodies. The former lower holes are restored to 2 mm solid wall; base slots and their 3 mm mounting-anchor margins are unchanged. See `raised-rear-vents.json`, `expanded-vents.json` and `rear-grille-ribs.json`.

One internal vertical rib reinforces the solid strip between the middle and rightmost rear slot columns, centered at X261.7 mm. It projects 2 mm inward from the original 2 mm back plate, giving a local thickness of 4 mm. Its 2 mm-wide crest has 2 × 2 mm chamfers at 45° on both sides and a 6 mm attachment footprint. The rib runs straight at X261.7 mm from the roof at Z27 mm to its seat on the bottom shell at Z−22 mm, merging with the existing chamfered USB pocket edge. The local PCB-front gap is 1 mm; nearby board fasteners also use the recorded local clearances. Other hardware retains at least 3 mm clearance, and the USB-C socket retains its 1 mm clearance envelope. The base geometry and exterior envelope are retained. All nine original slots remain in the finished part after membrane removal. Three matching slots complete the middle column, making four slots in each of three columns (12 total), with 380.16 mm² open area. The rear-rib update retains the exterior envelope, component positions, 7.6 mm top rim and 17 mm upward relocation. The current base reinforcement is described below. The left-hand gap is left clear to preserve clearance behind switch 4.


The base ventilation zone has a **1 mm internal reinforcement**, increasing its floor from 2 mm to 3 mm. The single rectangular zone is X208.6–262.4 mm and Y13–57.4 mm (53.8 × 44.4 mm), covering all thirteen slots with a 3 mm border around their combined envelope. The inside floor rises from Z−22 to Z−21; the outside remains at Z−24. All slots and existing floor bores remain open. The converter retains 8.65 mm clearance above the reinforced floor; board, clip-tip and screw-seat positions are unchanged. The raised floor shortens the exposed clip root by 1 mm, so retention should be checked on the actual PETG print. See [reinforcement checks](../base-vent-reinforcement.json).

## Printing and validation

Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers, 6 mm brim. Print each part individually. Standard and cap-adjacent upper shells print right-edge down (−X upward); the cap prints closed-left-end down (+X upward); universal bases print outside floor down (+Z upward). Bases require no supports; upper shells and cap use automatic snug supports at 40°.

See [current assembly](modular-assembled.png), [exploded underside](modular-exploded.png), [cap and universal base](cap-floor-underside.png), [part orientations](new-parts-print-orientations.png), [two-screw mounting](pair-two-screw-mounts.png), [joint verification](straight-base-lips.json), [mesh audit](mesh-audit.json) and [slicing results](slice-verification.json).

The current Fusion/STEP exports contain this alternative only, without the 150 mm parent comparison offset used in the main live document. All changed parts are single connected solids; 21-position floor insertion and 41-position straight base-seam approach checks pass. The universal base is identical in both pair positions. Geometry checks do not establish printed tolerances or adhesive strength. Historical cap/base variants and obsolete illustrations are in the recovery archive and excluded from this package.

**Rear vent print membranes:** all twelve rear slots have a 0.6 mm sacrificial film at their internal side (Y1.4–2 mm), flush with the existing inside wall. Each outside slot remains a 1.4 mm-deep recess. The rear vents are closed as printed. Before installing electronics, score around each recessed slot outline with a sharp hobby blade, remove the thin film and clean the edges. Preserve the permanent 2 mm wall and straight reinforcing rib. Remove all twelve films before operating the controller; this restores the original 380.16 mm² rear open area. The membranes add no projection into the enclosure and leave component clearances unchanged. Actual slicing with the supplied 0.6 mm nozzle profile is checked for all twelve films; cutting force still depends on the print. See [membrane checks](../rear-vent-membranes.json).

The right electronics section now uses **four M2×6 base screws**, including two near the split at X201 mm, Y6 and Y86 mm. The new mounts have Ø9 mm bosses, Ø1.9 × 6.5 mm blind pilots, and matching Ø2.6 mm base clearances with Ø4.4 × 0.9 mm countersinks. Leading 9 mm webs support end-down printing. Small local reliefs clear the retained locating ribs without cutting the 2 mm floor or straight seam glue lip. The split joint and all component positions are retained. The main enclosure and the illustrated 8-switch modular enclosure each use eight base screws in total; the display uses four M2×5 screws. See [mount checks](../extra-right-base-screws.json).


The four display mounts accept **M2×5 countersunk screws**. The recessed head seats are 1 mm deeper, preserving the flush display, 1.39 mm nominal stud engagement and 2 mm minimum tower walls. Base-shell screws remain M2×6. See [mount verification](../display-m2x5.json).

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

## SIGMIDI presentation

The project is named **SIGMIDI Foot Controller**. [Branded enclosure renderings](../../../previews/README.md#sigmidi-enclosure-presentation-sheets) cover both orientations and the main and modular assemblies. Native CAD filenames, document names and historical verification records retain their original identifiers for traceability.
