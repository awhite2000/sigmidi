# SIGMIDI Foot Controller v0.1 — Main enclosure — current CAD and print files

**The preferred assembly is the [Left enclosure](../mirrored/README.md).** This page retains the original Right-variant technical details and deliverables.

Current fit: **0.20 mm normal clearance at the upper hooked joint** (was 0.30 mm) and **0.20 mm clearance between locating ribs and shell walls** (was 0.35 mm). Ribs remain 1.8 mm thick. The 0.25 mm glued seams, 0.30 mm cap-floor butt clearance and existing screw holes are retained. Use the supplied **0.6 mm nozzle / PETG / 0.3 mm layer** 3MFs and profile. Print the two matching fit coupons before the full shells; flow, first-layer setup and PETG shrinkage affect the final fit. See [fit and assembly checks](../snug-06-tolerances.json) and [coupon/calibration instructions](../printing-tolerances.md).


Current base revision: front positioning ribs are **1.8 mm thick**, matching the rear ribs, with 3 mm height and 0.5 mm top lead-ins. Four unobstructed gaps are joined into three continuous runs. Screw-boss/web and MCU/USB reliefs remain open. The same refined pair base fits every modular pair. See [fit verification](../positioning-rib-refinement.json).


An obsolete outboard TRS-port relief is also closed using the nominal 2 mm rear-wall profile. The enclosure-wide wall audit reinforces blind base-screw pilot caps from 0.5 to 2 mm in all seven upper-shell print shapes, with 45° shoulders and unchanged screw bores. The modular end cap front wall is restored from 1.66 to 2.19 mm, and an unused slit in the main left base is closed with the original 2 mm floor. Exterior surfaces, hardware positions, joints and functional clearances are preserved. Intentional LED/vent covers, joint and glue-land runouts, recessed text edges, countersinks and flexible clips keep their specified geometry. See [reinforcement checks](../enclosure-wall-reinforcement.json), [wall audit](../wall-thickness-audit.json) and [toolpath checks](../enclosure-wall-slice.json).

The rear upper-shell corners have continuous **2 mm R6/R4 walls** from Z−15 to Z−9.2, filling obsolete screw-boss reliefs that left only 0.34 mm at the main back-right corner. The matching back-left relief and modular end-cap relief are also filled. Exterior surfaces, screw mounts and pilots, joints, base seating and hardware positions are preserved. See [wall checks](../upper-corner-walls.json), [0.6 mm slice checks](../upper-corner-slice.json) and [section view](../upper-corner-wall-detail.png).

The Pololu mount uses two **4.8 mm-wide spring leaves** (previously 2.4 mm), retaining 1.6 mm bending thickness, the existing hook geometry and 0.6 mm outward insertion travel. Each root has a 0.8 mm, 45° outward gusset rising from the reinforced floor at Z−21. Both main and modular electronics bases use this mount; board position, all vents and the repaired corner are retained. See [wide clip checks](../wide-pololu-clips.json) and [mount detail](../clip-mount.png).

The front-right base corner has a continuous 2 mm floor, with the inherited narrow cut filled in both the main and modular electronics bases. The rounded perimeter, screw holes, vents and mounts are preserved. See [repair checks](../base-corner-repair.json) and [corner detail](../base-corner-detail.png).

Revision: **snug 0.6 mm PETG fit with 1.8 mm base positioning ribs**, with reinforced cooling grilles and PETG clip mount, retaining straight base glue lips. The assembled main enclosure remains 350 × 92 × 54 mm. The outer shell rests on a full-outline floor (2 mm generally, 3 mm in the vent reinforcement zone), with the upper skirt shortened to Z−22 and the floor bottom at Z−24.


## Recessed switch labels

The upper shells have recessed **Arial Bold** switch labels beside the optional LEDs: upper **E D C B A** and lower **5 4 3 2 1**, read left to right from the front. Every glyph's actual outline is 8 mm high and its recess is 0.8 mm deep, leaving 2.2 mm of the 3 mm top panel below it. The glyph's left edge is 6 mm right of the LED center, providing at least 3 mm horizontal clearance from the 6 mm LED flange. Counter shapes in A, B, D and 4 remain intact. Switch holes, LED seats and breakaway covers, roof-to-wall blends, shell joints, base parts and hardware positions are retained. See [label checks](../recessed-switch-labels.json) and [label view](../switch-labels.png).

