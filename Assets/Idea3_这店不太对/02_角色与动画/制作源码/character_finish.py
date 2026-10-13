import bpy,json,shutil
from pathlib import Path
OUT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付/02_角色与动画');WORK=Path('D:/Repos/claw/outputs/idea3-character');rows=[]
for asset in ['CHR_CLERK_COW','CHR_BOX_CUSTOMER','PRP_ODD_PRODUCT']:
 dst=OUT/asset;bpy.ops.wm.open_mainfile(filepath=str(dst/f'{asset}_Rigged.blend'));rig=bpy.data.objects[asset+'_Rig'];mesh=bpy.data.objects[asset+'_Mesh'];sc=bpy.context.scene
 rig.animation_data.action=None
 for p in rig.pose.bones:p.location=(0,0,0);p.rotation_quaternion=(1,0,0,0)
 bpy.context.view_layer.update();sc.camera.data.ortho_scale=max(mesh.dimensions.x,mesh.dimensions.z)*1.22;sc.render.filepath=str(dst/'Preview'/'01_Rest_TPose.png');bpy.ops.render.render(write_still=True)
 rig.animation_data.action=bpy.data.actions[asset+'__Idle'];sc.frame_set(1);e=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();coords=[v.co for v in m.vertices];rows.append({'asset_id':asset,'idle_bounds_local_m':{'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]}});e.to_mesh_clear()
(OUT/'placement_bounds.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'visual_review.json').write_text(json.dumps({'reviewed_images':['cow rest/idle/deepbow','box rest/idle/turnticket','milk idle/step'],'corrections':['isolated box shoulder weights from rigid body','corrected original box internal yaw using bilateral arm principal axis','rejected weld+collapse variant because it distorted face UV; retained UV split vertices','full T-pose framing'],'result':'local preview accepted; final Unity camera and deformation test pending'},ensure_ascii=False,indent=2),encoding='utf8')
source=OUT/'制作源码';source.mkdir(exist_ok=True)
for n in ('character_build.py','character_verify.py','character_preview.py','character_make_previews.py','character_finish.py'):
 shutil.copy2(Path('D:/Repos/claw/tools/idea3')/n,source/n)
print(json.dumps(rows))
