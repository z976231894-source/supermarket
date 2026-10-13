# 《这店不太对》自由探索 UI v2

当前默认交付与飞书idea3对齐：walking sim、3个独立场景、无任务/战斗/失败。

## 文件

- 7屏：三关入口、极简探索HUD、按键帮助、暂停声音、可选拍照、保存提示、随时离开。两档1920×1080/1280×720共14张PNG预览。
- 24张透明切片及SVG源；Data内中文文案、9-slice与精确元素布局。中文程序渲染，不烘焙。
- VFX为原低透明像素雾/星点，≤12粒子；不闪屏、不遮挡。
- 背景为本包Blender实渲叠加UI，不是Unity运行截图。

## Unity

Sprite/Single/FullRect/Point/Compression None/Alpha Is Transparency；sprite_map.json给Border Left/Bottom/Right/Top。Canvas Scaler1920×1080、match=.5、适配SafeArea。程序使用已许可中文TMP字体（预览调用系统微软雅黑，不附带字库）。

标题三关全部可进；不得用“看完所有梗”解锁下一关或离开。难度提升只指观察层次与多物件联动。HUD只显示当前附近物体的单行E提示；Tab只看操作，不再显示交班单。Esc可随时离开，无成功/失败成绩页。没有倒计时/经营数值/收集进度。

拍照是完全可选的本地保存，写盘成功后再弹提示；失败文案见strings。旧交班设计已移出正式包，保存在项目根 [98_过程留档/03_UI/_旧版任务UI留档](../../98_过程留档/03_UI/_旧版任务UI留档)，可研究为可选彩蛋，但不是主流程，不导入Unity。音频接04_音频/Data/free_exploration_cues.json。

## 已验收与边界

两档截图引用/溢出、三关直进、Tab帮助、音量滑块与PNG规格已测试。离线页面不是游戏；没有启动Unity Editor验证，不宣称Prefab/状态机已集成。

## 最终三关绑定

Data/layouts.json的levels给出L1/L2/L3稳定加载ID及三个实际.blend与scene-manifest.json相对路径（相对03_UI）。.blend为制作源，不是已建立的Unity Scene；技术在引擎中制作对应Scene后将加载ID映射过去。不得把前一关完成作为入口前置条件。
