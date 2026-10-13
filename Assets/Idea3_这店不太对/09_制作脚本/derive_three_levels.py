"""Derive three independent optional-gag walking-sim art levels from final base.
Run only after root author announces readiness: blender -b --python this.py -- --source-ready
Source .blend is opened read-only and never saved over. Scene FBX/GLB are static visual
snapshots; .blend keeps genuine rigs. Standalone skinned prefabs remain in 02_角色与动画.
"""
import bpy,bmesh,json,math,hashlib,sys,copy
from pathlib import Path
from mathutils import Vector,Matrix

ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付')
BASE=ROOT/'01_场景与模型/Idea3_这店不太对_完整场景.blend'
if '--source-ready' not in sys.argv:raise SystemExit('Await final base author confirmation; pass --source-ready explicitly.')
SPECS=[('L1','L1_便民店初访',0,9),('L2','L2_后仓夜游',9,20),('L3','L3_整店不对劲',0,20)]
if '--level' in sys.argv:
 chosen=sys.argv[sys.argv.index('--level')+1];SPECS=[s for s in SPECS if s[0]==chosen]
BASE_SHA=hashlib.sha256(BASE.read_bytes()).hexdigest()
BASE_MANIFEST=json.loads((ROOT/'01_场景与模型/scene-manifest.json').read_text('utf8'))

def bbox(o,evaluated=False):
 if o.type!='MESH':return None
 if evaluated:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();vs=[o.matrix_world@v.co for v in m.vertices];e.to_mesh_clear()
 else:vs=[o.matrix_world@v.co for v in o.data.vertices]
 if not vs:return None
 return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]

def remove_tree(o):
 for child in list(o.children):remove_tree(child)
 bpy.data.objects.remove(o,do_unlink=True)

def clone_tree(source,newname,pos,yaw=None):
 src=[source]+list(source.children_recursive);mapping={}
 for o in src:
  n=o.copy();n.name=newname+o.name[len(source.name):];bpy.context.scene.collection.objects.link(n);mapping[o]=n
 for o,n in mapping.items():
  n.parent=mapping.get(o.parent)
  for m in n.modifiers:
   if hasattr(m,'object') and m.object in mapping:m.object=mapping[m.object]
 n=mapping[source];n.location=pos
 if yaw is not None:n.rotation_euler.z=math.radians(yaw)
 return n

def material(name,hexcolor,emission=0):
 old=bpy.data.materials.get('I3_'+name)
 if old:return old
 m=bpy.data.materials.new('LV_'+name);m.use_nodes=True
 srgb=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)];rgb=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in srgb];p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.84;p.inputs['Metallic'].default_value=0
 if emission:p.inputs['Emission Color'].default_value=(*rgb,1);p.inputs['Emission Strength'].default_value=emission
 return m

def cube(name,loc,dims,mat,col):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(mat);o['art_role']='derived_level_structure';return o

def clip_world_y(o,y,keep_lower):
 if o.data.users>1:o.data=o.data.copy()
 bm=bmesh.new();bm.from_mesh(o.data);bm.transform(o.matrix_world)
 res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,y,0),plane_no=(0,1,0),clear_outer=keep_lower,clear_inner=not keep_lower)
 edges=[v for v in res['geom_cut'] if isinstance(v,bmesh.types.BMEdge) and v.is_boundary]
 if edges:
  try:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
  except Exception:pass
 bm.transform(o.matrix_world.inverted());bm.to_mesh(o.data);bm.free();o.data.update()

def collect_instances():
 rows=[]
 for o in bpy.context.scene.objects:
  if o.type=='EMPTY' and o.get('asset_id'):
   rows.append({'instance_id':o.name,'asset_id':o['asset_id'],'position_blender_m':list(o.matrix_world.translation),'yaw_degrees':math.degrees(o.matrix_world.to_euler().z),'objects':[c.name for c in o.children_recursive]})
 return rows

def cam(name,pos,target,lens=28,ortho=None):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.025;d.clip_end=150
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o

