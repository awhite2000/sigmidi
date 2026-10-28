"""Validate and package only the current main/modular CAD and print parts."""
from pathlib import Path
import hashlib,json,re,zipfile
P=Path(__file__).resolve().parent
REV='display_m2x5'
display= json.loads((P/'display-m2x5.json').read_text())
assert display['screw_length_mm']==5 and display['main_and_modular_updated']
assert not display['physical_collisions'] and not display['wire_corridor_collisions']
assert max(display['outside_display_post_envelopes_bidirectional_difference_mm3'])<.001
display_slice=json.loads((P/'display-m2x5-slice.json').read_text())
assert display_slice['all_probes_have_two_or_more_tracks'] and display_slice['all_access_centers_open']
assert display_slice['STL_sha256']==hashlib.sha256((P/'print/base-right.stl').read_bytes()).hexdigest()
display_section=json.loads((P/'display-m2x5-section.json').read_text())
assert display_section['STL_sha256']==display_slice['STL_sha256']
assert display_section['image_sha256']==hashlib.sha256((P/'display-m2x5-section.png').read_bytes()).hexdigest()
label_variants=['pair-shell-D','pair-shell-at-cap-C','pair-shell-at-cap-E']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snug=read(P/'snug-06-tolerances.json')
assert snug['nozzle_mm']==.6 and snug['hook_clearance_normal_mm']==snug['locator_wall_clearance_mm']==.2
assert not any(snug[k] for k in ['physical_collisions','wire_collisions','assembly_collisions'])
section=read(P/'snug-fit-sections.json')
assert section['image_sha256']==sha(P/section['image'])
for n,h in section['STL_sha256'].items():assert sha(P/n)==h
rib_fit=read(P/'positioning-rib-refinement.json')
assert rib_fit['front_and_rear_rib_thickness_mm']==1.8 and rib_fit['all_models_updated']
assert not any(rib_fit[k] for k in ['physical_collisions','wire_collisions','assembly_collisions'])
rib_slice=read(P/'positioning-rib-slice.json')
assert rib_slice['all_probes_have_two_or_more_tracks'] and rib_slice['nozzle_mm']==.6
for r in rib_slice['STL_checks']:assert r['sha256']==sha(P/r['path'])
wall=read(P/'enclosure-wall-reinforcement.json')
assert wall['obsolete_TRS_relief']['restored_wall_mm']==2
assert wall['obsolete_TRS_relief']['restored_nominal_profile_missing_mm3']<.001
audit=read(P/'wall-thickness-audit.json')
assert audit['unique_print_parts']==11 and audit['unresolved_sample_count']==0
for row in audit['parts']:assert row['STL_sha256']==sha(P/(row['part']+'.stl'))
assert wall['blind_cap_thickness_mm']==2 and wall['cap_front_flat_wall_mm']>=2
assert wall['floor_slit_closed'] and wall['all_changed_parts_single_connected_solids']
assert wall['original_material_removed_mm3']==0 and wall['all_component_positions_and_mounting_hole_axes_unchanged']
assert not any(wall[k] for k in ['body_collisions','wire_collisions','assembly_collisions'])
wall_slice=read(P/'enclosure-wall-slice.json')
assert wall_slice['all_checks_passed']
for row in wall_slice['STL_checks']:assert row['sha256']==sha(P/row['path'])
upper=read(P/'upper-corner-walls.json')
assert upper['nominal_repaired_wall_mm']==2 and upper['all_changed_parts_single_connected_solids']
assert upper['exterior_shape_and_bounds_unchanged'] and upper['screw_bosses_pilots_base_seating_and_shell_joints_unchanged']
assert all(r['missing_reference_wall_after_mm3']<.001 and r['original_material_removed_mm3']<.001 for r in upper['parts'])
assert not any(upper[k] for k in ['body_collisions','wire_collisions','assembly_collisions'])
upper_slice=read(P/'upper-corner-slice.json')
assert upper_slice['all_repaired_probes_have_at_least_two_tracks']
assert upper_slice['toolpath_comparison_sha256']==sha(P/upper_slice['toolpath_comparison_image'])
for row in upper_slice['parts']:
    assert row['STL_sha256']==sha(P/row['STL_path'])
