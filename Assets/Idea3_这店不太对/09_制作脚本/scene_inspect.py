from pathlib import Path
import bpy,json,zipfile,math
from mathutils import Vector
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗')
OUT=Path('D:/Repos/claw/outputs/idea3-scene')
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
rows=[]
files=sorted((ROOT/'资产').glob('*.zip'))
for idx,zp in enumerate(files):
    folder=OUT/'raw'/zp.stem;folder.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():
            target=(folder/info.filename).resolve()
            assert target.is_relative_to(folder.resolve())
        z.extractall(folder)
    fbx=next(folder.rglob('*.fbx'))
    before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(fbx),use_anim=False)
    objs=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    assert objs
    for o in objs:o.rotation_euler.z-=math.pi/2
    bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(p) for o in objs for p in o.bound_box]
    low=Vector(tuple(min(v[k] for v in pts) for k in range(3)));high=Vector(tuple(max(v[k] for v in pts) for k in range(3)))
    dims=high-low;s=1.75/max(dims)
    off=Vector(((idx%5)*2.5,(idx//5)*3.2,0))
    for o in objs:
        o.location=(o.location-Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z)))*s+off;o.scale*=s
        for m in o.data.materials:
            if not m:continue
            m.use_nodes=True
            for n in m.node_tree.nodes:
                if n.type=='BSDF_PRINCIPLED':n.inputs['Roughness'].default_value=.86;n.inputs['Metallic'].default_value=0
    comps=[]
    for o in objs:
        verts=o.data.vertices;adj=[[] for _ in verts]
        for e in o.data.edges:
            a,b=e.vertices;adj[a].append(b);adj[b].append(a)
        seen=set()
        for vi in range(len(verts)):
            if vi in seen:continue
            todo=[vi];seen.add(vi);group=[]
            while todo:
                n=todo.pop();group.append(n)
                for j in adj[n]:
                    if j not in seen:seen.add(j);todo.append(j)
            co=[verts[j].co for j in group]
            comps.append({'count':len(group),'bounds':[[min(v[k] for v in co) for k in range(3)],[max(v[k] for v in co) for k in range(3)]]})
    rows.append({'index':idx,'zip':str(zp),'fbx':str(fbx),'raw_rotated_dims':list(dims),'objects':[o.name for o in objs],'vertices':sum(len(o.data.vertices) for o in objs),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objs),'components':sorted(comps,key=lambda x:-x['count'])})
    bpy.ops.object.text_add(location=(off.x-1.0,off.y-.85,1.95),rotation=(math.pi/2,0,0))
    t=bpy.context.object;t.data.body=str(idx)+': '+zp.stem[:28];t.data.size=.12
world=bpy.context.scene.world or bpy.data.worlds.new('World');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.23,.27,.29,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6
for loc in [(3,-4,8),(9,7,7)]:
    bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=1600;l.data.shape='DISK';l.data.size=8
    l.rotation_euler=(Vector((5,3,0))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(12,-16,15));cam=bpy.context.object;cam.rotation_euler=(Vector((5,3.1,.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=15.4;bpy.context.scene.camera=cam
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.render.filepath=str(OUT/'source_models_overview.png');s.view_settings.view_transform='Standard'
(OUT/'inspection.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'inspection.blend'))
bpy.ops.render.render(write_still=True)
print('DONE',OUT,flush=True)
