import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付')
MODELS=ROOT/'01_场景与模型/Models';QA=ROOT/'06_验收与预览';rows=[]
for file in sorted(MODELS.glob('*/*.fbx')):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(file),use_image_search=False)
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];images=[]
 for m in bpy.data.materials:
  if m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
     im=n.image;images.append({'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'pixels_decodable':len(im.pixels)>0})
 missing=[x for x in images if min(x['size'])==0 or not x['pixels_decodable']]
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 vs=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];bb=[[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]]
 row={'asset':file.stem,'meshes':len(meshes),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'dimensions_m':[bb[1][i]-bb[0][i] for i in range(3)],'textures':images,'missing_texture_count':len(missing),'actions':len(bpy.data.actions),'has_geometry':bool(vs),'pass':bool(vs) and not missing}
 if file.stem=='PRP_CARGO_CRATE':
  bpy.context.scene.frame_set(20);bpy.context.view_layer.update();vs2=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];row['closed_demo_bbox_m']=[[min(v[k] for v in vs2) for k in range(3)],[max(v[k] for v in vs2) for k in range(3)]]
 rows.append(row)
(QA/'道具FBX回读验收.json').write_text(json.dumps({'method':'Blender clean-session import of all10 final props with image search disabled; geometry/material decoding and units, not Unity physics','assets':rows,'all_pass':all(x['pass'] for x in rows)},ensure_ascii=False,indent=2),'utf8')
print('PROPS_REIMPORT',len(rows),'PASS',all(x['pass'] for x in rows),flush=True)
