"""idea3 original Tripo meshes -> local custom rigs, deterministic parametric clips.
No motion-library claim, manual frame posing, model regeneration, or source overwrite.
"""
import bpy, bmesh, math, json, shutil, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗')
OUT=ROOT/'07_技术交付'/'02_角色与动画'; OUT.mkdir(parents=True,exist_ok=True)
WORK=Path('D:/Repos/claw/outputs/idea3-character')
DEG=math.pi/180; FPS=30
CONFIG=[('cow','CHR_CLERK_COW',2.2,1500),('box','CHR_BOX_CUSTOMER',1.0,1200),('milk','PRP_ODD_PRODUCT',.24,600)]
ALL=[]

def ease(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def bell(t,a,b,c,d):return ease(a,b,t)*(1-ease(c,d,t))
def update():bpy.context.view_layer.update()
def worldrot(pb,axis,angle):
 rest=pb.bone.matrix_local.to_quaternion();pb.rotation_quaternion=rest.inverted()@Quaternion(Vector(axis),angle)@rest
def create_bones(key):
 if key=='cow':
  B=[('Root',(0,0,0),(0,0,.2),None),('Hips',(0,0,.49),(0,0,.75),'Root'),('Spine',(0,0,.75),(0,0,1.04),'Hips'),('Chest',(0,0,1.04),(0,0,1.25),'Spine'),('NeckA',(0,0,1.25),(0,0,1.52),'Chest'),('NeckB',(0,0,1.52),(0,0,1.81),'NeckA'),('Head',(0,0,1.81),(0,-.25,1.96),'NeckB'),('Tail',(0,.16,.59),(0,.65,.59),'Hips')]
  for side,s in [('L',1),('R',-1)]:
   B += [(f'UpperArm.{side}',(s*.23,0,1.15),(s*.55,0,1.15),'Chest'),(f'Forearm.{side}',(s*.55,0,1.15),(s*.83,0,1.15),f'UpperArm.{side}'),(f'Hand.{side}',(s*.83,0,1.15),(s*.94,0,1.15),f'Forearm.{side}'),(f'Thigh.{side}',(s*.175,0,.45),(s*.175,0,.26),'Hips'),(f'Shin.{side}',(s*.175,0,.26),(s*.175,0,.075),f'Thigh.{side}'),(f'Foot.{side}',(s*.175,0,.075),(s*.175,-.13,.05),f'Shin.{side}')]
  return B
 if key=='box':
  B=[('Root',(0,0,0),(0,0,.12),None),('Body',(0,0,.35),(0,0,.8),'Root')]
  for side,s in [('L',1),('R',-1)]:
   B += [(f'UpperArm.{side}',(s*.30,0,.60),(s*.48,0,.60),'Body'),(f'Forearm.{side}',(s*.48,0,.60),(s*.67,0,.60),f'UpperArm.{side}'),(f'Leg.{side}',(s*.145,0,.24),(s*.145,0,.08),'Root'),(f'Foot.{side}',(s*.145,0,.08),(s*.145,-.13,.035),f'Leg.{side}')]
  return B
 return [('Root',(0,0,0),(0,0,.025),None),('Body',(0,0,.05),(0,0,.18),'Root'),('Leg.L',(.032,0,.049),(.032,0,.014),'Root'),('Leg.R',(-.032,0,.049),(-.032,0,.014),'Root'),('Foot.L',(.032,0,.014),(.032,-.02,.006),'Leg.L'),('Foot.R',(-.032,0,.014),(-.032,-.02,.006),'Leg.R')]

def weights(key,p):
 x,y,z=p;side='L' if x>=0 else 'R';a=abs(x)
 if key=='cow':
  if y>.29 and z<.72:return {'Tail':1}
  if a>.255 and .95<z<1.34:
   if a<.37:
    t=ease(.255,.37,a);return {'Chest':1-t,f'UpperArm.{side}':t}
   t=ease(.48,.62,a)
   if a>.77:
    t=ease(.77,.87,a);return {f'Forearm.{side}':1-t,f'Hand.{side}':t}
   return {f'UpperArm.{side}':1-t,f'Forearm.{side}':t}
  if z<.36:
   if z<.12:
    t=ease(.055,.12,z);return {f'Foot.{side}':1-t,f'Shin.{side}':t}
   t=ease(.21,.29,z);return {f'Shin.{side}':1-t,f'Thigh.{side}':t}
  if z<.52:
   t=ease(.36,.48,z);return {f'Thigh.{side}':1-t,'Hips':t}
  if z<.87:
   t=ease(.63,.84,z);return {'Hips':1-t,'Spine':t}
  if z<1.28:
   t=ease(.9,1.05,z);return {'Spine':1-t,'Chest':t}
  if z<1.48:
   t=ease(1.28,1.37,z);return {'Chest':1-t,'NeckA':t}
  if z<1.73 and y>-.32:
   t=ease(1.46,1.59,z);return {'NeckA':1-t,'NeckB':t}
  t=ease(1.68,1.80,z) if y>-.32 else 1
  return {'NeckB':1-t,'Head':t}
 if key=='box':
  if a>.305 and .48<z<.76:
   if a<.365:
    t=ease(.305,.365,a);return {'Body':1-t,f'UpperArm.{side}':t}
   t=ease(.44,.53,a);return {f'UpperArm.{side}':1-t,f'Forearm.{side}':t}
  if z<.22:
   t=ease(.066,.12,z);return {f'Foot.{side}':1-t,f'Leg.{side}':t}
  return {'Body':1}
 if z<.041 and a<.05:
  t=ease(.013,.021,z);return {f'Foot.{side}':1-t,f'Leg.{side}':t}
 return {'Body':1}

def make_rig(key,asset,mesh,col):
 data=bpy.data.armatures.new(asset+'_Skeleton');rig=bpy.data.objects.new(asset+'_Rig',data);col.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True)
 bpy.ops.object.mode_set(mode='EDIT')
 for n,h,t,parent in create_bones(key):
  b=data.edit_bones.new(n);b.head=h;b.tail=t
  if parent:b.parent=data.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
 for b in rig.pose.bones:b.rotation_mode='QUATERNION'
 groups={b.name:mesh.vertex_groups.new(name=b.name) for b in data.bones}
 for v in mesh.data.vertices:
  w=weights(key,v.co);total=sum(w.values())
  for n,val in w.items():
   if val>1e-6:groups[n].add([v.index],val/total,'REPLACE')
 mod=mesh.modifiers.new('Skin_Custom_'+key,'ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False;mesh.parent=rig
 rig['asset_id']=asset;rig['front_axis']='-Y';rig['rig_type']='Generic; custom local skeleton; not Mixamo';rig['motion_source']='AI-authored deterministic parametric curves, baked at 30 fps';rig['rest_pose']='T-Pose' if key!='milk' else 'No-arm rest pose'
 return rig

def pose(key,rig,clip,t,duration):
 for p in rig.pose.bones:p.location=(0,0,0);p.rotation_quaternion=(1,0,0,0);p.scale=(1,1,1)
 pb=rig.pose.bones;phase=2*math.pi*t/duration
 if key=='cow':
  for side,s in [('L',1),('R',-1)]:worldrot(pb[f'UpperArm.{side}'],(0,1,0),s*72*DEG)
  worldrot(pb['NeckA'],(1,0,0),.5*DEG*math.sin(phase));worldrot(pb['Head'],(0,0,1),1.2*DEG*math.sin(phase));worldrot(pb['Tail'],(0,0,1),5*DEG*math.sin(phase))
  if clip=='Look':
   w=bell(t,.2,.9,1.6,2.7);worldrot(pb['NeckB'],(0,0,1),28*DEG*w);worldrot(pb['Head'],(0,0,1),10*DEG*w)
  if clip in ('DeepBow','SmallBow'):
   w=bell(t,.25,1.5,2.0,duration-.25);scale=1 if clip=='DeepBow' else .28
   worldrot(pb['Spine'],(1,0,0),12*DEG*w*scale);worldrot(pb['NeckA'],(1,0,0),48*DEG*w*scale);worldrot(pb['NeckB'],(1,0,0),26*DEG*w*scale);worldrot(pb['Head'],(1,0,0),-10*DEG*w*scale)
  if clip in ('Welcome','Point'):
   w=bell(t,.55,1.35,2.1,duration-.2)
   worldrot(pb['UpperArm.L'],(0,1,0),(72-67*w)*DEG);worldrot(pb['Forearm.L'],(0,0,1),(-24+(12*math.sin(t*8) if clip=='Welcome' else 0))*DEG*w);worldrot(pb['Head'],(0,0,1),-8*DEG*w)
 elif key=='box':
  for side,s in [('L',1),('R',-1)]:worldrot(pb[f'UpperArm.{side}'],(0,1,0),s*75*DEG)
  worldrot(pb['Body'],(0,0,1),.8*DEG*math.sin(phase))
  if clip in ('ShortStep','ThreeStepTurn'):
   steps=1 if clip=='ShortStep' else 3
   stride=2*math.pi*t*(steps/duration)
   env=1 if clip=='ShortStep' else math.sin(math.pi*min(1,t/duration))**.35
   for side,s in [('L',1),('R',-1)]:
    worldrot(pb[f'Leg.{side}'],(1,0,0),s*13*DEG*math.sin(stride)*env);worldrot(pb[f'Foot.{side}'],(1,0,0),-s*8*DEG*math.sin(stride)*env)
   pb['Body'].location.z=.006*(1-math.cos(stride*2))*env
   if clip=='ThreeStepTurn':worldrot(pb['Root'],(0,0,1),math.pi*ease(duration*.35,duration,t))
  if clip=='TurnTicket':
   w=bell(t,.5,1.25,2.5,duration-.2);worldrot(pb['Root'],(0,0,1),math.pi*ease(.15,2.0,t));worldrot(pb['UpperArm.R'],(0,1,0),(-75+60*w)*DEG);worldrot(pb['Forearm.R'],(0,0,1),30*DEG*w)
 else:
  if clip=='ShortStep':
   for side,s in [('L',1),('R',-1)]:
    worldrot(pb[f'Leg.{side}'],(1,0,0),s*16*DEG*math.sin(phase));worldrot(pb[f'Foot.{side}'],(1,0,0),-s*9*DEG*math.sin(phase))
   pb['Body'].location.z=.01*(1-math.cos(phase*2))
  if clip=='Turn180':worldrot(pb['Root'],(0,0,1),math.pi*ease(.2,1.7,t))
  if clip=='PeekBack':worldrot(pb['Root'],(0,0,1),35*DEG*bell(t,.2,.6,.9,1.4))

def reset_selection(objs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objs:o.select_set(True)
 bpy.context.view_layer.objects.active=objs[0]

def export_fbx(path,rig,mesh,bake):
 reset_selection([rig,mesh]);bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,armature_nodetype='NULL',use_armature_deform_only=False,bake_anim=bake,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,bake_anim_step=1,path_mode='COPY',embed_textures=True,use_custom_props=True)

def render(path,height,rig,mesh):
 sc=bpy.context.scene;sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)

