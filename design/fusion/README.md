# SIGMIDI Foot Controller v0.1 — Right enclosure reference — snug 0.6 mm PETG fit

**The preferred assembly is the [Left enclosure](mirrored/README.md).** This page retains the original Right-variant technical details and deliverables.

Current fit: **0.20 mm normal clearance at the upper hooked joint** (was 0.30 mm) and **0.20 mm clearance between locating ribs and shell walls** (was 0.35 mm). Ribs remain 1.8 mm thick. The 0.25 mm glued seams, 0.30 mm cap-floor butt clearance and existing screw holes are retained. Use the supplied **0.6 mm nozzle / PETG / 0.3 mm layer** 3MFs and profile. Print the two matching fit coupons before the full shells; flow, first-layer setup and PETG shrinkage affect the final fit. See [fit and assembly checks](snug-06-tolerances.json).


Current base revision: front positioning ribs are **1.8 mm thick**, matching the rear ribs, with 3 mm height and 0.5 mm top lead-ins. Four unobstructed gaps are joined into three continuous runs. Screw-boss/web and MCU/USB reliefs remain open. The same refined pair base fits every modular pair. See [fit verification](positioning-rib-refinement.json).


An obsolete outboard TRS-port relief is also closed using the nominal 2 mm rear-wall profile. The enclosure-wide wall audit reinforces blind base-screw pilot caps from 0.5 to 2 mm in all seven upper-shell print shapes, with 45° shoulders and unchanged screw bores. The modular end cap front wall is restored from 1.66 to 2.19 mm, and an unused slit in the main left base is closed with the original 2 mm floor. Exterior surfaces, hardware positions, joints and functional clearances are preserved. Intentional LED/vent covers, joint and glue-land runouts, recessed text edges, countersinks and flexible clips keep their specified geometry. See [reinforcement checks](enclosure-wall-reinforcement.json), [wall audit](wall-thickness-audit.json) and [toolpath checks](enclosure-wall-slice.json).

The rear upper-shell corners have continuous **2 mm R6/R4 walls** from Z−15 to Z−9.2, filling obsolete screw-boss reliefs that left only 0.34 mm at the main back-right corner. The matching back-left relief and modular end-cap relief are also filled. Exterior surfaces, screw mounts and pilots, joints, base seating and hardware positions are preserved. See [wall checks](upper-corner-walls.json), [0.6 mm slice checks](upper-corner-slice.json) and [section view](upper-corner-wall-detail.png).

The Pololu mount uses two **4.8 mm-wide spring leaves** (previously 2.4 mm), retaining 1.6 mm bending thickness, the existing hook geometry and 0.6 mm outward insertion travel. Each root has a 0.8 mm, 45° outward gusset rising from the reinforced floor at Z−21. Both main and modular electronics bases use this mount; board position, all vents and the repaired corner are retained. See [wide clip checks](wide-pololu-clips.json) and [mount detail](clip-mount.png).

The front-right base corner has a continuous 2 mm floor, with the inherited narrow cut filled in both the main and modular electronics bases. The rounded perimeter, screw holes, vents and mounts are preserved. See [repair checks](base-corner-repair.json) and [corner detail](base-corner-detail.png).

The active Fusion document is **MIDI Foot Controller - VERIFIED chassis**. It contains the main 10-switch enclosure and the separate `ALT Chainable` assembly. The files in this directory are the current revision; previous iterations are kept in the recovery archive.

The main enclosure is **350 × 92 × 54 mm**, with 65 mm switch pitch, 32.5 mm stagger, 53 mm row spacing, and a 30 mm raised rear row. Sides are at least 2 mm, top panels 3 mm. The base is 2 mm thick generally, with 3 mm local vent reinforcement, and follows the outer enclosure outline. Upper walls end at Z−22 and rest on the base, whose underside is Z−24. Screw mounts, component positions, supports and locating ribs are retained.


