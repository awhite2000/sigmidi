# SIGMIDI Foot Controller v0.1

## Bill of materials - one completed controller

Preferred build: **Left**, with electronics on the left and modular extensions to the right. The Right variant uses the same purchased electrical parts; select its matching printed files. Quantities are installed quantities, excluding spares. Prices, stock and shipping are not included.

| Profile | Installed switches N | Pair extensions | Base M2x6 screws | Printed enclosure pieces |
|---|---|---|---|---|
| Modular 4 | 4 | 0 | 4 | 3 |
| Modular 6 | 6 | 1 | 6 | 5 |
| Modular 8 | 8 | 2 | 8 | 7 |
| Modular 10 | 10 | 3 | 10 | 9 |
| Main 10, fixed split chassis | 10 | Not applicable | 8 | 4 |

Use **N** below for the chosen installed switch count. **AR** means as required. Optional feature quantities apply only when that feature is fitted. Parts inside purchased boards are not itemized; no separate MCU, ADC, expander or BLE radio is required.

## 1. Required control electronics

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| E01 / U1 | 1 piece | **DFRobot DFR1075**. FireBeetle 2 ESP32-C6; current design uses V1.1 geometry, 25.4 x 60 mm PCB. |
| E02 / U2 | 1 piece | **Waveshare 24382**. 1.69inch LCD Module; ST7789V2; 240 x 280 native / 280 x 240 landscape; 31.5 x 39 mm PCB. |
| E03 / SW11 | 1 piece | **Rotary encoder with push switch**. Passive quadrature, 20 detents/revolution; normally-open click; 15 x 15 mm body. |
| E04 / SW1-SW10 | N piece | **Momentary footswitch**. Normally open, non-latching; 12 mm mounting thread; 30 x 13 x 15 mm body; shaft offset 9 mm from short end. |
| E05 / R7 | 1 piece | **10 kOhm ladder pull-up**. 1% metal-film, through-hole; 0.25 W procurement choice. |
| E06 / R8 | 1 piece | **20 kOhm idle resistor**. 1% metal-film, through-hole; 0.25 W procurement choice. |
| E07 / R9-R18 | N piece | **1 kOhm ladder sections**. 1% metal-film, through-hole; 0.25 W procurement choice. |
| E08 / C5 | 1 piece | **100 nF ladder filter capacitor**. Ceramic, through-hole; >=10 V rating (50 V is suitable). |

All discrete resistors are 1% metal-film; 0.25 W through-hole is a practical procurement choice. Higher precision is optional. The 100 nF capacitor belongs to the switch ladder. Four 1 kOhm sections are in the base; each two-switch extension adds two. No resistor terminates the final tap.

<!-- page -->

# 2. Feature-dependent electronics

## Two passive pedal inputs

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| E09 / J2 | 1 piece | **Amphenol ACJS-MHDC**. One dual 6.35 mm switched TRS socket housing; fitted horizontally in chassis. |
| E10 / R21, R31 | 2 piece | **10 kOhm pedal bias resistors**. 1% metal-film, through-hole; 0.25 W. |
| E11 / R20, R30 | 2 piece | **5.1 kOhm pedal reference resistors**. 1% metal-film, through-hole; 0.25 W. |

Fit J2 once for one or both pedal inputs. Each populated input adds one 10 kOhm bias resistor and one 5.1 kOhm reference resistor. The table fits both inputs. Across the complete two-input build there are **three 10 kOhm resistors total**, including R7 on page 1. The external pedals are passive; no active interface or extra ADC board is fitted.

## Optional 9 V power input

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| E12 / J1 | 1 piece | **Barrel power socket**. 5.5 x 2.1 mm; external thread diameter 8 mm, length 8 mm; 4 mm flange/body + 6 mm terminals = 18 mm total. |
| E13 / U3 | 1 piece | **Pololu S13V10F5 #4083**. 5 V, nominal 1 A step-up/step-down regulator; about 8.9 x 12.1 mm. |
| E14 / C1 | 1 piece | **47 uF input capacitor**. Polarized electrolytic; 35 V minimum; compact radial package. |

