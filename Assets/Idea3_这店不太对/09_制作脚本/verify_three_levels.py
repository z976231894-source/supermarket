"""Reopen every independent .blend, FBX and GLB in isolated Blender scenes.
Import copies are made under workspace so embedded-image extraction never dirties delivery.
"""
import bpy,json,hashlib,shutil,math,struct
from pathlib import Path
from io_scene_fbx import parse_fbx
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付');WORK=Path('D:/Repos/claw/outputs/idea3-level-import-qa');WORK.mkdir(parents=True,exist_ok=True)
def stats():
 sc=bpy.context.scene;meshes=[o for o in sc.objects if o.type=='MESH'];pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];bad_images=[];images={}
 for o in meshes:
  for m in o.data.materials:
   if m and m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='TEX_IMAGE' and n.image:
      im=n.image;images[im.name]={'size':list(im.size),'packed':bool(im.packed_file),'interpolation':n.interpolation,'decoded':im.size[0]>0};
      if im.size[0]<=0:bad_images.append(im.name)
 return {'mesh_objects':len(meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'armatures':len([o for o in sc.objects if o.type=='ARMATURE']),'lights':len([o for o in sc.objects if o.type=='LIGHT']),'images':images,'missing_or_undecoded_images':sorted(set(bad_images)),'no_material_meshes':[o.name for o in meshes if not any(o.data.materials)],'nonfinite_vertices':sum(not all(math.isfinite(x) for x in v) for v in pts),'bounds':{'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]},'object_names':[o.name for o in sc.objects]}
rows=[]
for folder in sorted((ROOT/'01_场景与模型/Levels').iterdir()):
 if not folder.is_dir() or not (folder/'scene-manifest.json').exists():continue
 manifest=json.loads((folder/'scene-manifest.json').read_text('utf8'));lid=manifest['level_id'];blend=folder/(folder.name+'.blend');bpy.ops.wm.open_mainfile(filepath=str(blend));bpy.context.scene.frame_set(1);bs=stats();triggers=[o.name for o in bpy.context.scene.objects if o.name.startswith('TRG_'+lid) and not o.name.endswith('_SAFE_STAND')];legacy=[o.name for o in bpy.context.scene.objects if o.name.startswith(('EVT_E','SLOT_','TAKE_CARD_','SCAN_SAMPLE_'))]
 relative_files=[r['rigged_prefab_path'] for r in manifest['character_placeholders']]+[r['file'] for t in manifest['triggers'] for r in t['animation_refs'] if r.get('kind')=='skeletal_clip'];badrefs=[p for p in relative_files if not (folder/p).resolve().is_file()]
 row={'level_id':lid,'manifest_sha256':hashlib.sha256((folder/'scene-manifest.json').read_bytes()).hexdigest(),'blend':{k:v for k,v in bs.items() if k!='object_names'},'trigger_count':len(triggers),'expected_trigger_count':manifest['gag_count'],'legacy_mission_markers':legacy,'missing_relative_references':badrefs,'all_optional_no_prerequisites':all(t['optional'] and not t['prerequisites'] and t['replay_allowed'] for t in manifest['triggers']),'preview_files':{},'exports':[]}
 for img in sorted((ROOT/'06_验收与预览'/folder.name).glob('*.png')):row['preview_files'][img.name]=img.stat().st_size
 for ext in ['fbx','glb']:
  file=folder/(folder.name+'.'+ext);scratch=WORK/lid/ext;scratch.mkdir(parents=True,exist_ok=True);temp=scratch/file.name;shutil.copy2(file,temp)
  if ext=='fbx':
   tree,ver=parse_fbx.parse(str(file));objs=next(e for e in tree.elems if e.id==b'Objects');emb=[len(c.props[0]) for e in objs.elems if e.id==b'Video' for c in e.elems if c.id==b'Content' and c.props];info={'version':ver,'embedded_images_count':len(emb),'embedded_images_bytes':sum(emb)}
  else:
   raw=file.read_bytes();magic,ver,size=struct.unpack_from('<III',raw,0);length,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+length]);info={'version':ver,'embedded_images_count':sum('bufferView'in im for im in g.get('images',[])),'external_image_uris':[im['uri'] for im in g.get('images',[]) if 'uri'in im and not im['uri'].startswith('data:')],'samplers':g.get('samplers',[]),'extras_character_placeholders':sum(bool(n.get('extras',{}).get('character_placeholder')) for n in g.get('nodes',[]))}
  bpy.ops.wm.read_factory_settings(use_empty=True)
  if ext=='fbx':bpy.ops.import_scene.fbx(filepath=str(temp),use_anim=False)
  else:bpy.ops.import_scene.gltf(filepath=str(temp))
  s=stats();r={'format':ext,'file':str(file),'bytes':file.stat().st_size,'container':info,'stats':{k:v for k,v in s.items() if k!='object_names'}}
  r['pass']=s['nonfinite_vertices']==0 and not s['missing_or_undecoded_images'] and not s['no_material_meshes'] and s['armatures']==0 and info['embedded_images_count']>0 and (not info.get('external_image_uris')) and s['mesh_objects']>0
  r['static_visual_expected']=True;r['rigs_intentionally_in_blend_and_separate_prefabs']=True;row['exports'].append(r)
 row['pass']=len(triggers)==manifest['gag_count'] and not legacy and not badrefs and row['all_optional_no_prerequisites'] and len(row['preview_files'])>=4 and all(r['pass'] for r in row['exports']) and not bs['missing_or_undecoded_images'];rows.append(row)
 print('LEVEL_VERIFIED',lid,row['pass'],flush=True)
report={'scope':'three independent optional-observation levels; actual Blender/FBX/GLB reopen','all_pass':len(rows)==3 and all(r['pass'] for r in rows),'levels':rows,'not_verified':['Unity project import','player controller','observation event runtime','runtime collision/navigation','actual first-play duration'],'static_scene_export_policy':'FBX/GLB contain baked Idle character visuals; use replacement map for actual animation. Editable Blend files retain rigs.'}
(ROOT/'06_验收与预览/三关卡回读验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'all_pass':report['all_pass'],'levels':[(r['level_id'],r['pass']) for r in rows]},ensure_ascii=False))
