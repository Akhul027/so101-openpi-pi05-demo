# SO101 Pi0.5 Pick-and-Place Demo

Repository ini berisi pipeline demo **SO101 follower robot** dengan model **Pi0.5 / LeRobot**. Sistem dibagi menjadi dua bagian: laptop dekat robot sebagai client, dan server RTX sebagai inference server.

> Status terakhir: pipeline client-server sudah tersambung. Kendala terakhir yang tercatat adalah kamera USB di laptop belum terdeteksi oleh OpenCV/LeRobot.

## Arsitektur Singkat

```text
SO101 Robot + USB Cameras
        ↓
Laptop Robot Client
        ↓ HTTP / VPN / SSH tunnel
RTX Inference Server
        ↓
Pi0.5 Policy Checkpoint
```

## Struktur Folder

```text
laptop_robot/          Script client robot, kamera, dan safe demo loop
rtx_inference_server/  FastAPI server untuk inference Pi0.5
tools/                 Utility deploy/check server via SSH
training/              Script/Notebook training Pi0.5 di Colab atau GPU server
docs/                  Catatan teknis dan langkah setup
```

## Konfigurasi Utama

Jangan hardcode IP, username, password, atau token. Gunakan environment variable.

```powershell
$env:SO101_SERVER_URL = "http://<RTX_SERVER_IP>:8000/predict"
$env:SO101_PORT = "COM3"
$env:SO101_TOP_CAM = "2"
$env:SO101_WRIST_CAM = "3"
$env:SO101_TASK = "move red cube to the brown area"
```

Untuk server RTX:

```bash
export PI05_MODEL_PATH=/data/robot_project/models/pi05_v2model/pretrained_model
export PI05_DEVICE=cuda
export PI05_N_ACTION_STEPS=10
```

## Cara Menjalankan Client di Laptop Robot

Masuk ke folder LeRobot runtime:

```powershell
cd $env:USERPROFILE\lerobot
. $env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1
conda activate lerobot
$env:PYTHONPATH = "src"
```

Salin isi `laptop_robot/` ke folder runtime LeRobot, lalu jalankan urutan aman:

```powershell
python check_cameras.py
python test_read_robot_state.py
python test_send_hold_pose.py
python test_real_state_camera_policy.py
python test_policy_one_safe_step.py
python run_pick_and_place_demo.py
```

Atau gunakan wrapper:

```powershell
.\run_demo_windows.ps1
```

## Cara Menjalankan RTX Inference Server

Di server RTX, letakkan folder `rtx_inference_server/` ke:

```bash
/data/robot_project/inference_server
```

Jalankan:

```bash
bash /data/robot_project/inference_server/start_server.sh
bash /data/robot_project/inference_server/check_server.sh
```

Endpoint yang tersedia:

```text
GET  /health
POST /predict
POST /reset
POST /warmup
```

## Catatan Keselamatan

- Jalankan test satu langkah sebelum full demo.
- Pastikan emergency stop atau akses power robot mudah dijangkau.
- Gunakan `SO101_MAX_STEP_DEG`, `SO101_MAX_SHOULDER_LIFT_STEP_DEG`, dan `SO101_MAX_GRIPPER_STEP` untuk membatasi gerakan.
- Jangan menjalankan robot jika kamera, port serial, atau policy server belum tervalidasi.

## Status Debug Terakhir

- Server RTX health check sudah OK.
- Policy reset endpoint sudah tersedia.
- Client memakai `use_degrees=False` karena dataset memakai normalized joint position `-100..100`.
- Kamera model memakai key `observation.images.front` dan `observation.images.wrist`.
- Task prompt training: `move red cube to the brown area`.
- Kendala terakhir: kamera USB tidak terdeteksi oleh OpenCV/LeRobot di laptop robot.

## Langkah Lanjut

1. Pastikan kamera front dan wrist terbaca di Windows.
2. Jalankan `lerobot_find_cameras` untuk memastikan index kamera.
3. Set ulang `SO101_TOP_CAM` dan `SO101_WRIST_CAM` jika index berubah.
4. Jalankan demo 600 step setelah kamera dan server tervalidasi.
5. Jika grasp belum konsisten, evaluasi gripper step, wrist calibration, dan tambah dataset.