J1, U3 and C1 are omitted as a group in a USB-only electrical build. The existing chassis still contains their openings and mount features. Pololu 4083 is a **buck-boost** module, not just a step-down regulator; Kamami's 1178565 listing refers to this part. The 1 A rating is shared by controller, display and optional LEDs and is subject to thermal conditions. [S3]

## Optional LED feedback

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| E15 / LED1-LED10 | N piece | **Pololu 2535**. 5 mm diffused through-hole RGB pixel with integrated WS2811; 5 V; four leads DIN/5V/GND/DOUT. |

Pololu 2535 is sold as a **10-pack**: buy one pack for any single 4-10 switch build and fit N LEDs. The current chain has LEDs, +5 V, GND and data wiring only; no extra driver, buffer, series resistor or chain capacitor is specified. C1 is the converter input capacitor, not an LED-chain component. Direct 3.3 V data into 5 V LEDs requires verification with the actual batch and harness. [S4]

<!-- page -->

# 3. Mounting hardware

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| H01 | See p.1 | **Base screws**. M2 x 6 mm countersunk. |
| H02 | 4 piece | **Display screws**. M2 x 5 mm countersunk. |
| H03 | 4 piece | **MCU mounting screws**. M1.6; head style and under-head length to confirm before ordering. |
| H04 | N set | **Footswitch mounting hardware**. Matching nuts and washer set supplied for each selected footswitch. |
| H05 | 1 piece | **Encoder knob**. 15 mm diameter x 5 mm height; bore matched to selected shaft. |
| H06 | 1 set | **Encoder panel hardware**. Matching retaining nut and washer. |
| H07 | 1 set | **TRS panel hardware**. Two nickel nuts and two black fiber washers for ACJS-MHDC. |
| H08 | 1 piece | **DC socket retaining nut**. Matching 8 mm thread; 2 mm thick. |

**Avoid double counting included hardware.** H04 is one complete footswitch hardware set per switch; the reference drawing shows two nuts and one washer. H06 is the encoder's nut/washer set. H07 is J2's two nickel nuts and two fiber washers, shown in the attached manufacturer drawing. H08 is J1's 2 mm retaining nut. Check the seller's package contents before ordering any of these separately.

**H01 quantity:** main enclosure = eight. Modular = four on the electronics base plus two per added pair. The cap has an integral floor and no base screws. Use countersunk heads for H01 and H02. No separate heat-set inserts or metal standoffs are specified in the current design.

**Display fit:** four M2x5 screws pass through the printed hollow mounts into the factory blind studs. Nominal engagement is 1.39 mm; confirm head seating and usable stud depth on the delivered display. Do not substitute the base's M2x6 screws for the display screws.

**MCU fit remains to confirm:** the four M1.6 reference screw bodies have about 7.2 mm overall modeled height including the head. The project does not define an orderable under-head length or head standard. Measure PCB thickness and usable printed pilot depth, then select the length. Do not order from the 7.2 mm overall dimension.

**Control fit remains to confirm:** no exact footswitch or encoder manufacturer SKU is selected. Match the specified switch body and shaft offset, actuator height, encoder bushing length through the 3 mm roof, shaft form and knob bore. The encoder's 6 mm shaft and 8 mm body height are CAD assumptions. These checks determine the final orderable parts, not a change to the enclosure geometry.

<!-- page -->

# 4. Printed enclosure and assembly materials

Choose **one enclosure family**, not both. Main 10 is 350 mm wide; modular widths are 164.85 / 229.85 / 294.85 / 359.85 mm for 4 / 6 / 8 / 10 switches. The ten-switch modular enclosure is wider than the fixed main enclosure.

