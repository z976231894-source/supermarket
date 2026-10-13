# AI 商品包装图集

由内置 image_gen 生成，未调用 CLI/API，也未使用第三方商标或采样素材。原图保存在本目录 Shelf_Packaging_AI_Source.png，运行版为最近邻技术缩小的 Shelf_Packaging_Atlas_256.png；统一 Point 采样。

生成结果顶部三行是规则4列，底行不是等宽4列，因此仅使用顶部12个格子，不用不规则底行。UV每格内缩约1.5像素以减少串色。图集映射在背景普通商品正面，原13个Tripo模型UV未被覆盖。无须拿包装图集重新去Tripo生成模型。

## 完整生成提示词

Use case: stylized-concept. Asset type: square GAME UV BASE COLOR TEXTURE ATLAS, flat 2D, not a rendered scene. Create one single 4 by 4 grid of 16 equally sized square grocery packaging FRONT LABEL tiles filling the entire square exactly. Each cell is borderless, flat, edge-to-edge packaging artwork, no margins/gaps. Original generic late-night convenience store: six chip/cookie/cereal labels, four juice/soda can labels, four tea/canned soup labels, two absurd plain air-product labels. Palette restrained ochre orange, dusty mustard, teal, sage, dull purple, muted burgundy, cream and charcoal. Each cell has large simple graphic motif of food/fruit and chunky unreadable abstract pseudo-type horizontal blocks (NO actual brand names, no legible text), like low resolution 1990s PS1 grocery pixel textures. Distinct chromatic packaging, worn subtle square pixels but clean, solid block shapes, each cell has deliberately large readable colored fields and small cream label detail. All cells axis-aligned orthographic front printing; absolutely NO 3D object render, NO bottle/carton silhouettes sitting on a background, NO perspective, no lighting, no shadow, no photo, no mockup, no border outside grid, no watermark. Intended as single UV atlas mapped onto low polygon shelf products; exact 4x4 regular equal square tiling crucial. Original low-fi ugly-art visual style; controlled, not cute.
