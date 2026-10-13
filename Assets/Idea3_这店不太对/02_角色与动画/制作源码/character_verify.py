import bpy,json,shutil,math
from pathlib import Path
from io_scene_fbx import parse_fbx
OUT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付/02_角色与动画');WORK=Path('D:/Repos/claw/outputs/idea3-character/roundtrip');WORK.mkdir(parents=True,exist_ok=True)
rows=[]
for f in sorted(OUT.glob('*/*.fbx'))+sorted(OUT.glob('*/Clips/*.fbx')):
 root,version=parse_fbx.parse(str(f));objects=next(e for e in root.elems if e.id==b'Objects');videos=[e for e in objects.elems if e.id==b'Video'];embedded=[len(c.props[0]) for e in videos for c in e.elems if c.id==b'Content' and c.props]
 dst=WORK/f.parent.parent.name/f.parent.name;dst.mkdir(parents=True,exist_ok=True);copy=dst/f.name;shutil.copy2(f,copy)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(copy),use_anim=True)
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];coords=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
 row={'file':str(f.relative_to(OUT)),'fbx_version':version,'embedded_texture_bytes':embedded,'meshes':len(meshes),'rigs':len(rigs),'bones':[len(o.data.bones) for o in rigs],'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'uv_layers':[len(o.data.uv_layers) for o in meshes],'unweighted':sum(not len(v.groups) for o in meshes for v in o.data.vertices),'image_decode_ok':all(im.size[0]>0 for im in bpy.data.images),'actions':[{'name':a.name,'range':list(a.frame_range),'curves':len(a.fcurves)} for a in bpy.data.actions],'rest_bounds_m':{'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]}}
 row['pass']=len(meshes)==1 and len(rigs)==1 and bool(embedded) and row['unweighted']==0 and row['image_decode_ok'] and (bool(row['actions']) if 'Clips' in f.parts else True)
 rows.append(row)
(OUT/'fbx_roundtrip_qa.json').write_text(json.dumps({'all_pass':all(r['pass'] for r in rows),'files':rows},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'all_pass':all(r['pass'] for r in rows),'count':len(rows),'failures':[r for r in rows if not r['pass']]},ensure_ascii=False))