wide=read(P/'wide-pololu-clips.json')
assert wide['spring_leaf_width_mm']==4.8 and wide['spring_leaf_thickness_mm']==1.6
assert wide['root_gussets_exposed_above_reinforced_floor'] and wide['all_13_floor_vents_unchanged']
assert wide['original_material_removed_mm3']<.001 and wide['base_floor_material_changed_mm3']<.001
assert wide['main_and_modular_updated'] and wide['all_parts_single_connected_solids']
assert not any(wide[k] for k in ['body_collisions','component_clearances_below_3mm','wire_collisions','outward_clip_sweep_collisions','board_insertion_collisions','assembly_collisions','blocked_floor_vents'])
corner=read(P/'base-corner-repair.json')
assert corner['remaining_unintended_gap_mm3']<.001 and corner['original_material_removed_mm3']<.001
assert corner['single_connected_solid'] and corner['main_and_modular_updated'] and not corner['assembly_collisions']
assert corner['floor_thickness_mm']==2 and corner['screw_bores_countersinks_vents_mounts_and_joints_unchanged']
labels=read(P/'recessed-switch-labels.json')
assert labels['actual_outline_height_mm']==8 and labels['inset_depth_mm']==.8 and labels['minimum_remaining_top_mm']==2.2
assert labels['all_changed_shells_single_connected_solids'] and labels['all_glyphs_wholly_in_flat_roof'] and labels['all_pockets_backed_by_2_2mm_roof']
assert labels['seam_and_joint_material_removed_mm3']==0 and labels['all_other_components_and_base_parts_unchanged']
assert labels['minimum_LED_flange_clearance_X_mm']>=3
mounts=read(P/'extra-right-base-screws.json')
assert mounts['right_section_base_screw_count']==4 and mounts['main_total_base_screws']==8
assert mounts['pilot_diameter_mm']==1.9 and mounts['base_clearance_diameter_mm']==2.6
assert mounts['minimum_mount_to_hardware_clearance_lower_bound_mm']>=3
assert not any(mounts[k] for k in ['physical_collisions','clearances_below_3mm','wire_collisions','new_screw_intersections','assembly_collisions'])
assert mounts['upper_original_material_removed_mm3']<.001 and mounts['base_glue_lip_material_removed_mm3']<.001
membrane=read(P/'rear-vent-membranes.json')
assert membrane['membrane_thickness_mm']==.6 and membrane['membrane_count']==12 and membrane['cavity_projection_mm']==0
assert membrane['rear_as_printed_open_area_mm2']==0 and membrane['rear_open_area_after_membrane_removal_mm2']==380.16
assert max(membrane['virtual_removal_bidirectional_BRep_difference_mm3'])<.001
assert not any(membrane[k] for k in ['body_collisions','component_clearances_below_3mm','wire_collisions'])
membrane_slice=read(P/'rear-vent-membrane-slice.json')
assert membrane_slice['all_12_membranes_have_continuous_toolpaths'] and membrane_slice['STL_sha256']==sha(P/'print/shell-right.stl')
height=read(P/'full-height-rear-rib.json')
assert height['rib_projection_inward_mm']==2 and height['base_seating_Z_mm']==-22
assert height['lower_leg_offset_X_mm']==0 and height['continuous_straight_side_chamfers']
assert height['merged_with_existing_USB_pocket_chamfer'] and height['USB_socket_1mm_envelope_preserved']
assert height['base_contact_probe_volume_mm3']>.025 and height['assembled_base_overlap_mm3']<.001
assert height['minimum_component_clearance_lower_bound_mm']>=1 and height['minimum_other_component_clearance_lower_bound_mm']>=3
assert not any(height[k] for k in ['body_collisions','component_clearances_below_required_minimum','wire_collisions','blocked_passages','assembly_collisions'])
floor=read(P/'base-vent-reinforcement.json')
assert floor['added_thickness_mm']==1 and floor['border_mm']==3 and floor['reinforced_floor_thickness_mm']==3
assert floor['slot_count']==13 and floor['existing_floor_openings_and_bores_preserved']
assert not any(floor[k] for k in ['blocked_slots','body_collisions','component_clearances_below_3mm','wire_collisions','assembly_collisions'])
assert floor['minimum_component_clearance_lower_bound_mm']>=3
ribs=read(P/'rear-grille-ribs.json')
assert ribs['rib_count']==1 and ribs['rib_projection_inward_mm']==2 and ribs['chamfer_angle_degrees']==45
assert not ribs['body_collisions'] and not ribs['component_clearances_below_required_minimum'] and not ribs['blocked_passages']
assert ribs['minimum_component_clearance_lower_bound_mm']>=1 and ribs['minimum_other_component_clearance_lower_bound_mm']>=3
assert ribs['slot_count']==12 and ribs['slots_per_column']==4 and ribs['exterior_envelope_unchanged'] and ribs['original_nine_slots_preserved']
raised=read(P/'raised-rear-vents.json')
assert raised['rear_pattern_raise_mm']==17 and raised['slot_count']==9
assert not any(raised[k] for k in ['restored_skin_component_collisions','vent_to_component_clearances_below_3mm','blocked_passages'])
assert raised['rear_top_solid_band_mm']>=7
assert raised['minimum_vent_to_switch_body_AABB_clearance_mm']>=3
assert raised['minimum_vent_to_hardware_clearance_lower_bound_mm']>=3
expanded=read(P/'expanded-vents.json')
assert expanded['extra_rear_rows']==2 and expanded['minimum_slot_to_anchor_clearance_lower_bound_mm']>=3
assert expanded['USB_pocket_material_removed_mm3']<.001 and max(expanded['unintended_added_material_mm3'])<.001
cooling=read(P/'ventilated-clip.json')
assert not any(cooling[k] for k in ['body_collisions','component_clearances_below_3mm','wire_collisions','assembly_collisions','outward_clip_sweep_collisions'])
assert cooling['anchor_material_removed_mm3']<.001 and cooling['USB_pocket_material_removed_mm3']<.001
assert cooling['component_to_inside_floor_clearance_mm']>8 and cooling['positive_lateral_locators']
assert not cooling.get('locator_body_collisions') and not cooling.get('locator_continuous_20mm_withdrawal_sweep_collisions')
clip_slice=read(P/'clip-slice-detail.json')
assert clip_slice['base_support_extrusion_mm']==0
assert clip_slice['expected_leaf_width_mm']==wide['spring_leaf_width_mm']
assert all(min(rows.values())>=3.4 for rows in clip_slice['extrusion_endpoint_X_spans_mm_by_layer'].values())
assert clip_slice['STL_sha256']==sha(P/'print/base-right.stl')
power=read(P/'aux-power.json')
assert power['total_socket_length_mm']==18 and power['input_V_DC']==9
assert not any(power[k] for k in ['body_collisions','component_clearance_lower_bounds_below_3mm','wire_collisions','assembly_collisions'])
assert read(P/'power-layout-verification.json')['all_other_existing_component_geometry_and_transforms_identical']
assert read(P/'power-geometry-verification.json')['main_and_modular_electronics_print_parts_identical']
fit=read(P/'straight-base-lips.json')
assert not fit['base_dovetails'] and fit['same_pair_base_for_all_positions']
assert not any(fit[k] for k in ['physical_collisions','wire_collisions','assembly_collisions'])
for folder,names in [(P/'print',['shell-left','shell-right','base-left','base-right','fit-coupon-left','fit-coupon-right']),(P/'modular',['pair-shell','pair-base','pair-shell-at-cap','left-cap','electronics-shell','electronics-base','fit-coupon-left','fit-coupon-right']+label_variants)]:
    meshes=read(folder/'mesh-audit.json')
    assert len(meshes)==(6 if folder.name=='print' else 7)
    for row in meshes:
        assert row['volume_mm3']>0
        assert all(row[k]==0 for k in ['boundary_edges','nonmanifold_edges','inconsistent_winding_edges','degenerate_triangles'])
    slice_report=read(folder/'slice-verification.json')
    assert slice_report['nozzle_mm']==.6 and slice_report['layer_mm']==.3
    slices={r['part']:r for r in slice_report['parts']}
    assert set(names)==set(slices)
    for n in names:
        assert slices[n]['slice_exit_code']==0
        with zipfile.ZipFile(folder/(n+'.3mf')) as z:
            assert z.testzip() is None
            assert b'nozzle_diameter = 0.6' in z.read('Metadata/Slic3r_PE.config')
