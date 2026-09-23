# AutoMonev

Pengingat + kirim otomatis laporan harian monev.maganghub.kemnaker.go.id.

- **16.00 / 19.00 / 21.00 WIB** — kalau laporan hari ini belum masuk, bot Telegram mengingatkan dan memberi teks siap tempel. Kalau sudah masuk, diam.
- **22.30 WIB** (cadangan 23.15) — kalau masih belum masuk, bot mengirim sendiri dengan status **Hadir, tanpa lokasi GPS**, memakai teks dari `teks.json`.
- Tidak masuk hari itu? Balas bot: `/izin sakit demam` → bot kirim "Tidak Hadir Dengan Keterangan". Salah ketik? `/batal`.
- Hari Minggu (off day) dan tanggal merah dari sistem monev otomatis dilewati.

Bot **tidak pernah memalsukan lokasi**. Laporan kiriman bot tercatat tanpa koordinat.

## Di mana bot berjalan

**Laptop (utama).** Cloudflare Kemnaker memblokir server GitHub, jadi login monev harus dari laptop.
Jadwal dipasang di Windows Task Scheduler oleh `pasang-jadwal.ps1`:

| Jam WIB | Perintah |
|---|---|
| 16.00, 19.00, 21.00 | `ingat` |
| 22.30, 23.15 | `kirim` |

- Jadwal yang terlewat (laptop mati/tidur) dijalankan begitu laptop nyala, tapi `kirim` hanya mau jalan di atas jam 22.00 dan `ingat` di atas jam 15.00.
- Malam hari, **Sleep** laptop saja, jangan Shut down: Task Scheduler bisa membangunkan laptop dari Sleep.
- Log: `automonev.log`.

**GitHub Actions (penjaga).** Jam 21.30 dan 23.15 WIB, GitHub mengecek apakah laptop sudah melapor "aman" hari ini
(ditandai lewat deskripsi bot Telegram). Kalau belum, misalnya karena laptop mati, kamu dapat peringatan untuk isi manual di HP.
Secrets: `TG_TOKEN`, `TG_CHAT_ID` (`MONEV_USER`/`MONEV_PASS` tidak dipakai di sana).

## Jalankan manual

```
pip install playwright && python -m playwright install chromium
python automonev.py cek
python automonev.py kirim --dry-run --paksa
powershell -ExecutionPolicy Bypass -File pasang-jadwal.ps1
```

Kredensial dibaca dari `.env` (lihat `.env.example`). `.env` tidak boleh di-commit.

## Ubah teks

Edit `teks.json`. Tiap teks minimal 100 karakter. Bot memilih satu variasi per tanggal supaya tidak sama persis tiap hari.
