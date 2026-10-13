"""Prepare genuine supplied AI meshes for idea3. Never overwrite ZIP sources."""
from pathlib import Path
import bpy,bmesh,json,math,hashlib,os,numpy as np
from mathutils import Vector,Matrix
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗')
OUT=ROOT/'07_技术交付/01_场景与模型'
WORK=Path('D:/Repos/claw/outputs/idea3-scene')
OUT.mkdir(parents=True,exist_ok=True)
ROWS=json.loads((WORK/'inspection.json').read_text('utf8'))
SPECS={
 0:('PRP_HAND_CART',(.75,1.1,1.0),1200),
 1:('PRP_SHIFT_CLIPBOARD',(.24,.035,.34),500),
 2:('PRP_FRIDGE',None,1200),
 5:('PRP_WEIGH_SCALE',None,800),
 6:('PRP_SYMBOL_CARD_SET',(.12,.008,.12),240),
 7:('PRP_REGISTER_FACE',None,1000),
 8:('PRP_CARGO_CRATE',(.55,.45,.58),800),
 9:('PRP_STAMP_STATION',None,900),
 11:('PRP_ROUTE_SIGN_SET',None,500),
 12:('PRP_LOADING_PALLET',(1.1,.9,.14),500),
}
HEIGHTS={'PRP_FRIDGE':2.1,'PRP_WEIGH_SCALE':1.25,'PRP_REGISTER_FACE':.4,'PRP_STAMP_STATION':.9,'PRP_ROUTE_SIGN_SET':.25}
def bounds(o):
    c=[v.co for v in o.data.vertices]
    return Vector([min(v[k] for v in c) for k in range(3)]),Vector([max(v[k] for v in c) for k in range(3)])
def part(o,name,pred):
    mesh=o.data.copy();bm=bmesh.new();bm.from_mesh(mesh)
    remove=[f for f in bm.faces if not pred(f.calc_center_median())]
    bmesh.ops.delete(bm,geom=remove,context='FACES')
    bm.to_mesh(mesh);bm.free()
    if not len(mesh.polygons):bpy.data.meshes.remove(mesh);return None
    ob=bpy.data.objects.new(name,mesh);o.users_collection[0].objects.link(ob);return ob
def origin(o,pivot):
    o.data.transform(Matrix.Translation(-Vector(pivot)));o.location=Vector(pivot)
def make_empty(name,col):
    o=bpy.data.objects.new(name,None);col.objects.link(o);o.empty_display_type='PLAIN_AXES';o.empty_display_size=.12;return o
