# SIGMIDI Foot Controller v0.1 — Snug fit with a 0.6 mm nozzle

Target process: Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers, 0.67 mm nominal extrusion width. Use the supplied `mk3s-petg-06.ini` or the settings embedded in the current 3MFs. The CAD clearances are a starting point for a calibrated printer, not measured results from a physical test.

| Interface | Previous CAD clearance | Current target |
|---|---:|---:|
| Upper hooked joint, normal to inclined mating faces | 0.30 mm | 0.20 mm |
| Base positioning rib to inner shell wall, per face | 0.35 mm | 0.20 mm |
| Glued outer split seams | 0.25 mm | 0.25 mm |
| Integral cap floor to removable base butt edge | 0.30 mm | 0.30 mm |

The cap-facing receivers retain their special side-entry relief. The cap still approaches from the left while raised 2 mm, then seats downward. This entry relief is distinct from the loaded inclined mating faces. Both front and rear base positioning ribs retain their 1.8 mm thickness, 3 mm height and 0.5 mm lead-ins. The model is not globally scaled or offset, and the existing screw holes, component mounts and exterior dimensions are retained.

See [sections of the actual print meshes](snug-fit-sections.png).

Print `fit-coupon-left` and `fit-coupon-right` first with the supplied orientations, material and 0.6 mm settings. These are exact sections of the current upper joint, including its seating land. Remove their brims/supports and let both parts cool before testing the downward seating motion. Aim for a snug hand fit that seats fully; the final joint is glued rather than forced together as an interference fit.

If the coupon binds only at the bed-contact edge, check the first-layer setup and the supplied 0.2 mm elephant-foot compensation. If it binds throughout, measure the coupon and calibrate extrusion before printing the full enclosure. Keep global XY size compensation at zero so the connector openings, PCB positions and wall thicknesses stay at their designed dimensions. Do not force the PETG hook if it will not seat.

Nozzle diameter alone does not determine clearance: print orientation, material, flow and calibration also affect fit. See [Prusa's tolerance guidance](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) and [elephant-foot compensation](https://help.prusa3d.com/article/elephant-foot-compensation_114487).