def trigger(col,tid,title,owners,focus,stand,radius,action_refs,description):
 # Final base revision moved the cold-room table/characters away from the old exit bottleneck.
 if tid=='TRG_L2_04':focus=(10.5,4.6,.8);stand=(10.5,3.25,1.65)
 if tid=='TRG_L3_02':focus=(11.2,13.85,1.0);stand=(11.9,12.2,1.65)
 o=bpy.data.objects.new(tid,None);col.objects.link(o);o.location=focus;o.empty_display_type='SPHERE';o.empty_display_size=.18;o['trigger_id']=tid;o['optional']=True;o['has_prerequisites']=False;o['range_m']=radius;o['note']='art marker only; gameplay trigger not implemented'
 safe=bpy.data.objects.new(tid+'_SAFE_STAND',None);col.objects.link(safe);safe.location=(stand[0],stand[1],0);safe.empty_display_type='CIRCLE';safe.empty_display_size=.3
 return {'id':tid,'title':title,'observation_targets':owners,'focus_blender_m':list(focus),'safe_stand_blender_m':list(stand),'range_m':radius,'observation_hold_seconds':.6,'trigger_modes':['observe','optional_E_replay'],'prerequisites':[],'optional':True,'replay_allowed':True,'replay_cooldown_seconds':4,'no_input_lock':True,'no_failure':True,'no_collect_requirement':True,'behavior':description,'animation_refs':action_refs,'audio_cue':{'id':tid+'_CUE','status':'ready_mapping_available_runtime_not_implemented','mapping_file':'../../../04_音频/Data/runtime-cue-map.json','duck_bgm_db':-6,'not_a_prerequisite':True},'implemented_game_logic':False}

def char_clip(aid,name):return {'kind':'skeletal_clip','asset_id':aid,'file':'../../../02_角色与动画/'+aid+'/Clips/'+aid+'__'+name+'.fbx','clip':name}
def prop_ref(instance,part,axis,behavior):return {'kind':'optional_transform_track','instance':instance,'part_suffix':part,'axis':axis,'behavior':behavior,'runtime_implementation_required':True}