for target,source in {'electronics-shell':'shell-right','electronics-base':'base-right','fit-coupon-left':'fit-coupon-left','fit-coupon-right':'fit-coupon-right'}.items():
    for ext in ['stl','3mf']:assert (P/'modular'/f'{target}.{ext}').read_bytes()==(P/'print'/f'{source}.{ext}').read_bytes()
for n in ['midi-foot-chassis','modular/midi-foot-modular']+['modular/'+v for v in label_variants]:
    assert (P/(n+'.step')).read_text().count('MANIFOLD_SOLID_BREP(')>(0 if n.split('/')[-1] in label_variants else 200)
    with zipfile.ZipFile(P/(n+'.f3d')) as z:assert z.testzip() is None
for image in read(P/'render-manifest.json')['images']:
    assert sha(P/image['path'])==image['sha256']

def seconds(s):return sum(int(n)*{'h':3600,'m':60,'s':1}[u] for n,u in re.findall(r'(\d+)([hms])',s))
def estimates(folder,qty):
    sl={r['part']:r for r in read(folder/'slice-verification.json')['parts']}
    exports={r['name']:r for r in read(folder/'print-export.json')['parts']}
    text=['| Part | Quantity | Print size X × Y × Z | Estimated time each |','|---|---:|---|---|']
    for n,q in qty.items():
        row=exports.get(n)
        if row is None:
            alias={'electronics-shell':'shell-right','electronics-base':'base-right'}[n]
            row=next(r for r in read(P/'print/print-export.json')['parts'] if r['name']==alias)
        dims=' × '.join(f'{v:.2f}'.rstrip('0').rstrip('.') for v in row['size_mm'])
        text.append(f"| {n} | {q} | {dims} mm | {sl[n]['estimated_time']} |")
    mass=sum(float(sl[n]['filament_g'])*q for n,q in qty.items());t=sum(seconds(sl[n]['estimated_time'])*q for n,q in qty.items())
    text+=['',f'Estimated total: **{t//3600}h {(t%3600)//60}m, {mass:.0f} g**, including brims and supports, excluding fit coupons. Separate prints with the supplied PETG profile.','']
    rp=folder/'README.md';rp.write_text(rp.read_text().split('## Current slicer estimates')[0].rstrip()+'\n\n## Current slicer estimates\n\n'+'\n'.join(text))
    return {'estimated_mass_g':mass,'estimated_seconds':t}

