# SIGMIDI Foot Controller v0.1 — Power

The controller accepts USB power or **9 V DC, center-negative**, through a **5.5 × 2.1 mm barrel plug** and **Pololu S13V10F5 #4083** regulator (Kamami listing 1178565). The regulator supplies 5 V with a nominal **1 A total output limit**. Its module input range is 2.8–22 V; label the enclosure input 9 V DC, center-negative. [Manufacturer specifications](https://www.pololu.com/product/4083).

## Wiring

```text
Barrel sleeve (+9 V) -------- Nano VIN (6–21 V input)
          +----------------- Pololu VIN
Barrel centre (negative) ---- Nano GND / Pololu GND / peripheral GND
Pololu VOUT (+5 V) ---------- optional LED +5 V rail only
Nano 3V3 ------------------- LCD, ladder and pedal references
Nano USB VBUS -------------- 100k / 150k divider to A4 / GPIO11
```

The Nano is powered by USB-C or 9 V at VIN. Do not feed the converter's 5 V output to Nano VIN (specified for 6–21 V), or connect it to USB VBUS. VBUS supplies USB power and is not driven by the Nano when VIN is the source. Shared ground is required. The VBUS divider senses the host connection during VIN-powered operation; see [Nano wiring](hardware.md). The Nano has no battery charger.

Identify socket terminals by continuity with a matching plug. Leave any unused switched contact disconnected. Insulate lugs and provide slack between the socket on the upper shell and the converter on the removable base. Route supply/return together and away from analog sense wiring.

The regulator has no reverse-input-polarity protection. For long supply leads or hot-plug transients, Pololu specifies at least 33 µF, rated at least 35 V, near VIN/GND. See the manufacturer's protection and transient notes linked above.

## Load budget

The Pololu 1 A output supplies the LED rail; the Nano regulates its own VIN supply for the MCU, LCD and analog circuits. Its continuous capacity depends on input voltage, airflow and temperature. Ten Pololu 2535 LEDs draw approximately 0.5 A at full white. Default 64/255 brightness reduces average load, but wiring and supply selection must accommodate peak current. Validate Wi-Fi and full-white/startup load. No battery charger is included.

Branch LED +5 V and GND directly at the supply distribution point. Do not route LED current through the Nano header or join independent positive outputs. USB-only operation does not imply power on the converter's LED rail. [LED wiring](leds.md).

## Socket and converter placement

Left electronics are on the left; Right electronics are on the right. Positions below use each assembly's native millimetre coordinates.

| Feature | Left | Right |
|---|---|---|
| Rear DC socket centre | X140, Z0 | X210, Z0 |
| Converter centre, approximate | X123.968 | X226.033 |
| Converter PCB underside | Z−11 | Z−11 |
| Lowest-component clearance to floor | 8.65 mm | 8.65 mm |

The socket bore is Ø8.4 mm for an Ø8 mm thread. Its axial stack is **18 mm**: 8 mm threaded length, 4 mm flange/body and 6 mm terminals. A 2 mm nut sits outside the 2 mm rear panel. CAD reserves Ø12 mm flange and 13 mm nut across flats; confirm those envelopes and lug positions against the purchased socket.

The [converter STEP](../design/fusion/datasheets/pololu-4083.step) and [drawing](../design/fusion/datasheets/pololu-4083-dimensions.pdf) describe its approximately 8.9 × 12.1 × 4.2 mm double-sided assembly, with ±0.3 mm board-edge tolerance.

## Clip mount and ventilation

Three bare-edge seats and two opposing PETG springs support the converter. Springs are 4.8 mm wide, 1.6 mm thick and 13.216 mm tall above the reinforced floor, with 0.8 mm root gussets at 45°. Hook overlap is 0.4 mm, top clearance 0.2 mm and insertion travel about 0.6 mm outward per leaf. Solder wires first; spread the leaves, lower the PCB onto its seats and release. Press only on bare edges and keep strain off the springs.

The electronics base has six inlet slots around the converter and seven in the MCU mounting region, each 2.4 mm wide. The floor is 3 mm thick across their rectangular zone and a 3 mm border. Twelve rear exhaust slots form three columns and four rows; their highest edge leaves a 7.6 mm solid top rim. An internal rib with 45° side chamfers runs from roof to base between columns and joins the USB-pocket chamfer.

Rear vents print with **0.6 mm internal membranes**. Remove all twelve films and clean the openings before operation; finished rear open area is 380.16 mm². Keep grilles clear of foam, tape and wiring, and provide at least **3 mm air space under the base**. The ventilated enclosure is not sealed against dust or liquid.

Before removing the populated base, disconnect power, release the Nano from its four integral base posts and withdraw its USB-C connector from the pocket partition. Physical clip retention, fatigue and operating temperatures require testing with the intended PETG and electrical load.