The upper shells have recessed **Arial Bold** switch labels beside the optional LEDs: upper **E D C B A** and lower **5 4 3 2 1**, read left to right from the front. Every glyph's actual outline is 8 mm high and its recess is 0.8 mm deep, leaving 2.2 mm of the 3 mm top panel below it. The glyph's left edge is 6 mm right of the LED center, providing at least 3 mm horizontal clearance from the 6 mm LED flange. Counter shapes in A, B, D and 4 remain intact. Switch holes, LED seats and breakaway covers, roof-to-wall blends, shell joints, base parts and hardware positions are retained. See [label checks](recessed-switch-labels.json) and [label view](switch-labels.png).

## Auxiliary power

The rear wall now has an Ø8.4 mm opening at X210, Z0 for the confirmed 18 mm socket (8 mm thread, 4 mm flange/body, 6 mm terminals; 2 mm nut). Input is **9 V DC, center-negative, 5.5 × 2.1 mm**. The unspecified flange/nut diameters use conservative Ø12 mm / 13 mm AF reference envelopes.

The **Pololu S13V10F5 #4083** (Kamami 1178565) uses the manufacturer STEP shape. Its raised, screw-free PETG clip mount is integrated into the right base in both assemblies. The PCB sits at X220…232.065, Y26…34.89, Z−11 mm, leaving 8.65 mm beneath its lowest component. Three small edge seats with lateral locating tabs and two relaxed spring leaves replace the surrounding carrier; no adhesive is required. Connect sleeve to converter VIN, center to GND, and regulated VOUT/GND to the DFRobot VIN/5 V and GND inputs.

See the [power wiring and ratings](../../docs/power.md), [socket fit report](aux-power.json), [carrier report](converter-carrier.json), [rear close-up](power-rear.png) and [internal close-up](power-internal.png). Checks prove at least 3 mm socket-to-component separation and no positive-volume hardware, wire or sampled assembly-path collisions. Socket mounting contact and PCB/carrier seating are intentional contacts. The selected module supplies **1 A total**, shared with the controller and optional LEDs; it has no reverse-input-polarity protection.

## Cooling

The electronics base has six rounded inlet slots beneath/around the Pololu and seven beneath DFRobot, each 2.4 mm wide. Four new slots surround the converter mount, with at least 3 mm clearance to mounting anchors. Twelve rear exhaust slots in three columns and four rows have 45° ends to match the end-down shell printing orientation. The complete rear pattern is raised 17 mm. Row bottoms are Z2, Z8, Z14 and Z20; the top edge is Z22.4, leaving a 7.6 mm solid rim. Old lower holes are restored to the original 2 mm wall. Top switch mounting panels, the USB pocket and connectors are retained, with at least 3 mm clearance from the rear slots to the switch bodies. Use at least 3 mm adhesive rubber feet or equivalent free space below the base so its inlets remain open.

One internal vertical rib reinforces the solid strip between the middle and rightmost rear slot columns, centered at X261.7 mm. It projects 2 mm inward from the original 2 mm back plate, giving a local thickness of 4 mm. Its 2 mm-wide crest has 2 × 2 mm chamfers at 45° on both sides and a 6 mm attachment footprint. The rib runs straight at X261.7 mm from the roof at Z27 mm to its seat on the bottom shell at Z−22 mm, merging with the existing chamfered USB pocket edge. The local PCB-front gap is 1 mm; nearby board fasteners also use the recorded local clearances. Other hardware retains at least 3 mm clearance, and the USB-C socket retains its 1 mm clearance envelope. The base geometry and exterior envelope are retained. All nine original slots remain in the finished part after membrane removal. Three matching slots complete the middle column, making four slots in each of three columns (12 total), with 380.16 mm² open area. The rear-rib update retains the exterior envelope, component positions, 7.6 mm top rim and 17 mm upward relocation. The current base reinforcement is described below. The left-hand gap is left clear to preserve clearance behind switch 4.

