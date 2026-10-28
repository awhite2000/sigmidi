"""Run through the configured Fusion MCP to archive the entire current design."""
import adsk.core,adsk.fusion,json,datetime,zipfile,hashlib

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
 assert d,'Open the current SIGMIDI design in Fusion before exporting.'
 root=d.rootComponent
 icon=root.attributes.itemByName('SIGMIDI','embossed_icon_25mm')
 assert icon,'Expected the latest embossed SIGMIDI model.'
 mirrors=root.attributes.itemByName('MIDI_MIRROR','logical_left_electronics')
 assert mirrors,'Expected both Left enclosure assemblies.'
 assert not [o for o in root.occurrences if o.component.name.startswith('TEMP')]
 path='/Users/ab/Documents/ChatGPT/MIDI controller 3/design/fusion/sigmidi-foot-controller-0.1.f3d'
 if app.activeDocument.isModified:assert app.activeDocument.save('SIGMIDI complete project archive for distribution cleanup')
 assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path))
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 report={'project':'SIGMIDI Foot Controller','version':'0.1','native_document':app.activeDocument.name,'path':'sigmidi-foot-controller-0.1.f3d','scope':'Entire native design, including original Right and preferred Left main/modular assemblies and part libraries','top_level_components':[o.component.name for o in root.occurrences],'embossed_icon':json.loads(icon.value),'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'bytes':__import__('os').path.getsize(path),'archive_CRC_verified':True,'exported_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 with open(path.replace('.f3d','-model.json'),'w') as f:json.dump(report,f,indent=2)
