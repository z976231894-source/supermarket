"""Read-only actual scene geometry + 0.3m capsule footprint audits."""
import bpy,json,math,collections
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付')
rows=[]
def bounds(objects):
 pts=[]
 for o in objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();pts.extend(o.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
 return [[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]] if pts else None
for folder in sorted((ROOT/'01_场景与模型/Levels').iterdir()):
 if not (folder/'scene-manifest.json').exists():continue
 m=json.loads((folder/'scene-manifest.json').read_text('utf8'));lid=m['level_id'];bpy.ops.wm.open_mainfile(filepath=str(folder/(folder.name+'.blend')));bpy.context.scene.frame_set(1)
 for c in bpy.data.collections:c.hide_viewport=False
 bpy.context.view_layer.update();obstacles=[];char=[];roofs=[];owners={}
 # Actual world-space geometry envelopes of furniture, structural walls and asset families.
 for o in bpy.context.scene.objects:
  if o.name.startswith('CEILING_'):roofs.append({'name':o.name,'bounds':bounds([o]),'hide_render':o.hide_render,'collections':[c.name for c in o.users_collection]})
  if o.type=='EMPTY' and o.get('asset_id'):
   b=bounds(o.children_recursive);owners[o.name]=b
   if o['asset_id'] in ['CHR_CLERK_COW','CHR_BOX_CUSTOMER','PRP_ODD_PRODUCT']:char.append({'name':o.name,'root':list(o.matrix_world.translation),'bounds':b})
  elif o.type=='MESH' and (o.name.startswith(('WALL_','L1_NORTH','L1_WINDOW','SHELF_','COUNTER_','LOW_MILK_TABLE','COLD_CONFIRM','L1_MILK_LOW_TABLE','L1_MILK_TABLE_LEG','L1_APRON','L2_APRON','L3_APRON')) or any(c.name=='02_Fixtures' for c in o.users_collection)):
   b=bounds([o])
   if b and b[1][2]>.12 and b[0][2]<1.75:obstacles.append({'name':o.name,'bounds':b})
 for name,b in owners.items():
  if b and b[1][2]>.12 and b[0][2]<1.75:obstacles.append({'name':name,'bounds':b})
 def dist(x,y,o):
  a,b=o['bounds'];return math.hypot(max(a[0]-x,0,x-b[0]),max(a[1]-y,0,y-b[1]))
 # AABB obstacles conservatively enclose irregular models; submesh overhangs are intentionally safety-biased.
 stands=[]
 for t in m['triggers']:
  x,y,_=t['safe_stand_blender_m'];near=sorted([(dist(x,y,o),o['name']) for o in obstacles])
  stands.append({'id':t['id'],'stand':t['safe_stand_blender_m'],'nearest_obstacle_distance':near[0][0],'intersections_r03':[{'name':n,'distance':d} for d,n in near if d<.3-1e-4],'nearest':near[:4],'owners_present':[{'owner':n,'bounds':owners.get(n)} for n in t['observation_targets']]})
 # Grid flood fill through conservative actual fixture envelopes, all observed owners remain solid.
 step=.15;minx=.3;miny=-1.7;maxx=13.7;maxy=m['room_dimensions_m'][1]-.3;nx=math.floor((maxx-minx)/step)+1;ny=math.floor((maxy-miny)/step)+1
 blocked=set()
 for i in range(nx):
  for j in range(ny):
   if any(dist(minx+i*step,miny+j*step,o)<.3-1e-4 for o in obstacles):blocked.add((i,j))
 def cell(p):return (max(0,min(nx-1,round((p[0]-minx)/step))),max(0,min(ny-1,round((p[1]-miny)/step))))
 start=cell(m['player_start_blender_m']);reach=set();q=collections.deque([start]) if start not in blocked else collections.deque()
 while q:
  c=q.popleft()
  if c in reach:continue
  reach.add(c)
  for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)]:
   n=(c[0]+dx,c[1]+dy)
   if 0<=n[0]<nx and 0<=n[1]<ny and n not in blocked and n not in reach:q.append(n)
 for r in stands:r['grid_reachable_from_spawn']=cell(r['stand']) in reach
 doors=[]
 for d in m['open_doors']:
  x,y,_=d['position'];yaw=math.radians(d['yaw_degrees']);side=(math.cos(yaw),math.sin(yaw));forward=(-math.sin(yaw),math.cos(yaw));hx=abs(side[0])*.375+abs(forward[0])*.55;hy=abs(side[1])*.375+abs(forward[1])*.55
  cart_hits=set();player_hits=set()
  for stepnum in range(61):
   t=-1.5+stepnum*.05;px=x+t*forward[0];py=y+t*forward[1]
   for o in obstacles:
    a,b=o['bounds']
    if dist(px,py,o)<.3-1e-4:player_hits.add(o['name'])
    if px+hx>a[0]+1e-4 and px-hx<b[0]-1e-4 and py+hy>a[1]+1e-4 and py-hy<b[1]-1e-4:cart_hits.add(o['name'])
  doors.append({'id':d['id'],'nominal_clear_width_m':d['clear_width_m'],'minimum_design_width_1_4m_pass':d['clear_width_m']>=1.4,'player_radius_m':.3,'player_straight_crossing_3m_pass':not player_hits,'player_intersections':sorted(player_hits),'cart_reference_footprint_m':[.75,1.1],'cart_aligned_straight_crossing_3m_pass':not cart_hits,'cart_intersections':sorted(cart_hits),'cart_note':'Reference footprint only; no pushable cart gameplay required or verified. Rotation/swept door closure not tested.'})
 allowners=all(all(x['bounds'] for x in r['owners_present']) for r in stands)
 allsafe=all(not r['intersections_r03'] and r['grid_reachable_from_spawn'] for r in stands)
 roofok=any(r['bounds'] and r['bounds'][0][1]>=-.01 and r['bounds'][1][1]<=m['room_dimensions_m'][1]+.01 for r in roofs)
 rows.append({'level_id':lid,'pass':allowners and allsafe and roofok and all(d['player_straight_crossing_3m_pass'] for d in doors),'stands':stands,'all_trigger_owners_have_geometry':allowners,'characters':char,'roofs':roofs,'doors':doors,'obstacle_count':len(obstacles),'blocked_cells':len(blocked),'reachable_cells':len(reach),'spawn_cell_blocked':start in blocked,'obstacles':obstacles})
 print('AUDIT',lid,[(r['id'],r['intersections_r03'],r['grid_reachable_from_spawn']) for r in stands],flush=True)
out=Path('D:/Repos/claw/outputs/idea3-level-import-qa');out.mkdir(parents=True,exist_ok=True);(out/'geometry-and-nav.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
report={'all_pass':len(rows)==3 and all(r['pass'] for r in rows),'method':'Actual Blender evaluated geometry world AABBs; 0.30m radius player, 1.75m height, 0.15m four-neighbour navigation raster; conservative solid furniture envelope; initial door pose; no Unity runtime simulation','levels':[{k:v for k,v in r.items() if k!='obstacles'} for r in rows],'not_verified':['Unity collider setup / navmesh','runtime animated obstruction','capsule step heights, slope and physics','cart turning and pushing','minimum play duration']}
(ROOT/'06_验收与预览/三关卡动线验收.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
