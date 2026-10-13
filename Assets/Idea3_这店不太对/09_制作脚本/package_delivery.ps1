$ErrorActionPreference = 'Stop'
$packageRoot = [IO.Path]::GetFullPath('D:\游戏资产idea2-4\idea3_丑美术玩梗\07_技术交付')
$projectRoot = [IO.Path]::GetFullPath('D:\游戏资产idea2-4\idea3_丑美术玩梗')
$sceneQA = Get-Content -LiteralPath (Join-Path $packageRoot '06_验收与预览\三关卡回读验收.json') -Raw | ConvertFrom-Json
$propQA = Get-Content -LiteralPath (Join-Path $packageRoot '06_验收与预览\道具FBX回读验收.json') -Raw | ConvertFrom-Json
$navQA = Get-Content -LiteralPath (Join-Path $packageRoot '06_验收与预览\三关卡动线验收.json') -Raw | ConvertFrom-Json
$rigQA = Get-Content -LiteralPath (Join-Path $packageRoot '02_角色与动画\fbx_roundtrip_qa.json') -Raw | ConvertFrom-Json
if (-not $sceneQA.all_pass -or -not $propQA.all_pass -or -not $navQA.all_pass -or -not $rigQA.all_pass) { throw 'Cannot ship: asset roundtrip QA not complete.' }
$sourceCopies = @('derive_three_levels.py','verify_three_levels.py','verify_props.py','build_store_scene.py','finish_store_base.py','scene_prop_library.py','package_delivery.ps1')
foreach ($name in $sourceCopies) { Copy-Item -LiteralPath (Join-Path 'D:\Repos\claw\tools\idea3' $name) -Destination (Join-Path $packageRoot ('09_制作脚本\' + $name)) }
$rawChecks = @()
foreach ($zip in Get-ChildItem -LiteralPath (Join-Path $packageRoot '08_原始AI输入') -File -Filter '*.zip') {
    $original = Join-Path $projectRoot ('资产\' + $zip.Name)
    $same = (Get-FileHash -LiteralPath $zip.FullName -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash
    if (-not $same) { throw ('Original differs: ' + $zip.Name) }
    $rawChecks += [ordered]@{file=$zip.Name;sha256=(Get-FileHash -LiteralPath $zip.FullName -Algorithm SHA256).Hash.ToLower();original_unchanged=$same}
}
$manifestPath = Join-Path $packageRoot '交付文件清单.json'
$files = @()
foreach ($item in Get-ChildItem -LiteralPath $packageRoot -Recurse -File | Sort-Object FullName) {
    if ($item.FullName -eq $manifestPath) { continue }
    if ($item.Extension -eq '.blend1' -or $item.FullName -match '_旧版|\.env$') { throw ('Unexpected draft or environment file: ' + $item.FullName) }
    $files += [ordered]@{path=$item.FullName.Substring($packageRoot.Length+1).Replace('\','/');bytes=$item.Length;sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLower()}
}
$sum = ($files | Measure-Object -Property bytes -Sum).Sum
$manifest = [ordered]@{version='2026-09-30-three-level-free-exploration';entrypoint='README_先看这里.md';scope='Art assets; runtime game logic and Unity validation not included';files_count_excluding_manifest=$files.Count;total_bytes_excluding_manifest=$sum;levels=3;optional_gags=@(4,5,5);source_zip_checks=$rawChecks;blender_roundtrip_pass=$true;files=$files}
$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipPath = Join-Path $projectRoot 'idea3_美术交付_三关版_20260930.zip'
if (Test-Path -LiteralPath $zipPath) { throw 'Existing delivery ZIP preserved; choose a versioned filename.' }
[IO.Compression.ZipFile]::CreateFromDirectory($packageRoot,$zipPath,[IO.Compression.CompressionLevel]::Optimal,$true)
$archive = [IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $dataEntries = @($archive.Entries | Where-Object { $_.Name })
    if ($dataEntries.Count -ne $files.Count + 1) { throw 'ZIP entry count mismatch' }
    $manifestEntry = $dataEntries | Where-Object { $_.FullName.EndsWith('/交付文件清单.json') }
    if (-not $manifestEntry) { throw 'ZIP missing manifest' }
    $fileLookup=@{};foreach($f in $files){$fileLookup['07_技术交付/'+$f.path]=$f}
    foreach($entry in $dataEntries){
        if($entry.FullName.EndsWith('/交付文件清单.json')){continue}
        $expected=$fileLookup[$entry.FullName.Replace('\','/')]
        if(-not $expected){throw ('Unknown archive entry '+$entry.FullName)}
        $stream=$entry.Open();$hasher=[Security.Cryptography.SHA256]::Create()
        try{$hash=[BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-','').ToLower()}finally{$hasher.Dispose();$stream.Dispose()}
        if($hash -ne $expected.sha256){throw ('ZIP hash mismatch '+$entry.FullName)}
    }
} finally { $archive.Dispose() }
$result=[ordered]@{zip=$zipPath;zip_bytes=(Get-Item -LiteralPath $zipPath).Length;zip_sha256=(Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLower();file_count=$files.Count+1;original_zip_checks=$rawChecks.Count;archive_all_file_hashes_verified=$true;qa='3 scene Blender + 6 scene FBX/GLB + 10 prop FBX; separate character QA in02'}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $projectRoot 'idea3_美术交付_三关版_20260930_校验.json') -Encoding utf8
$result | ConvertTo-Json -Depth 4