for key,asset,height,target in CONFIG:
 bpy.ops.wm.read_factory_settings(use_empty=True);dst=OUT/asset;dst.mkdir(exist_ok=True);texdir=dst/'Textures';texdir.mkdir(exist_ok=True);(dst/'Clips').mkdir(exist_ok=True);(dst/'Preview').mkdir(exist_ok=True)
 fbx=next((WORK/key).glob('*.fbx'));bpy.ops.import_scene.fbx(filepath=str(fbx))
 objs=[o for o in bpy.context.scene.objects if o.type=='MESH'];reset_selection(objs);bpy.ops.object.join();mesh=bpy.context.object;mesh.name=asset+'_Mesh';mesh.data.name=asset+'_Geometry'
 vs=[mesh.matrix_world@v.co for v in mesh.data.vertices];mn=Vector([min(v[i] for v in vs) for i in range(3)]);mx=Vector([max(v[i] for v in vs) for i in range(3)]);scale=height/(mx.z-mn.z)
 rot=Matrix.Rotation(-math.pi/2,4,'Z');center=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z))
 for v in mesh.data.vertices:v.co=rot@((mesh.matrix_world@v.co-center)*scale)
 mesh.matrix_world.identity()
 # Tripo box is yawed within its own FBX: derive bilateral T-pose axis, not camera guess.
 extra_yaw=0.0
 if key=='box':
  arm=np.array([list(v.co) for v in mesh.data.vertices if abs(v.co.x)>.48 and .51<v.co.z<.7]);xy=arm[:,:2]-arm[:,:2].mean(axis=0);_,_,vt=np.linalg.svd(xy,full_matrices=False);axis=vt[0]
  if axis[0]<0:axis=-axis
  extra_yaw=-math.atan2(axis[1],axis[0]);align=Matrix.Rotation(extra_yaw,4,'Z')
  for v in mesh.data.vertices:v.co=align@v.co
 # Root aligns with center of the two soles, not the muzzle/tail bounding box.
 feet=[v.co for v in mesh.data.vertices if v.co.z<height*.045];shift=Vector(((min(v.x for v in feet)+max(v.x for v in feet))/2,(min(v.y for v in feet)+max(v.y for v in feet))/2,0))
 for v in mesh.data.vertices:v.co-=shift
 orig_tri=sum(len(p.vertices)-2 for p in mesh.data.polygons)
 # Keep UV-split vertices: welding before collapse can stretch Tripo's facial atlas.
 # Original mesh is preserved in user ZIP; derivative LOD0 keeps enough faces for silhouettes.
 mod=mesh.modifiers.new('AutomaticLOD0_PreserveUV','DECIMATE');mod.ratio=min(1,target/orig_tri);mod.use_collapse_triangulate=True;reset_selection([mesh]);bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in mesh.data.polygons:p.use_smooth=False
 srcimage=next((WORK/key).rglob('*basecolor*'));shutil.copy2(srcimage,texdir/(asset+'_OriginalBaseColor'+srcimage.suffix))
 original=bpy.data.images.load(str(srcimage),check_existing=False);w,h=original.size;arr=np.empty(w*h*4,dtype=np.float32);original.pixels.foreach_get(arr);arr=arr.reshape(h,w,4);ix=np.minimum(w-1,((np.arange(256)+.5)*w/256).astype(int));iy=np.minimum(h-1,((np.arange(256)+.5)*h/256).astype(int));small=arr[iy[:,None],ix[None,:],:]
 img=bpy.data.images.new(asset+'_BaseColor_256',width=256,height=256);img.pixels.foreach_set(small.ravel());img.filepath_raw=str(texdir/(asset+'_BaseColor_256.png'));img.file_format='PNG';img.save();img.pack();img.filepath='//Textures/'+asset+'_BaseColor_256.png'
 mat=bpy.data.materials.new(asset+'_PixelMatte');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.84;bs.inputs['Metallic'].default_value=0;im=nt.nodes.new('ShaderNodeTexImage');im.image=img;im.interpolation='Closest';nt.links.new(im.outputs['Color'],bs.inputs['Base Color']);mesh.data.materials.clear();mesh.data.materials.append(mat)
 mesh['asset_id']=asset;mesh['source_zip']=str(ROOT/'资产'/({'cow':'三维长颈鹿模型.zip','box':'体素盒子角色3d模型.zip','milk':'奶盒3d模型.zip'}[key]));mesh['source_triangles']=orig_tri;mesh['texture_filter']='Point / Closest';mesh['coordinate_convention']='meters; Z up; front -Y; sole-origin';mesh['automatic_lod']=True
 col=bpy.data.collections.new(asset);bpy.context.scene.collection.children.link(col)
 for c in list(mesh.users_collection):c.objects.unlink(mesh)
 col.objects.link(mesh);rig=make_rig(key,asset,mesh,col)
 sc=bpy.context.scene;sc.render.fps=FPS;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1;sc.render.engine='BLENDER_EEVEE_NEXT';sc.render.resolution_x=800;sc.render.resolution_y=800;sc.render.resolution_percentage=100
 sc.world=bpy.data.worlds.new('NeutralPreviewWorld');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.13,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5
 sc.view_settings.view_transform='AgX'
 previewcol=bpy.data.collections.new('Preview_NotForExport');sc.collection.children.link(previewcol)
 for loc,power in [((height*2,-height*3,height*3),85*height*height),((-height*2,-height,height*1.5),35*height*height),((0,height*2,height*2),55*height*height)]:
  data=bpy.data.lights.new('PreviewSoftbox','AREA');data.energy=power;data.shape='DISK';data.size=height*2;ob=bpy.data.objects.new('PreviewSoftbox',data);previewcol.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,height*.5))-ob.location).to_track_quat('-Z','Y').to_euler()
 cd=bpy.data.cameras.new('PreviewCamera');cam=bpy.data.objects.new('PreviewCamera',cd);previewcol.objects.link(cam);cam.location=(height*.3,-height*3,height*.68);cam.rotation_euler=(Vector((0,0,height*.5))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=height*1.32;sc.camera=cam
 clips=({'cow':[('Idle',4,True),('Look',3,False),('DeepBow',4,False),('Welcome',3.6,False),('Point',3.6,False),('SmallBow',3,False)],'box':[('Idle',4,True),('ShortStep',1.2,True),('ThreeStepTurn',3.6,False),('TurnTicket',4,False)],'milk':[('Idle',2,True),('ShortStep',1,True),('Turn180',2,False),('PeekBack',1.6,False)]})[key]
 clipreports=[];actions={}
 for name,duration,loop in clips:
  action=bpy.data.actions.new(asset+'__'+name);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action;end=round(duration*FPS)+1;sc.frame_start=1;sc.frame_end=end
  for frame in range(1,end+1):
   pose(key,rig,name,(frame-1)/FPS,duration)
   for p in rig.pose.bones:p.keyframe_insert('location',frame=frame,group=p.name);p.keyframe_insert('rotation_quaternion',frame=frame,group=p.name)
  for fc in action.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
  actions[name]=action
  # Matrix endpoint comparisons are explicit; non-looping turns deliberately retain heading.
  sc.frame_set(1);start=[tuple(x for row in p.matrix for x in row) for p in rig.pose.bones];sc.frame_set(end);finish=[tuple(x for row in p.matrix for x in row) for p in rig.pose.bones];delta=max(abs(a-b) for x,y in zip(start,finish) for a,b in zip(x,y))
  bounds=[];bad=0
  for frame in sorted(set([1,end//4,end//2,3*end//4,end])):
   sc.frame_set(frame);ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();coords=[v.co for v in m.vertices];bad+=sum(not all(math.isfinite(a) for a in v) for v in coords);bounds.append({'frame':frame,'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]});ev.to_mesh_clear()
  sc.frame_set(1);export_fbx(dst/'Clips'/f'{asset}__{name}.fbx',rig,mesh,True)
  clipreports.append({'name':name,'file':f'Clips/{asset}__{name}.fbx','frames':[1,end],'fps':FPS,'duration_seconds':duration,'loop':loop,'endpoint_matrix_max_delta':delta,'loop_pass':delta<1e-5 if loop else None,'root_translation':'none; drive path in game','root_heading_degrees':180 if name in ('Turn180','ThreeStepTurn','TurnTicket') else 0,'sampled_deformation_bounds':bounds,'nonfinite_vertices':bad})
 rig.animation_data.action=None
 for p in rig.pose.bones:p.location=(0,0,0);p.rotation_quaternion=(1,0,0,0)
 sc.frame_set(1);export_fbx(dst/f'{asset}__Rig_TPose.fbx',rig,mesh,False)
 cd.ortho_scale=max(height,mesh.dimensions.x)*1.22;render(dst/'Preview'/'01_Rest_TPose.png',height,rig,mesh);cd.ortho_scale=height*1.32
 rig.animation_data.action=actions['Idle'];sc.frame_end=round(clips[0][1]*FPS)+1;sc.frame_set(1);render(dst/'Preview'/'02_Idle_ArmsDown.png',height,rig,mesh)
 event='DeepBow' if key=='cow' else ('TurnTicket' if key=='box' else 'ShortStep');rig.animation_data.action=actions[event];sc.frame_set(50 if key!='milk' else 9);render(dst/'Preview'/'03_EventPose.png',height,rig,mesh)
 rig.animation_data.action=actions['Idle'];sc.frame_set(1);reset_selection([rig]);
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_distance=height*2.5;area.spaces.active.region_3d.view_location=(0,0,height*.5)
 bone_map={b.name:{'parent':b.parent.name if b.parent else None,'head_local_m':list(b.head_local),'tail_local_m':list(b.tail_local)} for b in rig.data.bones}
 sums=[sum(g.weight for g in v.groups) for v in mesh.data.vertices];grpmax=max(len(v.groups) for v in mesh.data.vertices)
 qa={'asset_id':asset,'collection':asset,'mesh':mesh.name,'rig':rig.name,'height_m':height,'geometry_original_triangles':orig_tri,'geometry_runtime_triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'vertex_count':len(mesh.data.vertices),'bones':len(bone_map),'unweighted_vertices':sum(s==0 for s in sums),'weight_sum_min':min(sums),'weight_sum_max':max(sums),'maximum_weights_per_vertex':grpmax,'uv_layers':len(mesh.data.uv_layers),'basecolor_size':[256,256],'texture_embedded':True,'original_basecolor_preserved':True,'coordinates':'meters, Z up, front -Y, soles at Z0 in rest','fbx_export':'-Z forward, Y up; Unity Generic; Apply Root Motion off for in-place clips','default_pose':'Idle arms down' if key!='milk' else 'standing','source_revision':'User Tripo ZIP, original geometry-derived automatic LOD; no regenerated character','clips':clipreports,'remaining_engine_validation':['Unity import in actual project not executed','Cloth/joint silhouette must be checked at target in-game camera','Faces are original fixed texture; no fabricated expression blendshapes']}
 (dst/'bone_map.json').write_text(json.dumps(bone_map,ensure_ascii=False,indent=2),encoding='utf8');(dst/'clip_map.json').write_text(json.dumps(clipreports,ensure_ascii=False,indent=2),encoding='utf8');(dst/'qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
 bpy.ops.wm.save_as_mainfile(filepath=str(dst/f'{asset}_Rigged.blend'));qa['blend']=str(dst/f'{asset}_Rigged.blend');ALL.append(qa)
 print('CHARACTER_DONE',asset,flush=True)
(OUT/'characters_manifest.json').write_text(json.dumps(ALL,ensure_ascii=False,indent=2),encoding='utf8')
print('ALL_CHARACTER_RIGS_DONE',flush=True)
