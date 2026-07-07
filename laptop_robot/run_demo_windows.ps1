$ErrorActionPreference = "Stop"

$repo = "$env:USERPROFILE\lerobot"
$condaHook = "$env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1"

. $condaHook
conda activate lerobot
Set-Location $repo
$env:PYTHONPATH = "src"

if (!$env:SO101_SERVER_URL) { $env:SO101_SERVER_URL = "http://127.0.0.1:8000/predict" }
if (!$env:SO101_PORT) { $env:SO101_PORT = "COM3" }
if (!$env:SO101_TOP_CAM) { $env:SO101_TOP_CAM = "2" }
if (!$env:SO101_WRIST_CAM) { $env:SO101_WRIST_CAM = "3" }
if (!$env:SO101_TASK) { $env:SO101_TASK = "move red cube to the brown area" }
if (!$env:SO101_LOOP_HZ) { $env:SO101_LOOP_HZ = "10" }
if (!$env:SO101_MAX_STEP_DEG) { $env:SO101_MAX_STEP_DEG = "5" }
if (!$env:SO101_MAX_SHOULDER_LIFT_STEP_DEG) { $env:SO101_MAX_SHOULDER_LIFT_STEP_DEG = "3" }
if (!$env:SO101_MAX_GRIPPER_STEP) { $env:SO101_MAX_GRIPPER_STEP = "12" }
if (!$env:NO_PROXY) { $env:NO_PROXY = "localhost,127.0.0.1" }
if (!$env:no_proxy) { $env:no_proxy = $env:NO_PROXY }

python run_pick_and_place_demo.py