See [rib geometry checks](rear-grille-ribs.json), [inside chamfers](rear-ribs-internal.png), [empty clip mount](clip-mount.png), [base ventilation](ventilation-base.png), [rear exhausts](ventilation-rear.png) and [geometry checks](ventilated-clip.json) and [expanded grille checks](expanded-vents.json) and [rear relocation checks](raised-rear-vents.json). Thermal performance, spring retention and fatigue need verification on the actual PETG print under sustained operating load.


The base ventilation zone has a **1 mm internal reinforcement**, increasing its floor from 2 mm to 3 mm. The single rectangular zone is X208.6–262.4 mm and Y13–57.4 mm (53.8 × 44.4 mm), covering all thirteen slots with a 3 mm border around their combined envelope. The inside floor rises from Z−22 to Z−21; the outside remains at Z−24. All slots and existing floor bores remain open. The converter retains 8.65 mm clearance above the reinforced floor; board, clip-tip and screw-seat positions are unchanged. The raised floor shortens the exposed clip root by 1 mm, so retention should be checked on the actual PETG print. See [reinforcement checks](base-vent-reinforcement.json).

## Current joints

**All base dovetails are removed.** Base sections meet at straight butt faces, with continuous internal glue lands rising 2 mm above the floor and tapering inward over 2 mm at 45°. The main seam remains X193.65/193.9 mm, a nominal 0.25 mm gap. Join the base separately from the upper shell; align its flat outside floor faces while gluing.

The upper-shell continuous drop-down hooked joint retains its shape: lower each left part vertically onto its right neighbor. Its 2 × 2 mm bevel, seating lands, 0.20 mm inclined clearance and 0.25 mm exterior seam are retained. The one-piece cap retains its side approach at +2 mm Z followed by a 2 mm downward seat.

There is now **one universal `pair-base`** for standard and cap-adjacent modules. A special cap-adjacent **upper shell** is still required for cap entry. The cap's integral floor retains its 0.30 mm butt clearance to the removable universal base; keep that seam free of glue.

## Deliverables

- [Main Fusion model](midi-foot-chassis.f3d) and [STEP](midi-foot-chassis.step).
- [Main CAD and print package](print/mk3s-petg-06-print-package.zip), [print instructions](print/README.md).
- [Modular Fusion model](modular/midi-foot-modular.f3d), [STEP](modular/midi-foot-modular.step), [CAD and print package](modular/chainable-enclosure-mk3s-petg-06.zip), [module quantities](modular/README.md).
- [Current native render gallery](../../previews/README.md), [exact top view](panel-top.png), [base glue-lip detail](print/straight-base-lips.png), [printing orientations and slicer supports](print/printing-orientations-supports.png).
- [Current component bounds](current-layout.json), [joint validation](straight-base-lips.json), [native render provenance](render-manifest.json), [CAD export validation](cad-export.json).

Assembly CAD includes installed hardware and nonphysical layout/wiring references. Print the individual STL/3MF parts rather than the complete STEP assembly. Optional Pololu 2535 LEDs are shown fitted in populated views; their printable mounting membranes remain present.

## Validation and refresh

All changed bases are single connected solids. Installed-part, added-material/hardware, LED wiring, 21-position floor insertion and 41-position straight-seam approach checks pass the 0.001 mm³ positive-volume threshold. Standard and cap-adjacent pair bases have identical native geometry. See `straight-base-lips.json`. Geometry and slicing checks do not establish physical adhesive strength or printed tolerances.

`refresh_current_views.py` captures the live main/modular model and exports the current right upper shell and base STLs. `export_current_cad.py` exports independent main-only CAD copies and the separate modular assembly, checking for solid STEP content. Run scripts through `scripts/fusion_mcp_client.py` with `fusion_mcp_execute` and a JSON script argument; they do not create additional Fusion documents.

