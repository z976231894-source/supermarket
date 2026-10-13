from pathlib import Path
from PIL import Image
OUT=Path('D:/游戏资产idea2-4/idea3_丑美术玩梗/07_技术交付/02_角色与动画');WORK=Path('D:/Repos/claw/outputs/idea3-character/motion_frames')
for asset in ('CHR_CLERK_COW','CHR_BOX_CUSTOMER','PRP_ODD_PRODUCT'):
 files=sorted((WORK/asset).glob('*.png'));images=[Image.open(p).convert('RGB') for p in files];images[0].save(OUT/asset/'Preview'/'04_MotionPreview.gif',save_all=True,append_images=images[1:],duration=100,loop=0,optimize=False)
