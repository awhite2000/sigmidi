# SIGMIDI Foot Controller v0.1 — Right main printing

This folder contains the **Right** ten-switch enclosure, with the display/encoder and electronics on the right. For the preferred Left enclosure, use the [Left manufacturing files](../mirrored/README.md).

## Parts and settings

Print one each of `shell-left`, `shell-right`, `base-left` and `base-right`. Oriented STL and editable 3MF files are provided, with the assembly in `../midi-foot-chassis.f3d` and `.step`.

Use **Prusa MK3S+, PETG, 0.6 mm nozzle, 0.3 mm layers**, 6 mm brim and the supplied `mk3s-petg-06.ini`. Shells print on their outer ends, seams upward, using automatic snug supports at 40°. Bases print outside-floor down, mounts upward, without supports. Print and test both fit coupons first. [Tolerance guide](../printing-tolerances.md).

The assembled body is 350 × 92 × 54 mm. The roof is 3 mm, side walls at least 2 mm and base 2 mm with local 3 mm vent reinforcement. Label recesses are 0.8 mm deep with 2.2 mm backing. The upper row sits 30 mm above the lower; switch pitch is 65 mm, stagger 32.5 mm and row spacing 53 mm.

## Assembly

1. Clean brims and supports. Remove all twelve 0.6 mm rear vent films. Open the 0.8 mm LED covers only for installed LEDs and finish their seats.
2. Lower the left upper shell vertically onto the right using the continuous hooked joint. Glue the joint after confirming fit; inclined clearance is 0.20 mm and exterior seam 0.25 mm.
3. Glue the base's straight butt seam using its 2 mm internal glue land. Align the outside floor surfaces on a flat reference.
4. Fit the display using four M2×5 countersunk screws through the hollow mounts. Check nominal 1.39 mm engagement in its blind factory studs. Fit the MCU with M1.6 hardware and the converter in its PETG clips.
5. Install controls and insulated wiring. LEDs sit below the switches with nominal 0.8 mm dome exposure. Keep the vent openings and removable-base interface clear.
6. Seat the shell on the base perimeter using its 1.8 mm positioning ribs. Attach with eight M2×6 countersunk screws. Base bores are Ø2.6 mm, countersinks Ø4.4 × 0.9 mm and shell pilots Ø1.9 × 6.5 mm.

The populated DFR1075 USB-C connector engages the pocket partition. Release the MCU from its mounts and withdraw the connector before lowering a populated base. Leave slack between the rear socket and base-mounted converter. Provide at least 3 mm free space below the floor vents.

## References

[Assembly](../assembled.png) · [Exploded parts](split-exploded.png) · [Print orientations/supports](printing-orientations-supports.png) · [Straight glue lips](straight-base-lips.png) · [Base perimeter seat](perimeter-ledge-detail.png) · [Power](../power.md) · [LEDs](../leds.md) · [Enclosure dimensions](../README.md).

Mesh, wall and slicer checks are supplied. Physical print fit, thermal performance and adhesive strength require validation.

## Current slicer estimates

| Part | Quantity | Print size X × Y × Z | Estimated time each |
|---|---:|---|---|
| shell-left | 1 | 52 × 92 × 193.65 mm | 6h 46m 20s |
| shell-right | 1 | 52 × 92 × 160.35 mm | 6h 20m 1s |
| base-left | 1 | 193.65 × 92 × 21 mm | 1h 56m 54s |
| base-right | 1 | 156.1 × 92 × 21 mm | 2h 3m 57s |

Estimated total: **17h 7m, 343 g**, including brims and supports, excluding fit coupons. Separate prints with the supplied PETG profile.
