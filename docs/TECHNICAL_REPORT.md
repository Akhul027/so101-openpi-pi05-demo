# Laporan Teknis Singkat

## 1. Ringkasan

Project ini menguji integrasi SO101 follower robot dengan policy Pi0.5. Laptop robot bertugas membaca kamera dan state joint, lalu mengirim observation ke server RTX. Server RTX menjalankan model Pi0.5 dan mengembalikan action. Client kemudian membatasi action menggunakan safe step sebelum dikirim ke robot.

## 2. Komponen Sistem

| Komponen | Fungsi |
|---|---|
| SO101 follower | Aktuator robot utama |
| Kamera front dan wrist | Input visual untuk policy |
| Laptop robot | Client, camera capture, state read, action execution |
| RTX server | Inference Pi0.5 menggunakan GPU |
| FastAPI | API `/health`, `/predict`, `/reset`, `/warmup` |
| LeRobot | Interface robot, kamera, policy, dan dataset |

## 3. Alur Data

```text
Kamera + joint state
  -> laptop_robot/so101_demo_common.py
  -> HTTP POST /predict
  -> rtx_inference_server/server_policy.py
  -> Pi0.5 policy
  -> action 6 joint
  -> safe action clipping
  -> robot.send_action()
```

## 4. Konfigurasi Penting

- Dataset memakai kamera `observation.images.front` dan `observation.images.wrist`.
- Joint state dan action berisi 6 nilai: `shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper`.
- Client memakai `use_degrees=False` karena dataset direkam dalam normalized position `-100..100`.
- Task prompt yang sesuai dataset: `move red cube to the brown area`.
- Server menggunakan `PI05_N_ACTION_STEPS=10` agar action chunk tidak terlalu panjang.

## 5. Status Debug

Perbaikan yang sudah masuk:

1. Mapping kamera disesuaikan dari `top` ke `front` dan `wrist`.
2. Prompt task disesuaikan dengan prompt dataset.
3. Client memakai HTTP session dengan `trust_env=False` agar tidak terkena proxy environment.
4. Server memiliki endpoint `/reset` untuk mengosongkan action queue policy sebelum demo.
5. Safe loop dapat melewati error sementara dan abort setelah 10 kegagalan beruntun.

Kendala terakhir:

- Kamera USB tidak terdeteksi oleh OpenCV/LeRobot pada laptop robot. Ini harus diselesaikan sebelum demo autonomous dilanjutkan.

## 6. Rekomendasi Lanjut

1. Validasi kamera menggunakan `lerobot_find_cameras`.
2. Jalankan test bertahap: camera -> robot state -> hold pose -> policy dry-run -> one safe step -> full demo.
3. Jika robot mencapai objek tetapi gagal grasp, tuning `SO101_MAX_GRIPPER_STEP` dan kalibrasi `wrist_flex`.
4. Untuk stabilitas jangka menengah, tambah dataset dengan scene yang sama tetapi posisi objek sedikit bervariasi.