def build_triggers(lid,col):
 cow=lambda n:char_clip('CHR_CLERK_COW',n);box=lambda n:char_clip('CHR_BOX_CUSTOMER',n);milk=lambda n:char_clip('PRP_ODD_PRODUCT',n)
 if lid=='L1':
  return [trigger(col,'TRG_L1_01','欢迎得过于郑重',['COW_CLERK'],(2.25,3.2,1.6),(2.25,1.65,1.65),2,[cow('Look'),cow('DeepBow')],'注视牛，先慢慢看向玩家，再用长脖子深鞠躬。结束回Idle，不发任务。'),trigger(col,'TRG_L1_02','收银机也要发言',['REGISTER'],(3,2.65,1.15),(3.1,1.65,1.65),1.8,[prop_ref('REGISTER','Jaw','X','single sober jaw open/close, optional paper strip')],'轻触收银机，下巴短促开合并吐一张无意义小票；无需扫码或收集。'),trigger(col,'TRG_L1_03','极其认真地转错身',['BOX_CUSTOMER'],(4.6,1.65,.7),(5.7,1.65,1.65),1.8,[box('ThreeStepTurn')],'纸箱顾客小步转180°，仍一本正经；无需纠正或排队任务。'),trigger(col,'TRG_L1_04','奶盒在偷看',['L1_MILK_DISPLAY'],(8,4,.62),(7,4,1.65),1.8,[milk('Turn180'),milk('PeekBack')],'看向矮台商品，奶盒转脸；转开视线后小幅偷回头，不用抓取。')]
 if lid=='L2':
  cr=bpy.data.objects.get('CARGO_circle');cp=cr.matrix_world.translation if cr else Vector((1.6,1.95,.36));ap=bpy.data.objects.get('ROUTE_1');rp=ap.matrix_world.translation if ap else Vector((6.4,.6,1.65))
  return [trigger(col,'TRG_L2_01','郑重收藏的空气',['CARGO_circle'],(cp.x,cp.y,.72),(cp.x,cp.y+1.25,1.65),1.8,[prop_ref('CARGO_circle','Lid','X','open -> empty hold -> close using measured hinge')],'可选打开货箱，里面空空如也却得到庄严确认；不要求插卡搬箱。'),trigger(col,'TRG_L2_02','路牌比你更犹豫',['ROUTE_1','ROUTE_2'],(rp.x,rp.y,rp.z),(6.4,2,1.65),2,[prop_ref('ROUTE_1','Body','Z','turn away once then quietly return')],'观察箭头，它认真转向另一个明显出口，离开视线又回去；不设路线解谜。'),trigger(col,'TRG_L2_03','冰柜点名大会',['SINGING_FRIDGE'],(12.45,5.1,1.1),(12.8,3.7,1.65),1.9,[prop_ref('SINGING_FRIDGE','Door','Z','open and short staggered bottle response')],'轻触开门，商品错拍短合唱；可随时走开，不需确认三个符号。'),trigger(col,'TRG_L2_04','短腿商品散步',['MILK_1','MILK_2','MILK_3','MILK_4','MILK_5'],(11.25,3.9,.60),(11.25,2.65,1.65),1.9,[milk('ShortStep'),milk('Turn180')],'几只奶盒错开短步转脸；行为在台面安全范围内，不要求取回或封箱。'),trigger(col,'TRG_L2_05','空气也很有分量',['WEIGH_SCALE'],(2.3,9.1,.65),(2.3,8.1,1.65),1.8,[prop_ref('WEIGH_SCALE','Body','emission','one solemn confirmation and absurd weight display')],'轻触空称台，仪表给出过分郑重的确认音；无正确答案或分数。')]
 return [trigger(col,'TRG_L3_01','全店郑重欢迎',['COW_CLERK','REGISTER'],(2.65,2.8,1.35),(2.65,1.6,1.65),2,[cow('DeepBow'),prop_ref('REGISTER','Jaw','X','brief delayed reply')],'牛店员行礼后，收银机慢半拍回应；观察即可，不接交班任务。'),trigger(col,'TRG_L3_02','冷库悄悄开会',['SINGING_FRIDGE','MILK_1','MILK_2','MILK_3','MILK_4','MILK_5'],(11.85,13.2,.95),(11.8,11.5,1.65),3,[prop_ref('SINGING_FRIDGE','Door','Z','optional open to reveal the meeting'),milk('Turn180'),milk('PeekBack')],'冰柜与奶盒互相错拍回应；玩家可自由离开，没有冷封步骤。'),trigger(col,'TRG_L3_03','卸货区的空气称量',['WEIGH_SCALE','STAMP_STATION'],(3.1,18.45,.75),(3.1,17,1.65),2.1,[prop_ref('WEIGH_SCALE','Body','emission','absurd zero-weight result'),prop_ref('STAMP_STATION','Plunger','Z','one unnecessarily formal stamp')],'空称台和盖章台进行无意义但隆重的仪式；不用搬运三箱。'),trigger(col,'TRG_L3_04','纸箱顾客的严肃会议',['L3_CUSTOMER_MEETING_A','L3_CUSTOMER_MEETING_B'],(11.1,18.5,.65),(11.1,17,1.65),2.1,[box('TurnTicket'),box('ThreeStepTurn')],'两位纸箱顾客隔着空地认真交流，先后转错方向；不要求递票或通关。'),trigger(col,'TRG_L3_05','回头就变的箭头',['ROUTE_3','ROUTE_4'],(4.4,15.4,1.65),(4.4,14.15,1.65),2.6,[prop_ref('ROUTE_3','Body','Z','look-away return; never blocks doors')],'注视与回头时箭头悄悄换向，两个出口始终都能走；纯观察梗。')]

