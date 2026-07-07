# Setup VS Code dan Push ke GitHub

## A. Buka Project di VS Code

```powershell
cd D:\persepsirobot_openpi_so101
code .
```

Install extension VS Code yang disarankan:

- Python
- Pylance
- PowerShell
- GitLens, opsional

Pilih interpreter Python:

```text
Ctrl + Shift + P
-> Python: Select Interpreter
-> pilih env conda lerobot
```

Untuk terminal Windows/PowerShell:

```powershell
. $env:USERPROFILE\anaconda3\shell\condabin\conda-hook.ps1
conda activate lerobot
```

## B. Cek Kode Sebelum Commit

```powershell
python -m compileall laptop_robot rtx_inference_server tools
```

Kalau ingin test cepat:

```powershell
cd laptop_robot
python check_cameras.py
python test_read_robot_state.py
```

## C. Inisialisasi Git

```powershell
git init
git status
git add .
git commit -m "Initial SO101 Pi0.5 demo pipeline"
```

## D. Buat Repository di GitHub

1. Buka GitHub.
2. Klik **New repository**.
3. Nama repo contoh: `so101-pi05-pick-place-demo`.
4. Pilih public/private sesuai kebutuhan.
5. Jangan centang README, `.gitignore`, atau license jika file lokal sudah ada.

## E. Hubungkan Local Repo ke GitHub

Ganti URL sesuai repo kamu:

```powershell
git branch -M main
git remote add origin https://github.com/<username>/so101-pi05-pick-place-demo.git
git push -u origin main
```

Kalau remote sudah ada:

```powershell
git remote set-url origin https://github.com/<username>/so101-pi05-pick-place-demo.git
git push -u origin main
```

## F. Setelah Ada Perubahan

```powershell
git status
git add .
git commit -m "Update robot client and inference server"
git push
```

## Catatan Penting

Jangan push file yang berisi:

- password server
- token Hugging Face
- private key SSH
- file model besar `.safetensors`
- log panjang atau dataset mentah