| ID / print item | Mod 4 | Mod 6 | Mod 8 | Mod 10 | Main 10 |
|---|---|---|---|---|---|
| P01 Electronics upper shell | 1 | 1 | 1 | 1 | 1 |
| P02 Electronics base | 1 | 1 | 1 | 1 | 1 |
| P03 Main outer upper shell | 0 | 0 | 0 | 0 | 1 |
| P04 Main outer base | 0 | 0 | 0 | 0 | 1 |
| P05 Repeatable pair upper | 0 | 0 | 1 | 2 | 0 |
| P06 Cap-adjacent pair upper | 0 | 1 | 1 | 1 | 0 |
| P07 Universal pair base | 0 | 1 | 2 | 3 | 0 |
| P08 Integral-floor end cap | 1 | 1 | 1 | 1 | 0 |

## Preferred Left print selection

Main uses one each of **shell-left, shell-right, base-left, base-right** in design/fusion/mirrored/main/. Modular uses the electronics shell/base and one **right-cap**; every extension uses the universal **pair-base**. Upper-shell labeling depends on position:

| Modular total | Repeatable upper(s) | Cap-adjacent upper |
|---|---|---|
| 4 | None | None |
| 6 | None | pair-shell-at-right-cap-C |
| 8 | pair-shell-C | pair-shell-at-right-cap-D |
| 10 | pair-shell-C, pair-shell-D | pair-shell-at-right-cap-E |

Use the matching files in design/fusion/mirrored/modular/. Right builds use design/fusion/print/ and design/fusion/modular/, a left end cap and their matching labeled uppers. The print guides are authoritative for filenames and orientations. Print only designated shell/base/cap solids, not modeled electronics or reference hardware.

## Stock and consumables

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| M01 | AR mass | **PETG filament**. For the selected supplied enclosure print files. |
| M02 | AR set | **PETG-compatible adhesive**. For upper joint chain and removable-base joint chain. |
| M03 | 4 piece | **Non-slip feet / clearance pads**. Maintain >=3 mm open space beneath floor vents. |

Current supplied profiles use Prusa MK3S+, PETG, a 0.6 mm nozzle and 0.3 mm layers. A 1 kg filament spool is a stock allowance, not an estimate of consumed mass. Slice the actual selected parts with supports, brim and fit coupons. Mounts, converter spring clips, positioning ribs, support pins and glue lands are integral printed features, not separate purchased parts.

<!-- page -->

# 5. Wiring and external accessories

## Harness materials

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| W01 | 1 piece | **LCD cable**. GH1.25, 8-pin mating cable; verify orientation and signal labels. |
| W02 | AR length | **Signal hookup wire**. Stranded, insulated 26-28 AWG; assorted purpose colors. |
| W03 | AR length | **Supply/return wire**. Stranded, insulated 22-24 AWG. |
| W04 | AR set | **Insulated solder support**. Small perfboard or insulated solder strip for discrete resistors/capacitors. |
| W05 | AR set | **Insulation and strain relief**. Heat-shrink, small ties/anchors and insulating sleeves. |

Plan about **5 m total of assorted signal wire** and **2 m total supply/return wire** for stock. These are procurement allowances, not measured cut lengths. Keep purpose colors consistent, insulate solder joints, and leave service slack between upper ports and base electronics. Connector families for optional detachable section harnesses and a carrier-board outline are not finalized. Direct solder wiring is the documented electrical baseline; do not assume a custom PCB exists.

## Equipment outside the enclosure

| ID / references | Fitted qty | Part and specification |
|---|---|---|
| A01 | 1 piece | **USB-C data cable**. Suitable USB host/source end. |
| A02 | 1 piece | **USB 5 V source**. Capacity for measured controller and any USB-powered LED load. |
| A03 | 1 piece | **9 V DC adapter / pedalboard output**. Center-negative 5.5 x 2.1 mm; >=1 A procurement allowance. |
| A04 | 2 piece | **Passive continuous pedal**. Variable resistor or potentiometer, up to 10 kOhm. |
| A05 | 1 piece | **BLE MIDI DIN dongle**. Central-role support and third-party peripheral compatibility. |