After native exports, run `verify_power_layout.py`, `verify_power_geometry.py` (through MCP), `slice_print_parts.py`, `modular/slice_modular.py`, `audit_print_mesh.py`, `render_print_orientations.py` and `package_current.py`. The slicer profiles target Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers. Shells use automatic snug supports; bases print floor down without supports. The upper-joint fit coupons are still compatible.

`set_straight_base_lips.py`, `add_converter_carrier.py`, `add_dc_power_socket.py` and `add_ventilated_clip_mount.py` and `complete_clip_locators.py` and `add_more_vents.py` and `move_rear_vents.py` are guarded one-time conversions, already applied. Historical construction and migration scripts are in the recovery archive, not in the current workflow. Do not replay them on the finished model.

`reinforce_rear_column.py` is the guarded correction for the current internal rear rib; it must not be replayed after installation.

`reinforce_base_vents.py` is the guarded one-time local floor reinforcement, already applied in the current deliverables.

`extend_rear_rib_to_base.py` is the guarded roof-to-base extension. See [seating detail](rear-rib-base-seat.png) and [extension checks](full-height-rear-rib.json).

`straighten_rear_rib.py` is the guarded straightening and USB-pocket merge. Current local clearance checks are in [straight-rear-rib.json](straight-rear-rib.json).

**Rear vent print membranes:** all twelve rear slots have a 0.6 mm sacrificial film at their internal side (Y1.4–2 mm), flush with the existing inside wall. Each outside slot remains a 1.4 mm-deep recess. The rear vents are closed as printed. Before installing electronics, score around each recessed slot outline with a sharp hobby blade, remove the thin film and clean the edges. Preserve the permanent 2 mm wall and straight reinforcing rib. Remove all twelve films before operating the controller; this restores the original 380.16 mm² rear open area. The membranes add no projection into the enclosure and leave component clearances unchanged. Actual slicing with the supplied 0.6 mm nozzle profile is checked for all twelve films; cutting force still depends on the print. See [membrane checks](rear-vent-membranes.json).

`add_rear_vent_membranes.py` is the guarded sacrificial-film conversion. See [membrane cross-section](rear-vent-membrane-section.png).

`verify_rear_membrane_slice.py` checks non-support extrusion across every rear slot core on every print layer, using the current 0.8 mm G-code. See [slice detail](rear-vent-membrane-slice.json).

The right electronics section now uses **four M2×6 base screws**, including two near the split at X201 mm, Y6 and Y86 mm. The new mounts have Ø9 mm bosses, Ø1.9 × 6.5 mm blind pilots, and matching Ø2.6 mm base clearances with Ø4.4 × 0.9 mm countersinks. Leading 9 mm webs support end-down printing. Small local reliefs clear the retained locating ribs without cutting the 2 mm floor or straight seam glue lip. The split joint and all component positions are retained. The main enclosure and the illustrated 8-switch modular enclosure each use eight base screws in total; the display uses four M2×5 screws. See [mount checks](extra-right-base-screws.json).


`add_right_split_screws.py` adds the two matching mounts to each right section. See [right-section mount view](right-shell-base-mounts.png).

The four display mounts accept **M2×5 countersunk screws**. The recessed head seats are 1 mm deeper, preserving the flush display, 1.39 mm nominal stud engagement and 2 mm minimum tower walls. Base-shell screws remain M2×6. See [mount verification](display-m2x5.json).


## Independent mirrored alternatives

[Left-electronics main and right-extending modular variants](mirrored/README.md) are provided separately. The existing main and modular CAD/print deliveries remain intact. The mirrored folder contains its own CAD, oriented print parts, previews and verification.

## SIGMIDI presentation

The project is named **SIGMIDI Foot Controller**. [Branded enclosure renderings](../../previews/README.md#sigmidi-enclosure-presentation-sheets) cover both orientations and the main and modular assemblies. Native CAD filenames, document names and historical verification records retain their original identifiers for traceability.
