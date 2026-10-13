from pathlib import Path
import bpy,math,json
from mathutils import Vector
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付');OUT=ROOT/'01_场景与模型';QA=ROOT/'06_验收与预览'
file=OUT/'Idea3_这店不太对_完整场景.blend';bpy.ops.wm.open_mainfile(filepath=str(file));sc=bpy.context.scene
def cube(name,loc,dim,mat,col):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=name;ob.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for cc in list(ob.users_collection):cc.objects.unlink(ob)
 col.objects.link(ob);ob.data.materials.append(mat);return ob
roof=bpy.data.collections['08_Roof_Toggle'];front=bpy.data.collections['09_FrontWall_Toggle'];fx=bpy.data.collections['02_Fixtures'];lighting=bpy.data.collections['05_Lighting'];orange=bpy.data.materials['I3_orange'];dark=bpy.data.materials['I3_dark'];paper=bpy.data.materials['I3_paper'];purple=bpy.data.materials['I3_purple']
cow=bpy.data.objects['BOX_CUSTOMER'];cow.location=(4.6,1.65,0);cow.rotation_euler.z=math.pi/2
for ob in list(sc.objects):
 if ob.name.startswith('CEILING_BEAM'):
  for cc in list(ob.users_collection):cc.objects.unlink(ob)
  roof.objects.link(ob)
 if ob.name.startswith('QUEUE_FOOTPRINT'):bpy.data.objects.remove(ob,do_unlink=True)
# The queue sign is now only a decor/comedy prop near the customer, never a mandatory queue.
qr=bpy.data.objects.get('QUEUE_DIRECTION')
if qr:qr.location=(4.8,2.95,.75)
for name,pos in [('QUEUE_SIGN_BASE',(4.8,2.95,.045)),('QUEUE_SIGN_POST',(4.8,2.95,.40))]:bpy.data.objects[name].location=pos
for idx,(x,y) in enumerate([(3,3.9),(10.5,4.5),(4.2,11.8),(11.2,12),(4,18),(11,18)]):cube('FLUOR_FRONT_EMISSION_'+str(idx),(x,y-.116,2.80),(1.13,.008,.025),bpy.data.materials['I3_lamp'],lighting)
# Small normal checkout set-dressing like the reference; no new heroic replacement model.
cube('PEN_CUP',(1.18,2.25,1.01),(.12,.12,.16),purple,fx)
for i in range(4):
 ob=cube('PEN_'+str(i),(1.14+i*.025,2.25,1.15),(.009,.009,.20),dark,fx);ob.rotation_euler.y=(i-1.5)*.12
cube('COUNTER_THANKYOU',(1.55,2.71,1.15),(.30,.04,.33),paper,fx)
for dx in [-.07,.07]:cube('THANKYOU_EYE',(1.55+dx,2.684,1.16),(.020,.008,.022),dark,fx)
cube('THANKYOU_MOUTH',(1.55,2.681,1.08),(.062,.008,.012),dark,fx)
for x,y in [(3.5,1.0),(12.8,3.0)]:
 # Remove old solid basket block; keep stacked ridges and build an open basket top.
 for ob in list(sc.objects):
  if ob.name.startswith('BASKET_STACK') and abs(ob.location.x-x)<.02 and abs(ob.location.y-y)<.02:bpy.data.objects.remove(ob,do_unlink=True)
 cube('BASKET_BASE',(x,y,.035),(.40,.32,.07),purple,fx)
 for dx in [-.19,.19]:cube('BASKET_SIDE',(x+dx,y,.30),(.02,.32,.56),purple,fx)
 for dy in [-.15,.15]:cube('BASKET_SIDE',(x,y+dy,.30),(.38,.02,.56),purple,fx)
 for j in range(5):cube('BASKET_SLOT',(x-.135+j*.066,y-.162,.43),(.027,.009,.20),dark,fx)
cam=bpy.data.objects['CAM_01_Checkout'];cam.location=(2.1,.65,1.6);cam.rotation_euler=(Vector((2.35,3.5,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=24
cam=bpy.data.objects['CAM_02_Customer'];cam.location=(6.5,.45,1.1);cam.rotation_euler=(Vector((4.6,1.65,.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=35
sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.027,.043,.075,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.40
data=json.loads((OUT/'scene-manifest.json').read_text('utf8'))
for row in data['instances']:
 ob=bpy.data.objects.get(row['id'])
 if ob:row['position']=list(ob.location);row['yaw_degrees']=math.degrees(ob.rotation_euler.z)
for row in data['cameras']:
 ob=bpy.data.objects.get(row['name'])
 if ob:row['position']=list(ob.location)
data['packaging_atlas']={'source':'Textures/Shelf_Packaging_AI_Source.png','runtime':'Textures/Shelf_Packaging_Atlas_256.png','generator':'built-in image_gen','sampling':'Point','used_cells':'upper 3 rows x 4 columns =12; bottom row irregular and deliberately unused'}
(OUT/'scene-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
sc.camera=bpy.data.objects['CAM_00_Cutaway'];roof.hide_render=True;roof.hide_viewport=True;front.hide_render=False;front.hide_viewport=False;sc.frame_set(1)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(file),compress=True)
print('FINAL_BASE_READY',flush=True)
for name in ['CAM_00_Cutaway','CAM_01_Checkout','CAM_02_Customer','CAM_04_Coldroom']:
 sc.camera=bpy.data.objects[name];overview=name=='CAM_00_Cutaway';roof.hide_render=overview;front.hide_render=False
 sc.render.resolution_x=1440 if overview else 1280;sc.render.resolution_y=1000 if overview else 720;sc.render.filepath=str(QA/(name+'.png'));bpy.ops.render.render(write_still=True)
print('BASE_FINAL_PREVIEWS_COMPLETE',flush=True)