for lid,dirname,ymin,ymax in SPECS:
 bpy.ops.wm.open_mainfile(filepath=str(BASE));sc=bpy.context.scene;sc.name=dirname;sc.frame_set(1);sc.render.fps=30;sc.frame_end=121;preview_engine=sc.render.engine
 sc['delivery_type']='Independent '+lid+' free-observation art level; optional gags, no mission chain; FBX/GLB are static visual snapshots'
 for collection in bpy.data.collections:collection.hide_viewport=False
 for obj in sc.objects:obj.hide_set(False);obj.hide_viewport=False
 out=ROOT/'01_场景与模型/Levels'/dirname;out.mkdir(parents=True,exist_ok=True);preview=ROOT/'06_验收与预览'/dirname;preview.mkdir(parents=True,exist_ok=True)
 if lid=='L1':clone_tree(bpy.data.objects['MILK_1'],'L1_MILK_DISPLAY',(8,4,.44),0)
 if lid=='L3':
  clone_tree(bpy.data.objects['BOX_CUSTOMER'],'L3_CUSTOMER_MEETING_A',(10.3,18.5,0),90);clone_tree(bpy.data.objects['BOX_CUSTOMER'],'L3_CUSTOMER_MEETING_B',(11.9,18.5,0),-90)
 bpy.context.view_layer.update()
 # Remove all old mission markers, cameras, and obsolete dialogue. Keep source art and signs.
 old=bpy.data.collections.get('06_InteractionSockets')
 if old:
  for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
 for o in list(sc.objects):
  if o.type=='CAMERA':bpy.data.objects.remove(o,do_unlink=True)
  elif lid=='L1' and o.name.startswith(('AREA_SIGN_','AREA_LABEL_')):bpy.data.objects.remove(o,do_unlink=True)
  elif o.type=='FONT' and any(w in o.data.body for w in ['交班','交接','冷封','封箱','任务','完成','扫码']):bpy.data.objects.remove(o,do_unlink=True)
  elif o.name.startswith('SCAN_SAMPLE_'):o.name=o.name.replace('SCAN_SAMPLE_','DISPLAY_SHAPE_')
 # Whole imported instances are retained or removed as a family, not sliced at limb boundaries.
 if lid!='L3':
  handled=set()
  for oname in [o.name for o in sc.objects]:
   o=bpy.data.objects.get(oname)
   if o is None:continue
   if o.type=='EMPTY' and o.get('asset_id') and o.name not in handled:
    family=[o]+list(o.children_recursive);handled.update(x.name for x in family);y=o.matrix_world.translation.y
    if not (ymin-.001<=y<ymax-.001):remove_tree(o)
  # Modular structures may straddle the cut; clip only environmental mesh, not furniture/characters.
  for oname in [o.name for o in sc.objects]:
   o=bpy.data.objects.get(oname)
   if o is None:continue
   if o.name in handled or o.parent:continue
   if o.type=='MESH':
    b=bbox(o)
    if not b:continue
    lo,hi=b;center=(lo[1]+hi[1])/2
    structural=any(c.name in ['01_Structure','08_Roof_Toggle','09_FrontWall_Toggle'] for c in o.users_collection)
    if hi[1]<ymin-.0001 or lo[1]>ymax+.0001:remove_tree(o)
    elif structural and ((lid=='L1' and hi[1]>ymax) or (lid=='L2' and lo[1]<ymin)):clip_world_y(o,ymax if lid=='L1' else ymin,lid=='L1')
    elif not structural and not(ymin<=center<ymax):remove_tree(o)
   elif o.type in {'LIGHT','FONT','EMPTY'}:
    if not(ymin<=o.matrix_world.translation.y<ymax):remove_tree(o)
  # Door root trees are not tagged as assets; clean outside-zone roots, children follow safely.
  for oname in [o.name for o in sc.objects]:
   o=bpy.data.objects.get(oname)
   if o is None:continue
   if o.parent is None and o.type=='EMPTY' and o.name.startswith('GATE_') and not(ymin<=o.location.y<ymax):remove_tree(o)
 if ymin:
  for o in sc.objects:
   if o.parent is None:o.location.y-=ymin
 bpy.context.view_layer.update()
 derived=bpy.data.collections.new(lid+'_DerivedStructure');sc.collection.children.link(derived);wall=material('wall','677968');purple=material('purple','6E5879');dark=material('dark','34443E');paper=material('paper','D8D0B8')
 if lid=='L1':
  # Replace cut boundary with a complete north wall and a glazed observation window.
  for o in list(sc.objects):
   if o.type=='MESH' and o.name.startswith(('WALL_H_9','WALL_TRIM_H_9','SKIRT_H_9','WALL_PIXEL_H_9','AREA_SIGN_','AREA_LABEL_')):bpy.data.objects.remove(o,do_unlink=True)
  cube('L1_NORTH_LOWER',(7,9,.45),(14,.16,.9),wall,derived);cube('L1_NORTH_UPPER',(7,9,2.7),(14,.16,.6),wall,derived)
  cube('L1_NORTH_LEFT',(2.6,9,1.65),(5.2,.16,1.5),wall,derived);cube('L1_NORTH_RIGHT',(11.4,9,1.65),(5.2,.16,1.5),wall,derived)
  cube('L1_WINDOW_NIGHT_BACKING',(7,9.09,1.65),(3.6,.05,1.5),dark,derived)
  for x in [5.2,7,8.8]:cube('L1_WINDOW_MULLION',(x,8.895,1.65),(.06,.06,1.56),purple,derived)
  for z in [.9,2.4]:cube('L1_WINDOW_TRANSOM',(7,8.895,z),(3.65,.06,.06),purple,derived)
  cube('L1_MILK_LOW_TABLE',(8,4,.405),(.75,.55,.07),purple,derived)
  for x in [7.71,8.29]:
   for y in [3.8,4.2]:cube('L1_MILK_TABLE_LEG',(x,y,.19),(.06,.06,.38),wall,derived)
 # Every open front entrance leads to a real apron with side/back barriers, never an empty cut edge.
 cube(lid+'_ENTRY_APRON',(7,-1,-.08),(14,2,.16),wall,derived)
 cube(lid+'_APRON_FRONT_GUARD',(7,-2.05,.48),(14.2,.1,.96),purple,derived)
 for x in [-.05,14.05]:cube(lid+'_APRON_SIDE_GUARD',(x,-1,.48),(.1,2.2,.96),purple,derived)
 # Recreate neutral source-facing label after removing the old forced-shift instruction.
 if lid!='L2' and not any(o.name.startswith('COUNTER_LABEL') for o in sc.objects):
  bpy.ops.object.text_add(location=(2.25,2.235,.48),rotation=(math.pi/2,0,0));textobj=bpy.context.object
  textobj.name=lid+'_WELCOME_LABEL';textobj.data.body='欢迎光临';textobj.data.size=.14;textobj.data.align_x='CENTER';textobj.data.materials.append(paper)
  font=Path('C:/Windows/Fonts/msyh.ttc')
  if font.exists():textobj.data.font=bpy.data.fonts.load(str(font))
 # All Chinese labels become meshes, so FBX/glTF does not depend on the recipient's fonts.
 for o in list(sc.objects):
  if o.type=='FONT':bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 tcol=bpy.data.collections.new('06_OptionalGagTriggers');sc.collection.children.link(tcol);triggers=build_triggers(lid,tcol)
 start=bpy.data.objects.new(lid+'_PLAYER_START',None);tcol.objects.link(start);start.location=(7,1.6,1.65) if lid!='L2' else (4.4,.9,1.65)
 length=ymax-ymin;overview=cam(lid+'_CAM_Overview',(19,-31,34) if lid=='L3' else (19,-24,28),(7,10,.6) if lid=='L3' else (7,length/2,.7),ortho=27 if lid=='L3' else 23)
 if lid=='L2':closes=[cam(lid+'_CAM_Coldroom',(9.1,1,1.60),(11.7,5,.95),22),cam(lid+'_CAM_Warehouse',(6.8,1,1.62),(3,4,.8),24)]
 elif lid=='L1':closes=[cam(lid+'_CAM_Checkout',(2.1,.65,1.6),(2.35,3.5,1.35),24),cam(lid+'_CAM_Customer',(6.3,.7,1.15),(4.6,1.65,.65),38)]
 else:closes=[cam(lid+'_CAM_Checkout',(2.1,.65,1.6),(2.35,3.5,1.35),24),cam(lid+'_CAM_Coldroom',(9.1,10,1.60),(11.7,14,.95),22)]
 plan=cam(lid+'_CAM_Plan',(7,(length-2)/2,30),(7,(length-2)/2,0),ortho=17)
 instances=collect_instances();lightdata=[{'name':o.name,'type':o.data.type,'position_blender_m':list(o.matrix_world.translation),'rotation_euler_radians':list(o.matrix_world.to_euler()),'energy':o.data.energy,'color_linear':list(o.data.color),'area_size':o.data.size if o.data.type=='AREA' else None,'unity_note':'Area lights require baking or approximation; not runtime FBX lights'} for o in sc.objects if o.type=='LIGHT']
 doors=[]
 for d in BASE_MANIFEST.get('door_clearances',[]):
  if bpy.data.objects.get(d['id']) and bpy.data.objects[d['id']].name in sc.objects:
   nd=copy.deepcopy(d);nd['position'][1]-=ymin;doors.append(nd)
 exits=[{'id':lid+'_MAIN_ENTRY','center_blender_m':[7,0,0] if lid!='L2' else [4.4,0,0],'clear_width_m':2.5 if lid!='L2' else 1.6,'connects_to':'bounded 14x2m entrance apron','requires_progress_flag':False}]
 if lid=='L2':exits.append({'id':'L2_SECOND_ENTRY','center_blender_m':[11.1,0,0],'clear_width_m':1.6,'connects_to':'same bounded entrance apron','requires_progress_flag':False})
 colliders=[]
 for c in BASE_MANIFEST.get('suggested_colliders',[]):
  cy=c['center'][1];hh=c['size'][1]/2
  if cy+hh<ymin or cy-hh>ymax:continue
  nc=copy.deepcopy(c)
  if c['name'].startswith('WALL'):
   low=max(ymin,cy-hh);high=min(ymax,cy+hh);nc['center'][1]=(low+high)/2-ymin;nc['size'][1]=high-low
  elif not(ymin<=cy<ymax):continue
  else:nc['center'][1]-=ymin
  colliders.append(nc)
 for o in derived.objects:
  b=bbox(o)
  if b and b[1][2]>.12:colliders.append({'name':o.name,'center':[(b[0][i]+b[1][i])/2 for i in range(3)],'size':[b[1][i]-b[0][i] for i in range(3)],'kind':'Box','source':'derived_structure'})
 placeholders=[]
 for inst in instances:
  aid=inst['asset_id']
  if aid in ['CHR_CLERK_COW','CHR_BOX_CUSTOMER','PRP_ODD_PRODUCT']:
   placeholders.append({'instance_id':inst['instance_id'],'asset_id':aid,'rigged_prefab_path':'../../../02_角色与动画/'+aid+'/'+aid+'__Rig_TPose.fbx','rigged_blend_path':'../../../02_角色与动画/'+aid+'/'+aid+'_Rigged.blend','default_animation':'Idle','scene_fbx_glb_mode':'static evaluated Idle mesh, not an animatable prefab','preserve_root_transform':True,'replace_only_mesh_not_scene_root':True})
 # Pack material dependencies and remove dead imports from numerical counts.
 for im in bpy.data.images:
  if im.users and not im.packed_file:
   if im.source=='GENERATED' or (im.source=='FILE' and Path(bpy.path.abspath(im.filepath)).is_file()):im.pack()
 emission=[]
 for m in bpy.data.materials:
  if m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='BSDF_PRINCIPLED' and n.inputs['Emission Strength'].default_value>0:emission.append({'material':m.name,'strength':n.inputs['Emission Strength'].default_value,'color_linear':list(n.inputs['Emission Color'].default_value)})
 manifest={'level_id':lid,'title':dirname.split('_',1)[1],'source_base_sha256':BASE_SHA,'room_dimensions_m':[14,length,3],'entry_apron_m':[14,2],'source_y_range':[ymin,ymax],'origin_shift_blender_m':[0,-ymin,0],'units':'m','axes':{'blender':'Z up, fronts -Y','unity_export':'FBX -Z forward/Y up; glTF Y-up'},'design':'Single-player free walking observation comedy; no quest, combat, failure, collecting, required sequence or locked ending','gag_count':len(triggers),'triggers':triggers,'instances':instances,'character_placeholders':placeholders,'open_doors':doors,'entrances':exits,'suggested_colliders':colliders,'lights':lightdata,'emissive_materials':emission,'player_start_blender_m':list(start.location),'files':{'editable':dirname+'.blend','static_fbx':dirname+'.fbx','static_glb':dirname+'.glb'},'runtime_not_implemented':['walking controller','observation triggers and replay','prop event callbacks','physics/collision and navmesh','audio playback/ducking','Unity import validation'],'no_playtime_guarantee':True}
 (out/'scene-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');(out/'character-replacement-map.json').write_text(json.dumps(placeholders,ensure_ascii=False,indent=2),encoding='utf8')
 (out/'关卡美术接入说明.md').write_text(f'''# {dirname}

独立美术关卡，室内 14×{length}×3m，入口另有14×2m实体前坪和围挡。来自最终整店基场景的派生，不覆盖原场景。

玩法严格为单人自由走动观察：本关 {len(triggers)} 个独立可选梗，没有任务前置、战斗、失败、收集或强制通关次序。可随时忽略/离开/重播。触发点以 `TRG_{lid}_*` 标识，配套安全站位、观察目标和动作引用在 scene-manifest.json；旧14事件交班链已移除。

- `.blend`：可编辑完整场景，保留实际角色骨架、材质和灯光。默认总览隐藏屋顶便于查看；屋顶仍存在于 `08_Roof_Toggle`，切第一人称或检查完整外壳时可开启。入口前墙独立层，切面展示不代表没有墙体。
- `.fbx` / `.glb`：可直接看布局/材质的静态场景快照；贴图内嵌，角色采用当前Idle求值网格，**不是可动画角色Prefab**。
- 需要角色动画时按 `character-replacement-map.json`，保留对应 instance_id 根物体位姿，仅换掉静态角色网格，接入 `02_角色与动画` 中的 Generic 蒙皮FBX及独立动作。不能再次给根物体叠加轴向旋转。
- Blender米制、Z向上/角色正面-Y；FBX -Z Forward/Y Up、glTF Y Up。中文标签已转网格，接收方不依赖本机字体。
- `scene-manifest.json` 附静态灯功率/颜色、Emission、门洞、建议碰撞包络和可选触发说明。面积光在 Unity 需烘焙或近似，FBX/GLB不携带完整后处理。
- 实际控制器、观察触发、回放防抖、音效/BGM压低、碰撞和导航需要技术接入；当前不是可运行游戏，不宣称已测游玩时长。

总览、两个近景和完整平面图在 `../../../06_验收与预览/{dirname}`。具体读档验收见 `06_验收与预览/三关卡回读验收.json`。
''',encoding='utf8')
 # Beauty previews: cutaway views hide the actual complete roof/front only for inspection.
 def render(camera,name,planview=False):
  sc.camera=camera;sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.render.resolution_percentage=100
  if planview:
   sc.render.resolution_x=1400;sc.render.resolution_y=1000 if lid=='L1' else 1200 if lid=='L2' else 1800
   aspect=sc.render.resolution_x/sc.render.resolution_y;camera.data.ortho_scale=(max(14,(length+2)*aspect) if aspect>=1 else max(length+2,14/aspect))*1.13
  else:sc.render.resolution_x=1440 if camera==overview else 1600;sc.render.resolution_y=1000
  sc.render.filepath=str(preview/name);bpy.ops.render.render(write_still=True)
 roof=bpy.data.collections.get('08_Roof_Toggle');front=bpy.data.collections.get('09_FrontWall_Toggle')
 if roof:roof.hide_render=True
 if front:front.hide_render=(lid=='L2')
 render(overview,'01_总览.png')
 if roof:roof.hide_render=False
 if front:front.hide_render=False
 for i,camera in enumerate(closes):render(camera,f'0{i+2}_近景.png')
 if roof:roof.hide_render=True
 if front:front.hide_render=True
 render(plan,'04_完整平面.png',True)
 # Saved edit scene defaults to readable overview. Roof/front remain separate and can be toggled.
 sc.camera=overview;sc.render.resolution_x=1440;sc.render.resolution_y=1000
 if roof:roof.hide_render=True;roof.hide_viewport=True
 if front:front.hide_render=(lid=='L2')
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_perspective='CAMERA'
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(dirname+'.blend')))
 # Export evaluated Idle geometry for scene snapshots, maintaining named instance roots for replacement.
 # Changes here are in-memory only, after editable .blend has been saved.
 sc.frame_set(1)
 for o in list(sc.objects):
  if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers):
   old=o.data;e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());o.data=bpy.data.meshes.new_from_object(e,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());o.modifiers.clear();o.vertex_groups.clear();o['static_character_placeholder']=True
   parent=o.parent
   if parent and parent.type=='ARMATURE':world=o.matrix_world.copy();o.parent=parent.parent;o.matrix_world=world
 for o in list(sc.objects):
  if o.type=='ARMATURE':bpy.data.objects.remove(o,do_unlink=True)
 for o in sc.objects:
  o.hide_set(False);o.hide_viewport=False
  if o.type!='LIGHT' and o.animation_data:o.animation_data_clear()
 for c in bpy.data.collections:c.hide_viewport=False
 for mapping in placeholders:
  r=bpy.data.objects.get(mapping['instance_id'])
  if r:
   r['character_placeholder']=True;r['rigged_prefab_path']=mapping['rigged_prefab_path'];r['default_animation']='Idle'
 bpy.ops.object.select_all(action='DESELECT')
 for o in sc.objects:
  if o.type in {'MESH','EMPTY'}:o.select_set(True)
 bpy.ops.export_scene.fbx(filepath=str(out/(dirname+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},bake_anim=False,axis_forward='-Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',path_mode='COPY',embed_textures=True,use_custom_props=True)
 bpy.ops.export_scene.gltf(filepath=str(out/(dirname+'.glb')),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_apply=True)
 print('LEVEL_READY',lid,str(out),flush=True)
print('THREE_LEVEL_DERIVATION_COMPLETE',flush=True)