A04 allows up to two passive pedals; zero or one is also valid. A05 is needed for a direct HX Stomp DIN connection, not for connection to an iPad BLE MIDI application. The dongle must be able to act as a central for a third-party peripheral; interoperability has not been bench qualified. HX Stomp, iPad, printer, tools and their own power supplies are not included in the controller BOM.

USB and 9 V sources are alternative power options. Choose each supply for the complete measured load. Ten Pololu 2535 LEDs draw about 0.5 A at full white before the controller/display load. A higher-current input adapter does not increase the converter's 5 V output/thermal rating. Confirm how the LED 5 V branch is powered in a USB-only build; do not join independent positive supply outputs. [S3, S4]

<!-- page -->

# 6. Procurement notes and traceability

## Before placing the order

| Item | Required check |
|---|---|
| DFRobot DFR1075 | Current design uses V1.1 mounting and USB-C geometry. Compare a newer board revision before buying. |
| Waveshare 24382 | Non-touch 1.69inch LCD Module; verify rear M2 studs and GH1.25 8-pin cable. Do not substitute a similar touch display. |
| Footswitch / encoder | Exact supplier SKUs remain open; match the dimensional and contact requirements on pages 1 and 3. |
| J1 power socket | Match 8 mm thread, 8 mm threaded length, 18 mm total envelope and 2 mm nut; flange and nut outside diameters still require fit confirmation. |
| MCU screws | M1.6 quantity is fixed at four; select head style and under-head length from actual engagement measurements. |
| Bundled hardware | Check cable, header, nuts and washers already supplied with the boards and controls. Do not buy duplicate sets. |

## Quantity and source checks

The existing maximum electrical BOM/netlist contains **44 distinct component instances**: three purchased boards, two socket assemblies, one encoder, ten footswitches, sixteen resistors, two capacitors and ten LEDs. This is the fully fitted ten-switch case, including both pedal inputs, 9 V power and LEDs. The similarly sized CSV line count is coincidental: CSV rows also include grouped hardware, printed parts and external accessories.

For all optional circuits fitted, electrical instance totals are **26 / 32 / 38 / 44** at 4 / 6 / 8 / 10 switches. Omitting LEDs subtracts N; omitting 9 V input subtracts three (J1/U3/C1). Omitting the complete pedal interface subtracts five (J2 and four resistors). Printed/hardware quantities are separate. The BOM generator checks all 44 reference designators against both electrical exports and verifies the main 8/4/4 base/display/MCU screw counts against the CAD body inventory.

## References

**[S1]** [DFRobot DFR1075 documentation](https://wiki.dfrobot.com/dfr1075/): board identity and manufacturer dimensions. **[S2]** [Waveshare 24382 documentation](https://www.waveshare.com/wiki/1.69inch_LCD_Module): module, connector and mechanical specification.

**[S3]** [Pololu S13V10F5 #4083](https://www.pololu.com/product/4083): regulator, current/thermal limits and input transient capacitor guidance. **[S4]** [Pololu 2535](https://www.pololu.com/product/2535): 10-pack, supply and LED package.

Local basis: design/electrical/bom.csv and netlist.json; design/fusion/mirrored/layout.json; enclosure assembly guides; docs/hardware.md and power.md; and design/fusion/datasheets/double-trs-ACJS-MHDC.pdf. The manufacturer's TRS drawing shows the included nuts/washers and optional PCB support hole; no extra saddle screw is specified in this assembly.

Prepared 29 October 2026 for SIGMIDI v0.1. Existing schematic, firmware and Fusion geometry are unchanged. Values and CAD fit describe the current prototype; purchased-part fit, direct LED drive, power/thermal performance and physical assembly still require bench checks. Edit docs/bom-items.json and rerun scripts/build_bom.py to refresh the PDF, Markdown and shopping CSV.