## Parts and printing

Print one `shell-left`, `shell-right`, `base-left` and `base-right`. Their STL/3MF files are already in the recommended orientation at Z0. Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers, 6 mm brim. The shells print on their outer ends, open seam upward, with automatic snug supports at 40°. Bases print outside floor down, posts upward, without supports. The two small `fit-coupon` files test the retained upper-shell joint.

See [printing orientations and actual slicer support paths](printing-orientations-supports.png), [part dimensions](print-export.json), [slicing results](slice-verification.json) and [mesh audit](mesh-audit.json). The 3MFs contain the checked settings; no machine G-code is supplied.

## Power hardware

The right upper shell has the Ø8.4 mm DC input opening; the right base includes the raised PETG snap mount and grilles for the Pololu S13V10F5 #4083. No additional printed part or mounting screw is required. Use **9 V DC, center-negative, 5.5 × 2.1 mm**. The socket reference has 8 mm thread, 4 mm flange/body and 6 mm terminals, 18 mm overall, with a 2 mm outside nut. Assumed flange Ø12 / nut 13 mm AF dimensions need comparison with the purchased jack.

Solder the converter wires first, gently spread its two clips and lower the board onto the three bare-edge seats. Its PCB bottom is Z−11 mm, leaving 8.65 mm below the lowest component; no adhesive is required. Fit and tighten the socket, then solder and insulate its lugs. Sleeve goes to VIN, center to GND; regulated VOUT and GND feed DFRobot VIN/5 V and GND. Leave slack for base removal. Keep at least 3 mm free space beneath the floor inlets using adhesive rubber feet or pedalboard supports. Validate clip retention and temperatures under sustained load on the actual PETG print. See the package `power.md`, `ventilated-clip.json`, `aux-power.json`, `converter-carrier.json` and power close-ups. The converter is rated **1 A total** and lacks reverse-input-polarity protection.

The cooling layout now has six base slots beneath/around the Pololu mount, seven beneath DFRobot and three four-row rear exhaust columns. The rear pattern is now raised 17 mm, leaving a 7.6 mm solid top rim and at least 3 mm clearance to switch bodies. The former lower holes are restored to 2 mm solid wall; base slots and their 3 mm mounting-anchor margins are unchanged. See `raised-rear-vents.json`, `expanded-vents.json` and `rear-grille-ribs.json`.

One internal vertical rib reinforces the solid strip between the middle and rightmost rear slot columns, centered at X261.7 mm. It projects 2 mm inward from the original 2 mm back plate, giving a local thickness of 4 mm. Its 2 mm-wide crest has 2 × 2 mm chamfers at 45° on both sides and a 6 mm attachment footprint. The rib runs straight at X261.7 mm from the roof at Z27 mm to its seat on the bottom shell at Z−22 mm, merging with the existing chamfered USB pocket edge. The local PCB-front gap is 1 mm; nearby board fasteners also use the recorded local clearances. Other hardware retains at least 3 mm clearance, and the USB-C socket retains its 1 mm clearance envelope. The base geometry and exterior envelope are retained. All nine original slots remain in the finished part after membrane removal. Three matching slots complete the middle column, making four slots in each of three columns (12 total), with 380.16 mm² open area. The rear-rib update retains the exterior envelope, component positions, 7.6 mm top rim and 17 mm upward relocation. The current base reinforcement is described below. The left-hand gap is left clear to preserve clearance behind switch 4.


The base ventilation zone has a **1 mm internal reinforcement**, increasing its floor from 2 mm to 3 mm. The single rectangular zone is X208.6–262.4 mm and Y13–57.4 mm (53.8 × 44.4 mm), covering all thirteen slots with a 3 mm border around their combined envelope. The inside floor rises from Z−22 to Z−21; the outside remains at Z−24. All slots and existing floor bores remain open. The converter retains 8.65 mm clearance above the reinforced floor; board, clip-tip and screw-seat positions are unchanged. The raised floor shortens the exposed clip root by 1 mm, so retention should be checked on the actual PETG print. See [reinforcement checks](../base-vent-reinforcement.json).

