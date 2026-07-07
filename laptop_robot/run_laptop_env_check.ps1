$ErrorActionPreference = "Stop"

$repo = "$env:USERPROFILE\lerobot"
$condaHook = "$env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1"

if (!(Test-Path $repo)) {
    throw "LeRobot repo not found at $repo"
}
if (!(Test-Path $condaHook)) {
    throw "Conda hook not found at $condaHook"
}

. $condaHook
conda activate lerobot
Set-Location $repo
$env:PYTHONPATH = "src"

python -c "import lerobot, torch, cv2, serial, requests; print('imports ok'); print('torch', torch.__version__)"
python -c "import importlib.metadata as m; print('lerobot', m.version('lerobot'))"
Write-Host "Environment check OK"