main_names=['shell-left','shell-right','base-left','base-right','fit-coupon-left','fit-coupon-right']
mod_names=['pair-shell','pair-base','pair-shell-at-cap','left-cap','electronics-shell','electronics-base','fit-coupon-left','fit-coupon-right']+label_variants
summary={'right_section_base_screws':4,'main_base_screws':8,'modular_8_switch_base_screws':8,'revision':REV,'universal_pair_base':True,'base_dovetails':False,'checks':'native solid/assembly/wiring, closed manifold meshes, PrusaSlicer 0.6mm PETG, STEP solids, F3D and ZIP integrity'}
summary['display_mount']={'screw':'M2x5 countersunk','seat_Z_mm':display['new_recessed_head_seat_Z_mm'],'nominal_stud_engagement_mm':display['nominal_stud_engagement_mm'],'display_glass_Z_mm':0}
summary['wall_audit']={'unique_parts':11,'surface_samples':audit['total_samples'],'toolpath_checks':len(wall_slice['checks']),'blind_screw_cap_mm':2,'modular_cap_front_wall_mm':wall['cap_front_flat_wall_mm'],'left_floor_slit_closed':True,'old_TRS_relief_closed':True,'exterior_and_component_positions_preserved':True}
summary['snug_fit']={'nozzle_mm':.6,'hook_normal_clearance_mm':.2,'locator_wall_clearance_mm':.2,'print_joint_coupons_first':True}
summary['positioning_ribs']={'thickness_mm':1.8,'height_mm':3,'lead_in_mm':.5,'joined_clear_gaps':4,'rib_geometry_retained':True}
summary['pololu_spring_leaves']={'count':2,'width_mm':4.8,'bending_thickness_mm':1.6,'root_gusset_mm':.8,'outward_stroke_mm':.6}
summary['main']=estimates(P/'print',{n:1 for n in main_names[:4]})
summary['modular_8_switches']=estimates(P/'modular',{'pair-shell':1,'pair-shell-at-cap':1,'pair-base':2,'left-cap':1,'electronics-shell':1,'electronics-base':1})