def cube(name,loc,dim,col,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(o.users_collection):c.objects.unlink(o)
    col.objects.link(o);o.data.materials.append(mat);return o
def material(name,c,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.84;p.inputs['Metallic'].default_value=0
    if emission:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emission
    return m
bpy.ops.wm.read_factory_settings(use_empty=True)
records=[]
for index,(aid,fit,budget) in SPECS.items():
    row=next(r for r in ROWS if r['index']==index);before=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=row['fbx'],use_anim=False,use_image_search=False)
    imported=[o for o in bpy.data.objects if o not in before];meshes=[o for o in imported if o.type=='MESH'];assert len(meshes)==1
    ob=meshes[0];ob.rotation_euler.z-=math.pi/2
    if aid=='PRP_HAND_CART':ob.rotation_euler.z+=math.pi/2
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    lo,hi=bounds(ob);dims=hi-lo;offset=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z));ob.data.transform(Matrix.Translation(-offset))
    if fit:
        scales=Vector([fit[k]/dims[k] for k in range(3)])
    else:scales=Vector((HEIGHTS[aid]/dims.z,)*3)
    ob.data.transform(Matrix.Diagonal((*scales,1)))
    lo,hi=bounds(ob);dims=hi-lo
    col=bpy.data.collections.new(aid);bpy.context.scene.collection.children.link(col)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob)
    for x in imported:
        if x!=ob:bpy.data.objects.remove(x,do_unlink=True)
    # UV-preserving nearest-neighbour technical texture resampling; no repainting.
    source_tex=next(p for p in Path(row['fbx']).parent.rglob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png'})
    image=bpy.data.images.load(str(source_tex),check_existing=False);w,h=image.size;pixels=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4)
    idsx=np.minimum(((np.arange(256)+.5)*w/256).astype(int),w-1);idsy=np.minimum(((np.arange(256)+.5)*h/256).astype(int),h-1)
    im=bpy.data.images.new(aid+'_BaseColor',width=256,height=256,alpha=False);im.colorspace_settings.name='sRGB';im.pixels.foreach_set(pixels[idsy[:,None],idsx[None,:]].ravel());im.update()
    texpath=OUT/'Textures'/(aid+'_BaseColor.png');texpath.parent.mkdir(exist_ok=True);im.filepath_raw=str(texpath);im.file_format='PNG';im.save();im.pack()
    mat=material('MAT_'+aid,(.6,.6,.6));bsdf=mat.node_tree.nodes.get('Principled BSDF');tn=mat.node_tree.nodes.new('ShaderNodeTexImage');tn.image=im;tn.interpolation='Closest';mat.node_tree.links.new(tn.outputs['Color'],bsdf.inputs['Base Color']);ob.data.materials.clear();ob.data.materials.append(mat)
    for p in ob.data.polygons:p.material_index=0;p.use_smooth=False
    root=make_empty(aid+'_ROOT',col);root['asset_id']=aid;root['source_zip']=Path(row['zip']).name;root['front']='-Y';root['units']='m';ob.name=aid+'_Body'
    parts=[ob];dynamic=[];notes=[]
    # Extract source-surface moving groups, retaining original UV loops.
    if aid=='PRP_FRIDGE':
        threshold=lo.y+float(dims.y)*.15
        pred=lambda p:p.y<threshold and p.z>.12 and p.z<dims.z-.13
        window=lambda p:abs(p.x)<dims.x*.37 and .27<p.z<dims.z-.29
        cavity=lambda p:abs(p.x)<dims.x*.39 and p.y<hi.y-.075 and .24<p.z<dims.z-.23
        door=part(ob,aid+'_Door',lambda p:pred(p) and not window(p));body=part(ob,aid+'_Body',lambda p:not pred(p) and not cavity(p))
        if door and body:
            bpy.data.objects.remove(ob,do_unlink=True);parts=[body,door];pivot=(lo.x+.03,lo.y+.02,.12);origin(door,pivot);door['motion_axis']='Z';door['range_degrees']='0..-70';dynamic.append(door)
            dark=material(aid+'_Interior',(0.10,.16,.15));shelfmat=material(aid+'_Shelf',(.27,.39,.37));emitmat=material(aid+'_Emission',(.34,.75,.69),2)
            parts.append(cube(aid+'_InnerBack',(0,hi.y-.095,1.05),(dims.x*.80,.025,1.63),col,dark))
            for zz in [.38,.92,1.46]:parts.append(cube(aid+'_Shelf_'+str(zz),(0,.02,zz),(dims.x*.81,dims.y*.78,.032),col,shelfmat))
            parts.append(cube(aid+'_InnerLight',(0,hi.y-.12,1.82),(dims.x*.67,.028,.035),col,emitmat))
            glassmat=material(aid+'_Glass',(.35,.60,.56));glassmat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.12;glassmat.surface_render_method='DITHERED'
            glass=cube(aid+'_DoorGlass',(0,lo.y+.04,1.045),(dims.x*.74,.009,1.54),col,glassmat)
            glass.parent=door;glass.location-=door.location;glass['keep_parent']='door';parts.append(glass)
            framemat=material(aid+'_DoorFrame',(.18,.30,.29))
            for nm,loc,dim in [('Left',(-dims.x*.395,lo.y+.035,1.045),(.045,.045,1.66)),('Right',(dims.x*.395,lo.y+.035,1.045),(.045,.045,1.66)),('Top',(0,lo.y+.035,1.875),(dims.x*.83,.045,.05)),('Bottom',(0,lo.y+.035,.215),(dims.x*.83,.045,.05))]:
                frameob=cube(aid+'_Frame'+nm,loc,dim,col,framemat);frameob.parent=door;frameob.location-=door.location;frameob['keep_parent']='door';parts.append(frameob)
            for xx in [-.10,.10]:parts.append(cube(aid+'_PixelEye',(xx,lo.y-.006,2.0),(.044,.008,.022),col,dark))
            parts.append(cube(aid+'_PixelMouth',(0,lo.y-.008,1.955),(.03,.008,.016),col,dark))
            notes.append('Original exterior retained; source baked opaque centre removed to form a real cavity. Independent shelves, emissive strip and translucent window added. Door hinge Z 0..-70 degrees.')
    elif aid=='PRP_CARGO_CRATE':
        # Full slanted lid is above the box rim, including the forward triangles.
        pred=lambda p:p.z>.329
        lid=part(ob,aid+'_Lid',pred);body=part(ob,aid+'_Body',lambda p:not pred(p))
        if lid and body:
            bpy.data.objects.remove(ob,do_unlink=True);parts=[body,lid];origin(lid,(0,.20,.32));lid['motion_axis']='X';lid['reference_pose']='source open';dynamic.append(lid)
            notes.append('Lid split across full rim plane Z=.329; source tilted approx 41.5 degrees. Runtime collision remains a stable box. Decorative source closed envelope is approx .36m, not an assumed .45m solid cube.')
    elif aid=='PRP_STAMP_STATION':
        pred=lambda p:p.z>dims.z*.54 and p.z<dims.z*.85 and p.y<hi.y-dims.y*.27
        head=part(ob,aid+'_Plunger',pred);body=part(ob,aid+'_Body',lambda p:not pred(p))
        if head and body:
            bpy.data.objects.remove(ob,do_unlink=True);parts=[body,head];origin(head,(0,0,dims.z*.60));head['motion_axis']='Z';head['travel_m']=.045;dynamic.append(head)
    elif aid=='PRP_REGISTER_FACE':
        pred=lambda p:p.z>dims.z*.31 and p.z<dims.z*.43 and p.y<lo.y+dims.y*.24
        jaw=part(ob,aid+'_Jaw',pred);body=part(ob,aid+'_Body',lambda p:not pred(p))
        if jaw and body:
            bpy.data.objects.remove(ob,do_unlink=True);parts=[body,jaw];origin(jaw,(0,lo.y+.08,dims.z*.40));jaw['motion_axis']='X';dynamic.append(jaw)
    tris_before=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts)
    for o in parts:
        # Keep source UV seam vertices: welding these AI atlas islands before
        # decimation visibly warps the pixel panels and can collapse thin signs.
        if not o.get('keep_parent'):o.parent=root
        tri=sum(len(p.vertices)-2 for p in o.data.polygons)
        ratio=min(1,budget/max(1,tris_before))
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        if ratio<1:
            mod=o.modifiers.new('AI_mesh_budget_reduce','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
        for p in o.data.polygons:p.use_smooth=False
        o['asset_id']=aid;o['source_type']='User supplied Tripo mesh, UV retained';o['collision_hint']='manual_primitive'
    for o in dynamic:
        base_loc=o.location.copy();base_rot=o.rotation_euler.copy()
        for frame,v in [(1,0),(20,1),(45,1),(65,0),(90,0)]:
            o.location=base_loc.copy();o.rotation_euler=base_rot.copy()
            if o.name.endswith('Door'):o.rotation_euler.z=math.radians(-70)*v
            elif o.name.endswith('Lid'):o.rotation_euler.x=math.radians(41.5)*v
            elif o.name.endswith('Plunger'):o.location.z-=.045*v
            elif o.name.endswith('Jaw'):o.rotation_euler.x=math.radians(12)*v
            o.keyframe_insert(data_path='rotation_euler',frame=frame);o.keyframe_insert(data_path='location',frame=frame)
        if o.animation_data and o.animation_data.action:o.animation_data.action.name=aid+'_Demo'
    bpy.context.scene.frame_set(1)
    aid_dir=OUT/'Models'/aid;aid_dir.mkdir(parents=True,exist_ok=True)
    for img in [im]:img.filepath='//../../Textures/'+texpath.name
    asset_scene=bpy.data.scenes.new(aid+'_Preview');asset_scene.collection.children.link(col);asset_scene.unit_settings.system='METRIC';asset_scene.unit_settings.scale_length=1;asset_scene.render.fps=30;asset_scene.frame_end=90
    bpy.data.libraries.write(str(aid_dir/(aid+'.blend')),{col,asset_scene},path_remap='NONE',fake_user=True,compress=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in col.objects:o.select_set(True)
    # image absolute for FBX embed; each name unique to avoid Tripo Color.jpg collisions.
    im.filepath=str(texpath)
    bpy.ops.export_scene.fbx(filepath=str(aid_dir/(aid+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},use_mesh_modifiers=True,axis_forward='-Z',axis_up='Y',apply_unit_scale=True,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,path_mode='COPY',embed_textures=True,use_custom_props=True,add_leaf_bones=False)
    im.filepath='//Textures/'+texpath.name
    tris_after=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts)
    records.append({'asset_id':aid,'source_zip':str(row['zip']),'source_sha256':hashlib.sha256(Path(row['zip']).read_bytes()).hexdigest(),'dimensions_m':list(dims),'dimension_strategy':'specified fit for modular logistics pieces' if fit else 'uniform height fit preserving source silhouette','triangles_source':tris_before,'triangles_runtime':tris_after,'texture':str(texpath.relative_to(OUT)),'texture_size':[256,256],'sampling':'Point/Closest','objects':[o.name for o in col.objects],'dynamic_parts':[o.name for o in dynamic],'notes':notes})
    print('PREPARED',aid,tris_after,list(dims),flush=True)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
bpy.context.scene.render.fps=30;bpy.context.scene.frame_end=90;bpy.context.scene.frame_set(1)
for sc in bpy.data.screens:
    for a in sc.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Idea3_Prop_Library.blend'),compress=True)
(OUT/'processed-models.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),'utf8')
print('LIBRARY_READY',OUT,flush=True)
