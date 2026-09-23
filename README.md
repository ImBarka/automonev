# AutoMonev

Pengingat + kirim otomatis laporan harian monev.maganghub.kemnaker.go.id.

- **16.00 / 19.00 / 21.00 WIB**: kalau laporan hari ini belum masuk, bot Telegram mengingatkan dan memberi teks siap tempel. Kalau sudah masuk, diam.
- **22.30 WIB** (cadangan 23.15): kalau masih belum masuk, bot mengirim sendiri dengan status **Hadir, tanpa lokasi GPS**, memakai teks dari `teks.json`.
- Tidak masuk hari itu? Balas bot: `/izin sakit demam` → bot kirim "Tidak Hadir Dengan Keterangan". Salah ketik? `/batal`.
- Hari Minggu (off day) dan tanggal merah dari sistem monev otomatis dilewati.

Bot **tidak pernah memalsukan lokasi**. Laporan kiriman bot tercatat tanpa koordinat.

## Di mana bot berjalan

| Tempat | Tugas |
|---|---|
| **HP** (Termux + MacroDroid) | utama: `ingat` 16.00/19.00/21.00, `kirim` 22.30/23.15 |
| **Laptop** (Task Scheduler) | cadangan: `kirim` 23.30 kalau laptop sedang Sleep + dicas |
| **GitHub Actions** | penjaga: 21.30/23.15, peringatan Telegram kalau HP/laptop belum melapor "aman" |

Login monev harus dari jaringan rumahan/seluler. Cloudflare Kemnaker memblokir server pusat data seperti GitHub Actions.
Bot selalu cek "sudah terisi?" sebelum mengirim, jadi laporan tidak akan dobel.

## Pasang di HP (Termux + MacroDroid)

### 1. Termux

Pastikan Termux dari **F-Droid** atau GitHub, bukan Play Store. Lalu di Termux:

```
pkg update -y && pkg install -y git gh
gh auth login            # pilih GitHub.com → HTTPS → Login with a web browser
gh repo clone ImBarka/automonev ~/automonev
bash ~/automonev/pasang-hp.sh
```

Skrip akan menanyakan email, password SiapKerja, dan token bot (salin dari chat @BotFather). Di akhir harus muncul
`Laporan ... sudah masuk.` / `BELUM diisi.`, artinya login dari HP berhasil.

### 2. Termux:Tasker

Install **Termux:Tasker** dari tempat yang sama dengan Termux (F-Droid). Aplikasi ini jembatan supaya MacroDroid bisa menjalankan perintah Termux.

### 3. MacroDroid (2 macro)

**Macro "AutoMonev ingat"**
- Trigger: *Date/Time → Day/Time*, jam **16:00**, semua hari. Tambah trigger lagi untuk **19:00** dan **21:00**.
- Action: *Applications → Plugin Tasker/Locale → Termux:Tasker*
  - Executable: `automonev-ingat`
  - **Jangan** centang "Execute in a terminal session" (supaya jalan di latar belakang)

**Macro "AutoMonev kirim"**: sama, trigger **22:30** dan **23:15**, executable `automonev-kirim`.

### 4. Baterai POCO (HyperOS), penting

Untuk **Termux**, **Termux:Tasker**, dan **MacroDroid**:
- Setelan → Aplikasi → Kelola aplikasi → (nama aplikasi) → **Mulai otomatis: ON**
- → Penghemat baterai → **Tidak ada batasan**

Tanpa ini, HyperOS bisa mematikan jadwal diam-diam.

### 5. Tes

Di MacroDroid, buka macro "AutoMonev ingat" → ⋮ → **Test actions**. Kalau monev hari itu belum diisi dan sudah lewat jam 15.00,
pesan pengingat masuk ke Telegram. Log: `cat ~/automonev/automonev.log` di Termux.

Update kode di HP: `cd ~/automonev && git pull`.

## Laptop (cadangan)

```
pip install requests
powershell -ExecutionPolicy Bypass -File pasang-jadwal.ps1
```

Malam hari laptop cukup Sleep + dicas; Task Scheduler membangunkannya jam 23.30. Log: `automonev.log`.

## Perintah

```
python automonev.py cek                       # sudah diisi belum?
python automonev.py kirim --dry-run --paksa   # lihat isian tanpa mengirim
```

`ingat` hanya jalan setelah 15.00 dan `kirim` setelah 22.00 (tambah `--paksa` untuk tes), supaya jadwal yang terlewat
tidak mengirim laporan hari berikutnya di pagi hari.

## Ubah teks

Edit `teks.json`. Tiap teks minimal 100 karakter. Bot memilih satu variasi per tanggal supaya tidak sama persis tiap hari.