def package(folder,archive,names,extra):
    entries=[(folder/f'{n}.{ext}',f'{n}.{ext}') for n in names for ext in ['stl','3mf']]
    entries += [(folder/n,n) for n in ['README.md','mk3s-petg-06.ini','print-export.json','mesh-audit.json','slice-verification.json','straight-base-lips.json']]
    entries+=extra
    import sys
    sys.path.insert(0,str(P.parents[1]/'scripts'))
    from documentation_bundles import portable_markdown
    portable_entries=[]
    for f,n in entries:
        if n.endswith('.md'):
            # The ladder guide's temporary file has no project-relative source context.
            source=P.parents[1]/'docs/resistor-ladders.md' if n=='resistor-ladders.md' else f
            target=Path(portable.name)/(folder.name+'-'+n.replace('/','-'))
            target.write_text(portable_markdown(source,n,entries))
            portable_entries.append((target,n))
        else:
            portable_entries.append((f,n))
    entries=portable_entries
    manifest={'revision':REV,'parts':names,'files':{n:sha(f) for f,n in entries},'no_obsolete_base_variant':True}
    (folder/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2))
    entries.append((folder/'delivery-manifest.json','delivery-manifest.json'))
    temp=folder/('current-'+archive)
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
        for f,n in entries:z.write(f,n)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        for f,n in entries:assert z.read(n)==f.read_bytes()
    temp.replace(folder/archive)
    return {'files':len(entries),'ZIP_bytes':(folder/archive).stat().st_size,'sha256':sha(folder/archive)}

