"""One connected idea3 art scene, genuine imported heroes, authored support geometry."""
from pathlib import Path
import bpy,math,mathutils,json,random,os,hashlib,collections,numpy as np
from mathutils import Vector
ROOT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗')
DEL=ROOT/'07_技术交付';OUT=DEL/'01_场景与模型';QA=DEL/'06_验收与预览'
QA.mkdir(parents=True,exist_ok=True);(DEL/'05_技术接入').mkdir(exist_ok=True)
random.seed(31)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.name='Idea3_这店不太对';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.fps=30;scene.frame_end=180
COL={}
for name in ['01_Structure','02_Fixtures','03_Props','04_Characters','05_Lighting','06_InteractionSockets','07_Cameras','08_Roof_Toggle','09_FrontWall_Toggle']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);COL[name]=c
current=COL['01_Structure'];solids=[];instances=[];sockets=[];doors=[];lights=[];cams=[];cube_cache={};cylinder_cache={}
def link(o,col=None):
    for c in list(o.users_collection):c.objects.unlink(o)
    (col or current).objects.link(o);return o
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def rgb(h):return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))
def mat(name,h,emission=0,rough=.84):
    m=bpy.data.materials.new('I3_'+name);m.diffuse_color=(*rgb(h),1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb(h),1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=0
    if emission:p.inputs['Emission Color'].default_value=(*rgb(h),1);p.inputs['Emission Strength'].default_value=emission
    return m
M={k:mat(k,h,e) for k,h,e in [('wall','677968',0),('purple','6E5879',0),('dark','34443E',0),('paper','D8D0B8',0),('orange','E0A05B',0),('cyan','9AC5C0',0),('floor','7D897C',0),('metal','49574F',0),('lamp','B8DFD3',3),('warm_lamp','E0A05B',3),('cold_lamp','9AC5C0',2),('black','212729',0)]}
floorM=[mat('floor_'+str(i),h) for i,h in enumerate(['758373','7C8877','7A8778','818C7D','758174'])]
packM=[mat('pack_'+str(i),h) for i,h in enumerate(['C09247','AD6A47','6C6189','597E66','61949A','D3A047','48665C','B2A089','855975','657C90','BC793C','537C81'])]
atlas_source=OUT/'Textures/Shelf_Packaging_AI_Source.png'
im0=bpy.data.images.load(str(atlas_source));w,h=im0.size;px=np.empty(w*h*4,dtype=np.float32);im0.pixels.foreach_get(px);px=px.reshape(h,w,4)
idx_x=np.minimum(((np.arange(256)+.5)*w/256).astype(int),w-1);idx_y=np.minimum(((np.arange(256)+.5)*h/256).astype(int),h-1)
atlas=bpy.data.images.new('I3_Packaging_Atlas',width=256,height=256);atlas.colorspace_settings.name='sRGB';atlas.pixels.foreach_set(px[idx_y[:,None],idx_x[None,:]].ravel());atlas.update();atlas.filepath_raw=str(OUT/'Textures/Shelf_Packaging_Atlas_256.png');atlas.file_format='PNG';atlas.save();atlas.pack()
bpy.data.images.remove(im0)
atlasmat=mat('Packaging_AI_Atlas','FFFFFF');node=atlasmat.node_tree.nodes.new('ShaderNodeTexImage');node.image=atlas;node.interpolation='Closest';atlasmat.node_tree.links.new(node.outputs['Color'],atlasmat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
label_meshes={}
def package_label(name,loc,width,height,tile):
    tile=tile%12
    if tile not in label_meshes:
        me=bpy.data.meshes.new('PACK_UV_'+str(tile));me.from_pydata([(-.5,0,-.5),(.5,0,-.5),(.5,0,.5),(-.5,0,.5)],[],[(0,1,2,3)]);me.materials.append(atlasmat)
        uv=me.uv_layers.new(name='UVMap');u=(tile%4)/4;v=1-(tile//4+1)/4
        for loop,co in zip(uv.data,[(u+.006,v+.006),(u+.244,v+.006),(u+.244,v+.244),(u+.006,v+.244)]):loop.uv=co
        label_meshes[tile]=me
    ob=bpy.data.objects.new(name,label_meshes[tile]);current.objects.link(ob);ob.location=loc;ob.scale=(width,1,height);return ob
def box(name,loc,dim,material=None,solid=False,col=None):
    key=material.name if material else '_blank'
    if key not in cube_cache:
        mesh=bpy.data.meshes.new('UNIT_BOX_'+key);mesh.from_pydata([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
        if material:mesh.materials.append(material)
        cube_cache[key]=mesh
    o=bpy.data.objects.new(name,cube_cache[key]);(col or current).objects.link(o);o.location=loc;o.scale=dim
    o['art_role']='support_geometry'
    if solid and loc[2]+dim[2]/2>.12:solids.append({'name':name,'center':list(loc),'size':list(dim),'kind':'Box','source':'layout_geometry'})
    return o
def cyl(name,loc,r,depth,material,vertices=8,col=None):
    key=(vertices,material.name)
    if key not in cylinder_cache:
        vs=[(math.cos(i*2*math.pi/vertices),math.sin(i*2*math.pi/vertices),z) for z in [-.5,.5] for i in range(vertices)]
        fs=[tuple(reversed(range(vertices))),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
        me=bpy.data.meshes.new('CYL_'+str(key));me.from_pydata(vs,[],fs);me.materials.append(material);me.update();cylinder_cache[key]=me
    o=bpy.data.objects.new(name,cylinder_cache[key]);(col or current).objects.link(o);o.location=loc;o.scale=(r,r,depth);return o
def empty(name,loc,col=None):
    o=bpy.data.objects.new(name,None);(col or current).objects.link(o);o.location=loc;o.empty_display_size=.12;return o
def label(text,name,loc,size=.16,rot=(math.pi/2,0,0),material=None):
    bpy.ops.object.text_add(location=loc,rotation=rot);o=link(bpy.context.object,COL['02_Fixtures']);o.name=name;o.data.body=text;o.data.size=size;o.data.extrude=.001;o.data.align_x='CENTER'
    for fontpath in ['C:/Windows/Fonts/msyh.ttc','C:/Windows/Fonts/simhei.ttf']:
        if Path(fontpath).exists():o.data.font=bpy.data.fonts.load(fontpath);break
    o.data.materials.append(material or M['paper']);return o

def mosaic(name,loc,width,height,vertical=True,yaw=0,colors=None,step=.15,col=None):
    # Native low-poly pixel panels: exported geometry, not a render-only shader.
    colors=colors or wallM;vs=[];fs=[];mi=[];nx=max(1,round(width/step));ny=max(1,round(height/step));dx=width/nx;dy=height/ny
    for iy in range(ny):
        for ix in range(nx):
            x=-width/2+ix*dx;y=-height/2+iy*dy;k=len(vs)
            pts=[(x,y),(x+dx,y),(x+dx,y+dy),(x,y+dy)]
            vs.extend([(a,0,b) if vertical else (a,b,0) for a,b in pts]);fs.append((k,k+1,k+2,k+3));mi.append(random.randrange(len(colors)))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs)
    for ma in colors:me.materials.append(ma)
    for p,m in zip(me.polygons,mi):p.material_index=m
    me.update();o=bpy.data.objects.new(name,me);(col or current).objects.link(o);o.location=loc;o.rotation_euler.z=math.radians(yaw);return o

wallM=[mat('wall_pixel_'+str(i),h) for i,h in enumerate(['617363','647666','677968','6A7B6B','6C7D6D','657767'])]
def symbol(kind,loc,size=.11,flat=False,material=None,name='SYMBOL'):
    x,y,z=loc;ma=material or {'circle':M['orange'],'bar':M['cyan'],'square':M['purple']}[kind]
    if kind=='circle':
        o=cyl(name,loc,size/2,.004,ma,vertices=12,col=COL['03_Props'])
        if not flat:o.rotation_euler.x=math.pi/2
    else:
        dims=(size,.004,size if kind=='square' else size*.23) if not flat else (size,size if kind=='square' else size*.23,.004)
        o=box(name,loc,dims,ma,col=COL['03_Props'])
    return o
def socket(name,loc,event,action,owner=None,symbol_id=None):
    o=empty(name,loc,COL['06_InteractionSockets']);o.empty_display_type='SPHERE';o['event_id']=event;o['action']=action;o['range_m']=1.8
    row={'name':name,'position_blender':list(loc),'position_unity':[loc[0],loc[2],-loc[1]],'event':event,'action':action,'owner':owner,'symbol':symbol_id,'range_m':1.8}
    sockets.append(row);return o
templates={}
def load_template(aid,char=False):
    if aid in templates:return templates[aid]
    file=DEL/'02_角色与动画'/aid/(aid+'_Rigged.blend') if char else OUT/'Models'/aid/(aid+'.blend')
    assert file.exists(),file
    with bpy.data.libraries.load(str(file),link=False) as (src,dst):
        assert aid in src.collections,(aid,src.collections);dst.collections=[aid]
    c=dst.collections[0];templates[aid]=c;return c
def instance(aid,name,pos,yaw=0,char=False,solid_size=None):
    c=load_template(aid,char);target=COL['04_Characters'] if char else COL['03_Props'];root=empty(name,pos,target);root.rotation_euler.z=math.radians(yaw);root['asset_id']=aid;mapping={}
    for o in c.objects:
        n=o.copy();n.name=name+'__'+o.name.replace(aid+'_','');target.objects.link(n);mapping[o]=n
        if not char:n.animation_data_clear()
    for o,n in mapping.items():
        n.parent=mapping.get(o.parent,root)
        for mod in n.modifiers:
            if hasattr(mod,'object') and mod.object in mapping:mod.object=mapping[mod.object]
        for con in n.constraints:
            if hasattr(con,'target') and con.target in mapping:con.target=mapping[con.target]
    instances.append({'id':name,'asset_id':aid,'position':list(pos),'yaw_degrees':yaw,'objects':[o.name for o in mapping.values()]})
    if solid_size:solids.append({'name':name,'center':[pos[0],pos[1],pos[2]+solid_size[2]/2],'size':list(solid_size),'kind':'Box','source':'furniture_clearance'})
    return root,mapping
def wall_h(y,x0,x1,h=3,col=None):
    if x1-x0<.01:return
    box('WALL_H_'+str(y)+'_'+str(x0),((x0+x1)/2,y,h/2),(x1-x0,.16,h),M['wall'],True,col)
    box('WALL_TRIM_H_'+str(y)+'_'+str(x0),((x0+x1)/2,y,h-.13),(x1-x0,.20,.12),M['purple'],False,col)
    box('SKIRT_H_'+str(y)+'_'+str(x0),((x0+x1)/2,y-.095,.15),(x1-x0,.04,.3),M['dark'],False,col)
    for sy in [-1,1]:mosaic('WALL_PIXEL_H_'+str(y)+'_'+str(x0)+'_'+str(sy),((x0+x1)/2,y+sy*.081,h/2),x1-x0,h,col=col)
def wall_v(x,y0,y1,h=3,col=None):
    if y1-y0<.01:return
    box('WALL_V_'+str(x)+'_'+str(y0),(x,(y0+y1)/2,h/2),(.16,y1-y0,h),M['wall'],True,col)
    box('WALL_TRIM_V_'+str(x)+'_'+str(y0),(x,(y0+y1)/2,h-.13),(.20,y1-y0,.12),M['purple'],False,col)
    box('SKIRT_V_'+str(x)+'_'+str(y0),(x+.095,(y0+y1)/2,.15),(.04,y1-y0,.3),M['dark'],False,col)
    for sx in [-1,1]:mosaic('WALL_PIXEL_V_'+str(x)+'_'+str(y0)+'_'+str(sx),(x+sx*.081,(y0+y1)/2,h/2),y1-y0,h,yaw=90,col=col)
# Exact one-floor 14 x 20 metre envelope; source objects are not substituted by primitives.
box('FOUNDATION',(7,10,-.175),(14.3,20.3,.28),M['dark'])
for x in range(28):
    for y in range(40):
        box('TILE_%02d_%02d'%(x,y),(x*.5+.25,y*.5+.25,-.015),(.492,.492,.03),random.choice(floorM))
        mosaic('FLOOR_PIX_%02d_%02d'%(x,y),(x*.5+.25,y*.5+.25,.0004),.488,.488,False,colors=floorM,step=.125)
wall_v(0,0,20);wall_v(14,0,20);wall_h(20,0,14)
wall_h(9,0,3.6);wall_h(9,5.2,10.3);wall_h(9,11.9,14)
wall_v(8,9,11.3);wall_v(8,12.9,16)
wall_h(16,0,3.6);wall_h(16,5.2,10.3);wall_h(16,11.9,14)
# Front glazing / low wall, kept in a dedicated cutaway collection.
front=COL['09_FrontWall_Toggle']
for a,b in [(0,5.7),(8.3,14)]:
    wall_h(0,a,b,.55,front)
    box('FRONT_HEADER_'+str(a),((a+b)/2,0,2.8),(b-a,.2,.4),M['purple'],False,front)
    for x in [a+.1,(a+b)/2,b-.1]:box('WINDOW_MULLION_'+str(x),(x,0,1.65),(.1,.15,2.2),M['dark'],False,front)
    # Keep glass subtle so it does not obstruct the cutaway/first-person image.
    glass=mat('front_glass_'+str(a),'9AC5C0',0,.3);p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.16;glass.surface_render_method='DITHERED'
    box('WINDOW_GLASS_'+str(a),((a+b)/2,0,1.65),(b-a-.2,.012,2.05),glass,False,front)
for x in [5.7,8.3]:box('ENTRANCE_FRAME_'+str(x),(x,0,1.25),(.1,.2,2.5),M['purple'],False,front)
label('夜班便民店','STORE_TITLE',(7,-.12,2.67),.30,material=M['orange'])
box('ENTRY_MAT',(7,.9,.01),(2.1,1.15,.02),M['dark'])
for xa,xb in [(0,5.7),(8.3,14)]:box('SHOP_FRONT_SILL',((xa+xb)/2,-.17,.16),(xb-xa,.42,.32),M['purple'],False,front)
for xx in [5.72,8.28]:box('DOOR_RAIL',(xx,-.03,1.25),(.085,.085,2.5),M['dark'],False,front)
box('DOOR_HEADER',(7,-.03,2.54),(2.64,.16,.20),M['dark'],False,front)
box('SIGN_HEADER',(7,-.04,2.83),(2.45,.15,.37),M['purple'],False,front)
for x in [6.1,6.4,6.7,7,7.3,7.6,7.9]:box('MAT_LINE_'+str(x),(x,.9,.024),(.045,1.0,.006),M['wall'])
# Ceiling is real, separately toggled for an overview rather than omitted.
for label_id,loc,dim in [('FRONT',(7,4.5,3.04),(14,9,.08)),('WAREHOUSE',(4,12.5,3.04),(8,7,.08)),('COLD',(11,12.5,3.04),(6,7,.08)),('LOADING',(7,18,3.04),(14,4,.08))]:box('CEILING_'+label_id,loc,dim,M['wall'],False,COL['08_Roof_Toggle'])
def door(name,pos,yaw=0):
    root=empty(name,pos,COL['02_Fixtures']);root.rotation_euler.z=math.radians(yaw)
    for suf,loc,dim in [('LEFT',(-.75,0,1.15),(.10,.16,2.3)),('RIGHT',(.75,0,1.15),(.10,.16,2.3)),('TOP',(0,0,2.25),(1.6,.16,.1))]:
        p=box(name+'_'+suf,loc,dim,M['purple'],col=COL['02_Fixtures']);p.parent=root
    hinge=empty(name+'_HINGE',(-.69,0,0),COL['02_Fixtures']);hinge.parent=root;hinge.rotation_euler.z=math.radians(-100)
    panel=box(name+'_PANEL',(.69,0,1.06),(1.37,.055,2.10),M['wall'],col=COL['02_Fixtures']);panel.parent=hinge
    for nm,loc,dim,ma in [('WINDOW',(.7,-.035,1.52),(.52,.02,.38),M['cyan']),('HANDLE',(1.2,-.07,1.0),(.065,.12,.21),M['orange']),('STRIPE',(.7,-.034,.45),(1.1,.01,.07),M['purple'])]:
        p=box(name+'_'+nm,loc,dim,ma,col=COL['02_Fixtures']);p.parent=hinge
    doors.append({'id':name,'hinge':hinge.name,'frame':root.name,'position':list(pos),'yaw_degrees':yaw,'clear_width_m':1.40,'clear_height_m':2.2,'open_angle_blender_degrees':-100,'axis':'Z','initial_state':'open','safe_sweep_radius_m':1.4})
    return root
door('GATE_BC',(8,12.1,0),90);door('GATE_BD',(4.4,16,0),0)
for nm,pos,txt in [('AB',(4.4,8.88,2.5),'后仓'),('AC',(11.1,8.88,2.5),'冷库'),('BD',(4.4,15.88,2.5),'卸货'),('CD',(11.1,15.88,2.5),'交接出口')]:
    box('AREA_SIGN_'+nm,pos,(1.3,.06,.35),M['dark'],col=COL['02_Fixtures']);label(txt,'AREA_LABEL_'+nm,(pos[0],pos[1]-.04,pos[2]-.1),.2)
# Quiet support fixtures, clean silhouettes, repeated low-budget geometry.
current=COL['02_Fixtures']
box('CHECKOUT_COUNTER',(2.25,2.65,.43),(2.4,.75,.86),M['wall'],True)
box('CHECKOUT_TOP',(2.25,2.65,.895),(2.48,.82,.07),M['paper'])
box('CHECKOUT_FRONT_INSET',(2.25,2.26,.43),(2.18,.016,.55),M['purple'])
for x in [1.35,2.25,3.15]:box('COUNTER_PANEL_LINE_'+str(x),(x,2.24,.43),(.025,.012,.55),M['dark'])
label('欢迎光临','COUNTER_LABEL',(2.25,2.235,.48),.14)
def shelf(name,pos,levels=4,width=1.8,depth=.62,height=1.7,products=True,yaw=0):
    x,y,z=pos
    before=set(bpy.data.objects)
    for dx in [-width/2+.045,width/2-.045]:
        for dy in [-depth/2+.03,depth/2-.03]:box(name+'_POST',(x+dx,y+dy,z+height/2),(.06,.06,height),M['metal'])
    box(name+'_BACK',(x,y+depth/2,z+height/2),(width,.035,height),M['wall'])
    for tier in range(levels):
        zz=z+.18+tier*(height-.28)/levels
        box(name+'_SHELF_'+str(tier),(x,y,zz),(width,depth,.045),M['purple'])
        box(name+'_EDGE_'+str(tier),(x,y-depth/2-.015,zz+.025),(width,.032,.07),M['paper'])
        if products:
            count=max(6,int((width-.12)/.145))
            for row in range(3):
                for j in range(count):
                    xx=x-width/2+.10+j*(width-.17)/count;yy=y-depth/2+.10+row*.15;ma=packM[(j//3+tier*3)%12];typ=(j//3+tier)%4
                    tag=name+'_%d_%d_%d'%(tier,row,j);ht=[.24,.29,.20,.26][typ]
                    if typ in [0,2]:
                        o=cyl(tag,(xx,yy,zz+.025+ht/2),.055,ht,ma,8)
                        if typ==0:box(tag+'_CAP',(xx,yy,zz+.035+ht),(.06,.06,.035),M['purple'])
                    else:o=box(tag,(xx,yy,zz+.025+ht/2),(.12,.125,ht),ma)
                    if row==0:
                        package_label(tag+'_AI_LABEL',(xx,yy-.0655,zz+.025+ht/2),.112,ht*.87,(j//3+tier*3)%12)
            for j in range(max(2,count//3)):
                xx=x-width/2+.27+j*.42;box(name+'_PRICE',(xx,y-depth/2-.035,zz+.025),(.12,.008,.035),M['orange' if tier==1 else 'paper'])
    for j in range(max(3,int(width/.29))):
        xx=x-width/2+.18+j*.27;box(name+'_TOP_PACK',(xx,y,z+height-.005),(.23,.30,.26),packM[j%12])
        package_label(name+'_TOP_AI',(xx,y-.154,z+height),.22,.24,j%12)
    if yaw:
        rot=mathutils.Matrix.Rotation(math.radians(yaw),4,'Z')
        for o in set(bpy.data.objects)-before:o.location=Vector(pos)+rot.to_3x3()@(o.location-Vector(pos));o.rotation_euler.z+=math.radians(yaw)
    sz=[width,depth,height] if yaw%180==0 else [depth,width,height]
    solids.append({'name':name,'center':[x,y,z+height/2],'size':sz,'kind':'Box','source':'support_fixture'})
shelf('SHELF_A1',(5.0,5.8,0),width=3.0,yaw=90)
shelf('SHELF_A2',(9.7,5.7,0),width=2.6)
shelf('SHELF_A3',(12.55,6.4,0),width=2.5,yaw=90)
shelf('SHELF_A4',(9.5,2.25,0),width=2.3)
shelf('SHELF_A5',(2.1,6.2,0),width=2.4)
shelf('SHELF_A6',(12.9,1.45,0),width=1.8,yaw=90)
shelf('SHELF_A7',(7.9,7.8,0),width=1.8)
shelf('COUNTER_SIDE_STOCK',(.5,3.45,0),width=1.6,height=1.30,yaw=90)
shelf('BACK_STORAGE',(1.5,14.6,0),3,2.5,.70,1.8)
shelf('COLD_WALL_STOCK',(8.65,14.35,0),4,2.2,.65,1.9,yaw=90)
# Context from approved overview: repeat stock, ceiling beams, wall signs and warm shopfront.
for yy in [3.4,6.9,12.7,17.9]:box('CEILING_BEAM',(7,yy,2.93),(14,.12,.12),M['dark'])
for xx in [1.0,4.7,9.2,13.0]:
    box('EXTERIOR_POST',(xx,-.2,1.4),(.20,.35,2.8),M['purple'],col=COL['09_FrontWall_Toggle'])
    box('EXTERIOR_AMBER_LAMP',(xx,-.42,1.85),(.12,.09,.32),M['warm_lamp'],col=COL['09_FrontWall_Toggle'])
for text_,p in [('晚班也很重要',(1.0,5.8,1.8)),('仅供观察',(6.4,8.85,1.8)),('空气请轻放',(1.3,15.86,1.65)),('不用着急',(13.84,9.9,1.8))]:
    board=box('NOTICE_BOARD',p,(.52,.035,.69),M['paper']);label(text_,'NOTICE_TEXT',(p[0],p[1]-.025,p[2]),.085,material=M['dark'])
# Fine but disciplined environment details: flat conduit, vents, receipts, labels, not high-poly clutter.
for x,y in [(.15,5.8),(.15,12.5),(13.85,6.5),(13.85,12.5)]:
    box('ELECTRIC_BOX',(x,y,1.6),(.18,.24,.34),M['purple']);box('CONDUIT',(x,y,2.25),(.045,.045,.96),M['dark'])
for x,y in [(2,19.85),(9.0,15.87),(13.85,12.9)]:
    v=box('VENT',(x,y,2.6),(.5,.08,.3),M['dark'])
    for j in range(4):box('VENT_SLAT',(x,y-.05,2.5+j*.055),(.43,.025,.018),M['wall'])
for x,y in [(3.5,1.0),(12.8,3.0)]:
    box('BASKET_STACK',(x,y,.28),(.40,.32,.56),M['purple'])
    for j in range(5):box('BASKET_EDGE',(x,y-.167,.10+j*.09),(.42,.03,.018),M['dark'])
# Imported heroes and core operation props.
current=COL['03_Props']
instance('CHR_CLERK_COW','COW_CLERK',(2.25,3.70,0),char=True)
instance('CHR_BOX_CUSTOMER','BOX_CUSTOMER',(12.25,3.6,0),yaw=-90,char=True)
instance('PRP_REGISTER_FACE','REGISTER',(3.0,2.64,.932))
clip,_=instance('PRP_SHIFT_CLIPBOARD','CLIPBOARD',(1.9,2.49,.945));clip.rotation_euler.x=math.radians(68)
for i,kind in enumerate(['circle','bar','square']):
    c,_=instance('PRP_SYMBOL_CARD_SET','CARD_'+kind,(1.22+i*.19,2.48,.953));c.rotation_euler.x=math.pi/2
    symbol(kind,(1.22+i*.19,2.423,1.009),.065,True,name='CARD_FACE_'+kind)
    socket('SLOT_CLIPBOARD_'+kind,(1.9,2.43+i*.045,1.02),'E01','place_symbol_card','CLIPBOARD',kind)
    socket('TAKE_CARD_'+kind,(1.22+i*.19,2.48,1.00),'E01','take_card','CARD_'+kind,kind)
    # Scanner sample bottles, three simple reusable packaging meshes.
    xx=2.55+i*.21;cyl('SCAN_SAMPLE_'+kind,(xx,2.14,1.06),.06,.24,packM[i*3],8)
    symbol(kind,(xx,2.075,1.09),.042,name='SAMPLE_FACE_'+kind)
    socket('SCAN_SAMPLE_'+kind,(xx,2.14,1.07),'E03','scan_sample','REGISTER',kind)
socket('EVT_E02_COW',(2.25,3.0,1.5),'E02','confirm_shift_with_cow','COW_CLERK')
socket('EVT_E03_REGISTER',(3,2.18,1.10),'E03','scan_and_print','REGISTER')
socket('SLOT_RECEIPT',(3.10,2.22,.96),'E03','take_combined_receipt','REGISTER')
box('RECEIPT_REST',(3.12,2.10,.955),(.12,.25,.004),M['paper'])
box('QUEUE_SIGN_BASE',(11.4,3.3,.045),(.45,.34,.09),M['purple'])
box('QUEUE_SIGN_POST',(11.4,3.3,.40),(.05,.05,.7),M['metal'])
qs,_=instance('PRP_ROUTE_SIGN_SET','QUEUE_DIRECTION',(11.4,3.3,.75),yaw=-90)
socket('EVT_E04_QUEUE_SIGN',(11.4,3.3,.83),'E04','turn_queue_toward_door','QUEUE_DIRECTION')
socket('EVT_E04_CUSTOMER',(12.05,3.6,.70),'E04','show_receipt','BOX_CUSTOMER')
for idx,y in enumerate([2.5,3.1,3.7]):
    for dx in [-.13,.13]:box('QUEUE_FOOTPRINT_'+str(idx),(12.25+dx,y,.011),(.10,.22,.007),M['orange'])
# Warehouse three low positions, all within short sightlines of real exits.
for i,kind in enumerate(['circle','bar','square']):
    x=1.25+i*1.35;y=11.15
    box('CRATE_STAND_'+kind,(x,y,.18),(.85,.65,.36),M['purple'],True)
    instance('PRP_CARGO_CRATE','CARGO_'+kind,(x,y,.36))
    symbol(kind,(x,y-.242,.58),.15,name='CARGO_FACE_'+kind)
    box('BAY_MARK_'+kind,(x,12.3,.018),(.80,.70,.036),M['dark'])
    symbol(kind,(x,12.3,.04),.28,True,name='BAY_SYMBOL_'+kind)
    socket('EVT_E05_TAKE_'+kind,(x,y,.7),'E05','take_crate','CARGO_'+kind,kind)
    socket('SLOT_E05_BAY_'+kind,(x,12.3,.245),'E05','place_matching_crate','CARGO_'+kind,kind)
    socket('EVT_E07_LID_'+kind,(x,y,.91),'E07','open_insert_card_close','CARGO_'+kind,kind)
for i,(p,rot) in enumerate([((6.4,9.6,1.65),0),((7.5,11.0,1.65),-90),((2.8,15.4,1.65),0),((6.4,15.35,1.65),0)]):
    instance('PRP_ROUTE_SIGN_SET','ROUTE_'+str(i+1),p,rot);socket('EVT_E06_ROUTE_'+str(i+1),p,'E06','turn_arrow_to_visible_exit','ROUTE_'+str(i+1))
cart,_=instance('PRP_HAND_CART','HAND_CART',(6.05,13.8,0),yaw=0,solid_size=(.75,1.1,1.0))
cart_slots=[(6.05,13.53,.312),(6.05,14.07,.312),(6.05,13.8,.675)]
for i,p in enumerate(cart_slots):socket('SLOT_CART_'+str(i+1),p,'E08','snap_crate_2bottom_1upper','HAND_CART',['circle','bar','square'][i])
socket('EVT_E08_CART',(6.05,14.5,.9),'E08','take_control_cart','HAND_CART')
# Coldroom: fridge is the source narrow design, proportional fit by 2.1m height.
fridge,frparts=instance('PRP_FRIDGE','SINGING_FRIDGE',(12.7,14.7,0),yaw=0,solid_size=(.87,1.21,2.1))
for ob in frparts.values():
    if ob.name.endswith('Door'):ob.rotation_euler.z=math.radians(-70)
for i,kind in enumerate(['circle','bar','square']):
    pos=(12.47+i*.23,14.43,1.07);cyl('FRIDGE_BOTTLE_'+kind,pos,.07,.26,M['cyan'],8)
    symbol(kind,(pos[0],pos[1]-.079,pos[2]+.025),.055,name='COLD_BOTTLE_SYMBOL_'+kind)
    socket('EVT_E09_BOTTLE_'+kind,pos,'E09','confirm_symbol_bottle','SINGING_FRIDGE',kind)
socket('EVT_E09_FRIDGE_DOOR',(12.45,14.07,1.1),'E09','open_fridge','SINGING_FRIDGE')
box('MILK_LOW_TABLE',(10.5,13.5,.60),(1.85,.90,.07),M['metal'],True)
for x in [9.73,11.27]:
    for y in [13.12,13.88]:box('MILK_TABLE_LEG',(x,y,.30),(.07,.07,.60),M['purple'])
for i in range(5):
    x=9.8+i*.35;y=13.60
    instance('PRP_ODD_PRODUCT','MILK_'+str(i+1),(x,y,.64),char=True)
    kind=['circle','bar','square','bar','circle'][i]
    symbol(kind,(x,y-.058,.775),.035,name='MILK_SYMBOL_'+str(i+1))
    socket('EVT_E10_MILK_'+str(i+1),(x,y,.82),'E10','take_after_two_short_steps','MILK_'+str(i+1),kind)
box('COLD_CART_PARK',(9.65,10.4,.008),(1.10,1.7,.016),M['dark'])
for x in [9.10,10.2]:box('PARK_LINE',(x,10.4,.021),(.025,1.7,.009),M['cyan'])
socket('SLOT_COLD_CART',(9.65,10.4,0),'E08','park_full_cart','HAND_CART')
for i,kind in enumerate(['circle','bar','square']):socket('EVT_E11_SEAL_'+kind,(9.65,10.0+i*.4,.95),'E11','return_milk_then_cold_seal','HAND_CART',kind)
socket('EVT_E11_CLOSE_FRIDGE',(12.45,14.07,1.1),'E11','close_after_three_seals','SINGING_FRIDGE')
for d in doors:socket('EVT_E12_'+d['id'],(d['position'][0],d['position'][1],1.1),'E12','open_safe_door',d['id'])
# Loading finale: separate wait slots and final pallet, never double-count unload.
instance('PRP_WEIGH_SCALE','WEIGH_SCALE',(2.3,18.45,0),solid_size=(1.16,1.4,1.25))
instance('PRP_STAMP_STATION','STAMP_STATION',(4.1,18.8,0),solid_size=(.50,.58,.9))
instance('PRP_LOADING_PALLET','FINAL_PALLET',(9.2,18.55,0),solid_size=(1.1,.9,.14))
# Reuse actual supplied cargo models for dense normal stock, without new hero designs.
for x,y in [(1.1,13.2),(2.15,13.2),(3.2,14.65),(.8,17.5),(.8,18.3),(13.1,18.5),(12.35,19.25)]:
    for tier in range(2 if y<16 else 3):
        r,parts=instance('PRP_CARGO_CRATE','STOCK_CRATE_%s_%s_%s'%(x,y,tier),(x,y,tier*.365))
        for ob in parts.values():
            if ob.name.endswith('Lid'):ob.rotation_euler.x=math.radians(41.5)
    solids.append({'name':'STOCK_STACK_'+str((x,y)),'center':[x,y,.5],'size':[.55,.45,1.1],'kind':'Box','source':'decor_stock'})
box('LOADING_SHUTTER',(6.7,19.86,1.1),(2.1,.045,2.2),M['metal'])
for zz in np.arange(.12,2.2,.14):box('SHUTTER_SLAT',(6.7,19.827,float(zz)),(2.06,.025,.025),M['dark'])
for xx in [5.45,7.95]:
    box('LOADING_BOLLARD',(xx,19.7,.5),(.12,.12,1),M['orange'])
    for zz in [.25,.55,.85]:box('BOLLARD_STRIPE',(xx,19.63,zz),(.125,.012,.10),M['dark'])
for j in range(8):box('DOCK_CAUTION_MARK',(5.5+j*.31,18.05,.006),(.19,.13,.012),M['orange'])
socket('SLOT_E12_PARK',(6.2,18.2,0),'E12','park_for_weighing','HAND_CART')
socket('EVT_E13_WEIGH',(2.3,18.05,.44),'E13','weigh_single_crate','WEIGH_SCALE')
socket('EVT_E13_STAMP',(4.1,18.5,.63),'E13','insert_ticket_stamp_take','STAMP_STATION')
for i,kind in enumerate(['circle','bar','square']):
    x=5.6+i*.8;box('WAIT_SLOT_'+kind,(x,19.35,.02),(.6,.5,.04),M['purple']);socket('SLOT_WAIT_'+kind,(x,19.35,.265),'E13','wait_before_final_unload',None,kind)
    dx,dy=[(-.275,-.225),(.275,-.225),(-.275,.225)][i]
    symbol(kind,(9.2+dx,18.55+dy,.147),.14,True,name='FINAL_SLOT_MARK_'+kind)
    socket('SLOT_FINAL_'+kind,(9.2+dx,18.55+dy,.365),'E14','final_unload','FINAL_PALLET',kind)
socket('EVT_E14_CUSTOMER',(10.35,18.55,.72),'E14','show_complete_ticket','BOX_CUSTOMER')
socket('EVT_E14_COW',(2.25,3,1.5),'E14','return_shift_sheet','COW_CLERK')
socket('EVT_E14_FINISH',(1.9,2.43,1.05),'E14','end_shift','CLIPBOARD')
empty('BOX_CUSTOMER_END_MARKER',(10.35,18.55,0),COL['06_InteractionSockets'])
empty('PLAYER_START',(7,1.6,1.65),COL['06_InteractionSockets'])
# Subtle emissive practicals plus actual lights. No flashing or full-screen fog.
def light(name,loc,power,color,size=3,target=None):
    bpy.ops.object.light_add(type='AREA',location=loc);o=link(bpy.context.object,COL['05_Lighting']);o.name=name;o.data.energy=power;o.data.color=rgb(color);o.data.shape='DISK';o.data.size=size
    if target:o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    lights.append({'name':name,'type':'area_preview','position':list(loc),'energy_blender_w':power,'srgb_hex':color,'size_m':size,'unity_note':'Bake static indirect; rebuild runtime lights/probes from lighting-profile, not raw watts.'});return o
for idx,(x,y) in enumerate([(3,3.9),(10.5,4.5),(4.2,11.8),(11.2,12),(4.0,18.0),(11.0,18.0)]):
    box('FLUORESCENT_HOUSING_'+str(idx),(x,y,2.82),(1.26,.22,.12),M['dark'],col=COL['05_Lighting'])
    box('FLUORESCENT_TUBE_'+str(idx),(x,y,2.753),(1.13,.09,.02),M['lamp'],col=COL['05_Lighting'])
    for dx in [-.48,.48]:box('LAMP_CABLE_'+str(idx),(x+dx,y,2.95),(.018,.018,.24),M['metal'],col=COL['05_Lighting'])
    light('LIGHT_FLUOR_'+str(idx),(x,y,2.65),155,'CBDED0',3.5)
light('LIGHT_COUNTER_WARM',(2,1.75,2.55),105,'E0A05B',2,(2.25,3.5,1.1))
light('LIGHT_COLD_FILL',(12.5,13.8,2.25),90,'9AC5C0',1.8,(11.2,12.9,.65))
light('LIGHT_LOADING_WARM',(8.7,18.8,2.6),100,'E0A05B',2.8)
for x in [1.0,4.7,9.2,13.0]:light('LIGHT_SHOPFRONT_'+str(x),(x,.25,1.9),90,'FFA750',1.5,(x,2.5,.7))
light('LIGHT_BACK_ORANGE',(6.5,18.8,2.5),180,'FFAD55',4)
light('LIGHT_COLD_CABINET',(12.7,14.1,1.8),45,'A8F4DF',.8,(12.6,13.4,.8))
light('LIGHT_FRONT_SOFT',(7,5,2.85),55,'DCE5D8',7)
world=bpy.data.worlds.new('I3_Night_Exterior');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(*rgb('78938C'),1);world.node_tree.nodes['Background'].inputs[1].default_value=.32
def camera(name,pos,target,ortho=None,lens=28):
    bpy.ops.object.camera_add(location=pos);o=link(bpy.context.object,COL['07_Cameras']);o.name=name;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;o.data.clip_end=150
    if ortho:o.data.type='ORTHO';o.data.ortho_scale=ortho
    cams.append({'name':name,'position':list(pos),'look_at':list(target),'lens_mm':lens,'ortho_scale':ortho});return o
overview=camera('CAM_00_Cutaway',(19,-31,34),(7,10,.6),27)
camera('CAM_01_Checkout',(5.7,.85,1.68),(2.4,3.1,1.15),lens=25)
camera('CAM_02_Customer',(9.0,1.1,1.35),(11.9,3.6,.63),lens=26)
camera('CAM_03_Warehouse',(6.8,10.0,1.62),(2.8,13.4,.9),lens=22)
camera('CAM_04_Coldroom',(9.1,10.0,1.6),(11.7,14,.95),lens=22)
camera('CAM_05_Milk',(10.40,11.9,.90),(10.5,13.60,.78),lens=36)
camera('CAM_06_Loading',(12.4,17.0,1.6),(5.2,18.7,.75),lens=22)
camera('CAM_07_Plan',(7,10,28),(7,10,0),32)
# Data contract contains exact instance IDs and socket coordinates, not a fake playable game.
EVENT_NAMES=['三符号交班单','过度郑重欢迎','三样品扫码打印','纠正排队方向','三箱匹配货位','路牌指向出口','开空箱插卡合盖','装车与冷库停靠','冰柜三符号点名','取三只走路奶盒','逐箱冷封并关门','推车经门到卸货','逐箱称重盖章','卸到托盘并交回班单']
EVENT_FLAGS=['three_cards_slotted','sheet_presented_to_cow_and_register','three_samples_scanned_receipt_taken','sign_correct_customer_at_warehouse','three_crates_matched','two_exit_arrow_groups_correct','three_crates_carded_and_closed','three_crates_loaded_cart_cold_parked','three_bottles_confirmed','three_matching_milk_in_slots','three_cold_seals_fridge_closed','cart_at_loading_park','three_crates_weighted_and_stamped','three_final_slots_full_receipt_shown_sheet_returned_end_confirmed']
event_data=[]
for i in range(14):
    eid='E%02d'%(i+1);event_data.append({'id':eid,'title':EVENT_NAMES[i],'zone':['A']*4+['B']*4+['C']*3+['D']*3 if False else ('A' if i<4 else 'B' if i<8 else 'C' if i<11 else 'D'),'preconditions':[] if i==0 else ['E%02d_done'%i],'interact_targets':[r['name'] for r in sockets if r['event']==eid],'completion_flags':[EVENT_FLAGS[i],eid+'_done'],'allow_player_movement_during_cue':True,'wrong_action':'return_item_without_progress_loss','reset':'nearest safe transform / preserve confirmed flags','implemented_game_logic':False})
data={'title':'这店不太对','style':'A 低像素夜班','units':'m','axes':{'blender':'X right,Y depth,Z up; asset front -Y','unity':'X right,Y up,Z forward; Blender(x,y,z)->Unity(x,z,-y)'},'dimensions_m':[14,20,3],'zones':[{'id':'A','name':'前店','xy_bounds':[0,0,14,9]},{'id':'B','name':'后仓','xy_bounds':[0,9,8,16]},{'id':'C','name':'冷库','xy_bounds':[8,9,14,16]},{'id':'D','name':'卸货口','xy_bounds':[0,16,14,20]}],'instances':instances,'sockets':sockets,'door_clearances':doors,'suggested_colliders':solids,'cameras':cams,'events':event_data,'playtime':{'target_minutes':[24,30],'measured':False},'not_implemented':['WASD interaction runtime','event state machine','save system','collision & navmesh in engine','20min playtest'],'cart_slots_world':cart_slots}
(OUT/'scene-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
(DEL/'05_技术接入/event-contract.json').write_text(json.dumps(event_data,ensure_ascii=False,indent=2),'utf8')
(DEL/'05_技术接入/lighting-profile.json').write_text(json.dumps({'blender_preview_lights':lights,'recommended_unity':{'pipeline':'URP or Built-in with matching shader','ambient_color_srgb':'78938C','static_gi':'Bake room/fixtures','dynamic_probes':'Probe grid at .35/1.2/2.1m in all four zones','reflection_probes':'one per zone, blend distance1m','bloom':'subtle threshold1.2 intensity.08, optional','tonemapping':'Neutral/AgX comparison required','texture_filter':'Point, check mip shimmer','metallic':0,'smoothness':.16,'area_lights_not_runtime_portable':True}},ensure_ascii=False,indent=2),'utf8')
# Portable textures, packed and visible by default.
# Latest Feishu-authoritative design supersedes all 14 task-chain sockets.
for ob in list(COL['06_InteractionSockets'].objects):bpy.data.objects.remove(ob,do_unlink=True)
for ob in list(scene.objects):
    if ob.name.startswith(('WAIT_SLOT_','FINAL_SLOT_MARK_','BAY_MARK_','BAY_SYMBOL_','COLD_CART_PARK','PARK_LINE')):bpy.data.objects.remove(ob,do_unlink=True)
data['events']=[];data['sockets']=[];data['playtime']={'measured':False,'minimum_guarantee':False};data['source_only']=True;data['current_design']='Feishu free exploration; final triggers in each Levels/*/scene-manifest.json; no tasks, fail state, collection gate'
(OUT/'scene-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
(DEL/'05_技术接入/event-contract.json').write_text(json.dumps({'superseded':True,'use':'Levels/*/scene-manifest.json','reason':'Latest user requires original Idea3 free exploration without task chain'},ensure_ascii=False,indent=2),'utf8')
for im in bpy.data.images:
    if im.source!='FILE':continue
    if not im.packed_file and Path(bpy.path.abspath(im.filepath)).is_file():im.pack()
    assert im.packed_file and im.size[0]>0,(im.name,im.filepath)
    src=Path(bpy.path.abspath(im.filepath))
    if src.exists():im.filepath='//'+os.path.relpath(src,OUT).replace('\\','/')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
            area.spaces.active.region_3d.view_distance=28;area.spaces.active.region_3d.view_location=(7,10,0);area.spaces.active.region_3d.view_rotation=overview.rotation_euler.to_quaternion()
COL['08_Roof_Toggle'].hide_render=True;COL['08_Roof_Toggle'].hide_viewport=True
COL['09_FrontWall_Toggle'].hide_render=True;COL['09_FrontWall_Toggle'].hide_viewport=True
scene.camera=overview;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.2
scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene['delivery_type']='SOURCE assembly only; final freely explorable level exports are in Levels/. Legacy task sockets removed by derive_three_levels.py';scene['roof_toggle']='08_Roof_Toggle / 09_FrontWall_Toggle hidden only for cutaway';scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Idea3_这店不太对_完整场景.blend'),compress=True)
# Export real hierarchy, including roof and walls. No collision proxy meshes added.
COL['08_Roof_Toggle'].hide_viewport=False;COL['09_FrontWall_Toggle'].hide_viewport=False
bpy.ops.object.select_all(action='DESELECT')
for ob in scene.objects:
    if ob.type in {'MESH','ARMATURE','EMPTY'}:ob.select_set(True)
# Final exports belong to derived level folders; do not ship this construction snapshot as gameplay.
# True pixels: six first-person/photo views plus cutaway and plan.
COL['08_Roof_Toggle'].hide_viewport=True;COL['09_FrontWall_Toggle'].hide_viewport=True
for camrow in cams:
    scene.camera=bpy.data.objects[camrow['name']]
    is_over=camrow['name'] in ['CAM_00_Cutaway','CAM_07_Plan']
    COL['08_Roof_Toggle'].hide_render=is_over;COL['09_FrontWall_Toggle'].hide_render=camrow['name']=='CAM_07_Plan'
    scene.render.resolution_x=1440 if is_over else 1280;scene.render.resolution_y=1000 if is_over else 720
    scene.render.filepath=str(QA/(camrow['name']+'.png'));bpy.ops.render.render(write_still=True)
    print('RENDERED',camrow['name'],flush=True)
print('SCENE_COMPLETE',OUT,flush=True)
