# AutoMonev

Pengingat + kirim otomatis laporan harian monev.maganghub.kemnaker.go.id.

- **16.00 / 19.00 / 21.00 WIB** — kalau laporan hari ini belum masuk, bot Telegram mengingatkan dan memberi teks siap tempel. Kalau sudah masuk, diam.
- **22.30 WIB** (cadangan 23.15) — kalau masih belum masuk, bot mengirim sendiri dengan status **Hadir, tanpa lokasi GPS**, memakai teks dari `teks.json`.
- Tidak masuk hari itu? Balas bot: `/izin sakit demam` → bot kirim "Tidak Hadir Dengan Keterangan". Salah ketik? `/batal`.
- Hari Minggu (off day) dan tanggal merah dari sistem monev otomatis dilewati.

Bot **tidak pernah memalsukan lokasi**. Laporan kiriman bot tercatat tanpa koordinat.

## Jalankan lokal

```
pip install playwright && python -m playwright install chromium
python automonev.py cek
python automonev.py kirim --dry-run
```

Kredensial dibaca dari `.env` (lihat `.env.example`). `.env` tidak boleh di-commit.

## Pasang di GitHub Actions (jalan walau laptop mati)

1. Buat repo **private** baru, push isi folder ini (`.env` dan `kredential.md` sudah di-ignore).
2. Settings → Secrets and variables → Actions → tambahkan `MONEV_USER`, `MONEV_PASS`, `TG_TOKEN`, `TG_CHAT_ID`.
3. Tab Actions → automonev → Run workflow → `cek` untuk tes.

## Telegram

1. Chat @BotFather → `/newbot` → salin token ke `TG_TOKEN`.
2. Kirim pesan apa saja ke bot kamu, lalu buka `https://api.telegram.org/bot<TOKEN>/getUpdates` → ambil `chat.id` → `TG_CHAT_ID`.

## Ubah teks

Edit `teks.json`. Tiap teks minimal 100 karakter. Bot memilih satu variasi per tanggal supaya tidak sama persis tiap hari.
