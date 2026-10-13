import bpy,json
from pathlib import Path
OUT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付/02_角色与动画');WORK=Path('D:/Repos/claw/outputs/idea3-character/motion_frames');WORK.mkdir(parents=True,exist_ok=True)
for asset,clip in [('CHR_CLERK_COW','DeepBow'),('CHR_BOX_CUSTOMER','ThreeStepTurn'),('PRP_ODD_PRODUCT','ShortStep')]:
 dst=OUT/asset;bpy.ops.wm.open_mainfile(filepath=str(dst/f'{asset}_Rigged.blend'));rig=bpy.data.objects[asset+'_Rig'];rig.animation_data.action=bpy.data.actions[asset+'__'+clip];sc=bpy.context.scene;sc.render.resolution_x=480;sc.render.resolution_y=480;sc.render.resolution_percentage=100;end=int(rig.animation_data.action.frame_range[1]);frames=WORK/asset;frames.mkdir(exist_ok=True)
 for i,frame in enumerate(range(1,end,3)):
  sc.frame_set(frame);sc.render.filepath=str(frames/f'{i:03}.png');bpy.ops.render.render(write_still=True)
 print('PREVIEW_RENDERED',asset,flush=True)