## Assembly

1. Fit the upper-joint coupons. Assemble the upper halves by lowering the left shell vertically onto the right, then glue the upper seam.
2. Join the two bases at their **straight glue lips**. Dovetail tabs and recesses are removed. The internal lands rise 2 mm above the floor, with 45° inward tapers; align the flat outside floors while the adhesive cures. The nominal seam is 0.25 mm.
3. Install the controls and electronics at the existing positions. Seat the upper walls on the widened base, located by the existing ribs. Keep shell-to-base faces free of glue so the floor remains removable.
4. Attach the floor with eight M2×6 countersunk screws. The display uses four M2×5 screws. MCU M1.6 hardware is unchanged. Base clearances remain Ø2.6, countersinks Ø4.4 × 0.9 deep; shell pilots Ø1.9 × 6.5 deep.

The screen remains flush with the lower top surface; its hollow mounting towers and short-screw seats are retained. Optional Pololu 2535 LED holes retain 0.8 mm breakaway membranes and the existing recessed seats.

The populated MCU's USB-C connector passes through its dust pocket. Release the MCU from the base mounts and withdraw its connector from the pocket partition before lowering the populated base, as required by the existing connector geometry.

Current [glue-lip detail](straight-base-lips.png), [wall-on-base section](perimeter-ledge-detail.png), [exploded assembly](split-exploded.png) and [joint checks](straight-base-lips.json) match this revision. Earlier dovetail/inset-floor illustrations are archived and excluded from this package. Physical printed fit and adhesive strength still need validation.

**Rear vent print membranes:** all twelve rear slots have a 0.6 mm sacrificial film at their internal side (Y1.4–2 mm), flush with the existing inside wall. Each outside slot remains a 1.4 mm-deep recess. The rear vents are closed as printed. Before installing electronics, score around each recessed slot outline with a sharp hobby blade, remove the thin film and clean the edges. Preserve the permanent 2 mm wall and straight reinforcing rib. Remove all twelve films before operating the controller; this restores the original 380.16 mm² rear open area. The membranes add no projection into the enclosure and leave component clearances unchanged. Actual slicing with the supplied 0.6 mm nozzle profile is checked for all twelve films; cutting force still depends on the print. See [membrane checks](../rear-vent-membranes.json).

The right electronics section now uses **four M2×6 base screws**, including two near the split at X201 mm, Y6 and Y86 mm. The new mounts have Ø9 mm bosses, Ø1.9 × 6.5 mm blind pilots, and matching Ø2.6 mm base clearances with Ø4.4 × 0.9 mm countersinks. Leading 9 mm webs support end-down printing. Small local reliefs clear the retained locating ribs without cutting the 2 mm floor or straight seam glue lip. The split joint and all component positions are retained. The main enclosure and the illustrated 8-switch modular enclosure each use eight base screws in total; the display uses four M2×5 screws. See [mount checks](../extra-right-base-screws.json).


The four display mounts accept **M2×5 countersunk screws**. The recessed head seats are 1 mm deeper, preserving the flush display, 1.39 mm nominal stud engagement and 2 mm minimum tower walls. Base-shell screws remain M2×6. See [mount verification](../display-m2x5.json).

## Current slicer estimates

| Part | Quantity | Print size X × Y × Z | Estimated time each |
|---|---:|---|---|
| shell-left | 1 | 52 × 92 × 193.65 mm | 6h 46m 20s |
| shell-right | 1 | 52 × 92 × 160.35 mm | 6h 20m 1s |
| base-left | 1 | 193.65 × 92 × 21 mm | 1h 56m 54s |
| base-right | 1 | 156.1 × 92 × 21 mm | 2h 3m 57s |

Estimated total: **17h 7m, 343 g**, including brims and supports, excluding fit coupons. Separate prints with the supplied PETG profile.