for folder in [P/'print',P/'modular']:(folder/'straight-base-lips.json').write_bytes((P/'straight-base-lips.json').read_bytes())
main_extra=[(P/n,n) for n in ['midi-foot-chassis.f3d','midi-foot-chassis.step','assembled.png','panel-top.png','base-supports.png','cad-export.json']]
main_extra += [(P/'print'/n,n) for n in ['split-exploded.png','straight-base-lips.png','perimeter-ledge-detail.png','printing-orientations-supports.png','printing-orientations-supports.json']]
mod_extra=[(P/'modular'/n,n) for n in ['midi-foot-modular.f3d','midi-foot-modular.step','modular-design.json','modular-assembled.png','modular-exploded.png','pair-two-screw-mounts.png','new-parts-print-orientations.png','cap-floor-underside.png']]
mod_extra += [(P/'modular'/f'{name}.{ext}',f'{name}.{ext}') for name in label_variants for ext in ['f3d','step']]
mod_extra += [(P/'cad-export.json','cad-export.json'),(P/'print/straight-base-lips.png','straight-base-lips.png')]
power_extra=[(P/n,n) for n in ['display-m2x5.json','display-m2x5-section.png','display-m2x5-section.json','display-m2x5-slice.json','snug-06-tolerances.json','snug-fit-sections.png','snug-fit-sections.json','positioning-rib-refinement.json','positioning-rib-slice.json','enclosure-wall-reinforcement.json','wall-thickness-before.json','wall-thickness-audit.json','enclosure-wall-slice.json','blind-pilot-cap-section.png','upper-corner-walls.json','upper-corner-slice.json','upper-corner-wall-detail.png','upper-corner-toolpaths.png','wide-pololu-clips.json','base-corner-repair.json','base-corner-detail.png','recessed-switch-labels.json','switch-labels.png','aux-power.json','converter-carrier.json','power-layout-verification.json','power-geometry-verification.json','power-internal.png','power-rear.png','ventilated-clip.json','expanded-vents.json','raised-rear-vents.json','rear-grille-ribs.json','base-vent-reinforcement.json','full-height-rear-rib.json','straight-rear-rib.json','rear-vent-membranes.json','extra-right-base-screws.json','right-shell-base-mounts.png','rear-vent-membrane-slice.json','rear-vent-membrane-section.png','rear-ribs-internal.png','rear-rib-base-seat.png','clip-slice-detail.json','clip-mount.png','ventilation-base.png','ventilation-rear.png']]
guide=(P.parents[1]/'docs/power.md').read_text().replace('../design/fusion/datasheets/','datasheets/').replace('../design/fusion/ventilated-clip.json','ventilated-clip.json').replace('../design/fusion/raised-rear-vents.json','raised-rear-vents.json').replace('../design/fusion/rear-grille-ribs.json','rear-grille-ribs.json').replace('../design/fusion/base-vent-reinforcement.json','base-vent-reinforcement.json').replace('../design/fusion/full-height-rear-rib.json','full-height-rear-rib.json').replace('../design/fusion/straight-rear-rib.json','straight-rear-rib.json').replace('../design/fusion/rear-vent-membranes.json','rear-vent-membranes.json').replace('../design/fusion/extra-right-base-screws.json','extra-right-base-screws.json').replace('../design/fusion/wide-pololu-clips.json','wide-pololu-clips.json')
(P/'power.md').write_text(guide)
ledguide=(P.parents[1]/'docs/leds.md').read_text().replace('../design/fusion/datasheets/','datasheets/')
(P/'leds.md').write_text(ledguide)
(P/'printing-tolerances.md').write_text((P.parents[1]/'docs/printing-tolerances.md').read_text().replace('../design/fusion/',''))
power_extra += [(P/'power.md','power.md'),(P/'leds.md','leds.md'),(P/'printing-tolerances.md','printing-tolerances.md')]
import tempfile
portable=tempfile.TemporaryDirectory(prefix='midi-package-guides-')
ladderguide=Path(portable.name)/'resistor-ladders.md'
ladderguide.write_text((P.parents[1]/'docs/resistor-ladders.md').read_text().replace('../design/ladders/','ladders/'))
power_extra += [(ladderguide,'resistor-ladders.md')]
power_extra += [(f,'ladders/'+f.name) for f in sorted((P.parent/'ladders').glob('*')) if f.suffix in ['.svg','.csv']]
power_extra += [(P/'datasheets'/n,'datasheets/'+n) for n in ['pololu-4083.step','pololu-4083-dimensions.pdf','dfr1075-schematic-v11.pdf']]
main_extra += power_extra
mod_extra += power_extra
summary['auxiliary_power']={'input_V_DC':9,'polarity':'center-negative','regulator':'Pololu S13V10F5 / 4083','socket_overall_length_mm':18,'converter_to_floor_clearance_mm':cooling['component_to_inside_floor_clearance_mm'],'mount':'two PETG spring clips and three edge seats','floor_inlet_area_mm2':cooling['floor_open_area_mm2'],'rear_outlet_area_mm2':cooling['rear_open_area_mm2'],'rear_outlet_as_printed_mm2':0,'remove_all_12_rear_membranes_before_use':True}
summary['main_package']=package(P/'print','mk3s-petg-06-print-package.zip',main_names,main_extra)
summary['modular_package']=package(P/'modular','chainable-enclosure-mk3s-petg-06.zip',mod_names,mod_extra)
(P/'delivery-verification.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
