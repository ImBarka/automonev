"""AutoMonev — pengingat + kirim otomatis laporan harian monev.maganghub.kemnaker.go.id.

Perintah:
  python automonev.py cek              cek apakah laporan hari ini sudah masuk
  python automonev.py ingat            kirim pengingat Telegram kalau belum diisi
  python automonev.py kirim            kirim otomatis (tanpa GPS) kalau belum diisi
  python automonev.py kirim --dry-run  tampilkan isian tanpa mengirim
  python automonev.py jaga             (untuk GitHub) peringatkan kalau laptop belum
                                       melapor aman hari ini — tanpa login ke monev

Login ke monev harus dari HP/laptop di jaringan rumahan/seluler: Cloudflare
Kemnaker memblokir server pusat data seperti GitHub Actions.

Balas bot Telegram dengan "/izin <alasan>" di hari itu supaya bot mengirim
status "Tidak Hadir Dengan Keterangan", bukan "Hadir".
"""
import json
import os
import random
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

HERE = Path(__file__).parent
WIB = timezone(timedelta(hours=7))
APP = "https://monev.maganghub.kemnaker.go.id"
API = "https://monev-api.maganghub.kemnaker.go.id/api/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
MIN_CHARS = 100


def load_env():
    env_file = HERE / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def today():
    return datetime.now(WIB).date()


# ---------- Telegram ----------

def tg(method, **params):
    token = os.environ.get("TG_TOKEN")
    if not token:
        return None
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/{method}", data, timeout=20) as r:
        return json.load(r)


def notify(text):
    print(text)
    if os.environ.get("TG_TOKEN") and os.environ.get("TG_CHAT_ID"):
        try:
            tg("sendMessage", chat_id=os.environ["TG_CHAT_ID"], text=text, parse_mode="HTML")
        except Exception as e:
            print("Gagal kirim Telegram:", e)


def izin_hari_ini():
    """Cari pesan '/izin <alasan>' dari kamu hari ini. Return alasan atau None."""
    if not (os.environ.get("TG_TOKEN") and os.environ.get("TG_CHAT_ID")):
        return None
    try:
        res = tg("getUpdates", limit=100) or {}
    except Exception as e:
        print("Gagal baca Telegram:", e)
        return None
    alasan = None
    for u in res.get("result", []):
        m = u.get("message") or {}
        if str(m.get("chat", {}).get("id")) != os.environ["TG_CHAT_ID"]:
            continue
        if datetime.fromtimestamp(m.get("date", 0), WIB).date() != today():
            continue
        text = (m.get("text") or "").strip()
        if text.lower().startswith("/izin"):
            alasan = text[5:].strip() or "Izin tidak masuk magang hari ini."
        elif text.lower().startswith("/batal"):
            alasan = None
    return alasan


def tandai_aman(tanggal, ket):
    """Catat di deskripsi bot bahwa hari ini sudah aman, supaya penjaga di GitHub tahu."""
    try:
        tg("setMyShortDescription", short_description=f"monev-aman:{tanggal.isoformat()}:{ket}"[:120])
    except Exception as e:
        print("Gagal menandai aman:", e)


def sudah_aman(tanggal):
    res = tg("getMyShortDescription") or {}
    desc = (res.get("result") or {}).get("short_description", "")
    return desc.startswith(f"monev-aman:{tanggal.isoformat()}")


# ---------- Teks laporan ----------

def teks_laporan(tanggal):
    """Pilih variasi teks dari teks.json, konsisten per tanggal, minimal 100 karakter."""
    pools = json.loads((HERE / "teks.json").read_text(encoding="utf-8"))
    rng = random.Random(tanggal.isoformat())
    out = {}
    for field in ("activity_log", "lesson_learned", "obstacles"):
        pilihan = [t for t in pools[field] if len(t) >= MIN_CHARS]
        if not pilihan:
            raise SystemExit(f"teks.json: tidak ada teks '{field}' yang >= {MIN_CHARS} karakter")
        out[field] = rng.choice(pilihan)
    return out


# ---------- Monev ----------

class Monev:
    """Klien monev lewat HTTP biasa (tanpa browser), jadi bisa jalan di Termux."""

    SSO = "https://account.kemnaker.go.id"

    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept": "application/json"})
        self.token = None
        self.user = None

    def _cek_blokir(self, r):
        if r.status_code in (403, 503) and "cloudflare" in r.text.lower():
            raise RuntimeError("Diblokir Cloudflare Kemnaker (IP ini dianggap bot/pusat data).")

    def login(self):
        app_hdr = {"Origin": APP, "Referer": APP + "/"}
        # 1. API monev memberi URL login SSO (dan menyimpan cookie state)
        r = self.s.get(API + "/auth/login", headers=app_hdr, timeout=30)
        self._cek_blokir(r)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            j = r.text.strip().strip('"')
        sso_url = j if isinstance(j, str) else (j.get("redirectUrl") or j.get("redirect_uri") or j.get("url"))
        # 2. Halaman login SiapKerja -> cookie XSRF-TOKEN
        r = self.s.get(sso_url, headers={"Accept": "text/html"}, timeout=30)
        self._cek_blokir(r)
        xsrf = urllib.parse.unquote(self.s.cookies.get("XSRF-TOKEN", domain="account.kemnaker.go.id") or "")
        # 3. Kirim username + password
        r = self.s.post(f"{self.SSO}/auth/login", timeout=30,
                        json={"username": os.environ["MONEV_USER"], "password": os.environ["MONEV_PASS"]},
                        headers={"X-XSRF-TOKEN": xsrf, "X-Requested-With": "XMLHttpRequest",
                                 "Origin": self.SSO, "Referer": r.url})
        self._cek_blokir(r)
        if not r.ok:
            raise RuntimeError(f"Login SiapKerja ditolak ({r.status_code}): {r.text[:200]}")
        redirect = r.json()["data"]["redirect_uri"]
        # 4. Ikuti redirect sampai /sso/callback?code=...&state=...
        r = self.s.get(redirect, headers={"Accept": "text/html"}, timeout=30)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
        if "code" not in q:
            raise RuntimeError(f"Login tidak kembali ke monev (berhenti di {r.url[:120]})")
        # 5. Tukar code dengan access token
        r = self.s.get(API + "/auth/login/callback", headers=app_hdr, timeout=30,
                       params={"code": q["code"][0], "state": q["state"][0]})
        r.raise_for_status()
        self.token = r.json()["access_token"]
        self.user = self.get("/users/me")["data"]

    def _req(self, method, path, **kw):
        r = self.s.request(method, API + path, timeout=30, headers={
            "Authorization": f"Bearer {self.token}", "Origin": APP, "Referer": APP + "/"}, **kw)
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r.json()

    def get(self, path, params=None):
        return self._req("GET", path, params=params)

    def post(self, path, body):
        return self._req("POST", path, json=body)

    def sudah_isi(self, tanggal):
        d = tanggal.isoformat()
        res = self.get("/attendances", {"participant_id": self.user["id"], "start_date": d, "end_date": d})
        return any(a.get("date") == d for a in res.get("data", []))

    def alasan_libur(self, tanggal):
        """Return nama libur / 'hari off' kalau tanggal ini bukan hari magang, else None."""
        u = self.user
        if tanggal.strftime("%A").upper() in (u.get("off_days") or []):
            return f"hari off ({tanggal.strftime('%A')})"
        start = datetime.fromisoformat(u["internship_start_date"]).date()
        end = datetime.fromisoformat(u["internship_end_date"]).date()
        if not (start <= tanggal <= end):
            return "di luar periode magang"
        clean = lambda s: str(s or "").replace(".", "").strip()
        prov, kab = clean(u.get("internship_location_province_code")), clean(u.get("internship_location_regency_code"))
        page = 1
        while True:
            res = self.get("/holidays", {"page": page, "limit": 100})
            for h in res.get("data", []):
                if not str(h.get("date", "")).startswith(tanggal.isoformat()):
                    continue
                scope = h.get("scope")
                if (scope == "NATIONAL"
                        or (scope == "PROVINCE" and clean(h.get("province_code")) == prov)
                        or (scope not in ("NATIONAL", "PROVINCE") and clean(h.get("regency_code")) == kab)):
                    return h.get("name") or h.get("description") or "hari libur"
            if page * 100 >= res.get("total", 0):
                return None
            page += 1

    def kirim_hadir(self, tanggal, isi):
        body = {"date": tanggal.isoformat(), "status": "PRESENT", **isi}
        return self.post("/attendances/with-daily-log", body)

    def kirim_izin(self, tanggal, alasan):
        body = {"date": tanggal.isoformat(), "status": "ON_LEAVE", "leave_reason": alasan,
                "participant_id": self.user["id"]}
        return self.post("/attendances", body)

    def close(self):
        self.s.close()


# ---------- Perintah ----------

def main():
    load_env()
    args = sys.argv[1:]
    cmd = args[0] if args else "cek"
    dry = "--dry-run" in args
    tanggal = today()
    tgl = tanggal.strftime("%d-%m-%Y")

    if cmd == "jaga":
        if tanggal.strftime("%A").upper() == "SUNDAY" or sudah_aman(tanggal):
            print("Aman.")
            return
        jam = datetime.now(WIB).strftime("%H:%M")
        notify(f"⚠️ <b>Bot belum melapor monev {tgl} aman</b> (sekarang {jam} WIB).\n"
               f"Mungkin HP/laptop mati atau offline, jadi bot tidak bisa cek atau kirim otomatis.\n"
               f"Isi manual di HP sebelum 23.59: {APP}")
        return

    # Task Scheduler menjalankan jadwal yang terlewat begitu laptop nyala; jangan sampai
    # "kirim" 22.30 yang terlewat malah mengirim laporan hari berikutnya jam 7 pagi.
    jam_min = {"ingat": 15, "kirim": 22}.get(cmd)
    if jam_min and datetime.now(WIB).hour < jam_min and "--paksa" not in args:
        print(f"'{cmd}' hanya jalan setelah jam {jam_min}.00 WIB (tambahkan --paksa untuk tes).")
        return

    m = Monev()
    try:
        m.login()
        if m.sudah_isi(tanggal):
            print(f"Laporan {tgl} sudah masuk.")
            tandai_aman(tanggal, "terisi")
            return
        libur = m.alasan_libur(tanggal)
        if libur:
            print(f"{tgl}: {libur}, tidak perlu isi.")
            tandai_aman(tanggal, "libur")
            return

        if cmd == "cek":
            print(f"Laporan {tgl} BELUM diisi.")

        elif cmd == "ingat":
            isi = teks_laporan(tanggal)
            jam = datetime.now(WIB).strftime("%H:%M")
            notify(
                f"⏰ <b>Monev {tgl} belum diisi</b> (sekarang {jam} WIB, batas 23.59)\n"
                f"Isi di HP: {APP}\n\n"
                f"<b>Uraian aktivitas</b>\n<code>{isi['activity_log']}</code>\n\n"
                f"<b>Pembelajaran</b>\n<code>{isi['lesson_learned']}</code>\n\n"
                f"<b>Kendala</b>\n<code>{isi['obstacles']}</code>\n\n"
                f"Kalau tidak diisi, bot akan kirim otomatis jam ~22.30 tanpa lokasi.\n"
                f"Tidak masuk hari ini? Balas: /izin alasannya"
            )

        elif cmd == "kirim":
            if os.environ.get("AUTO_SUBMIT", "1") != "1":
                notify(f"🚨 Monev {tgl} BELUM diisi dan kirim otomatis dimatikan. Isi sekarang: {APP}")
                return
            alasan = izin_hari_ini()
            if alasan:
                if dry:
                    print("[dry-run] akan kirim IZIN:", alasan)
                    return
                m.kirim_izin(tanggal, alasan)
                ok = m.sudah_isi(tanggal)
                if ok:
                    tandai_aman(tanggal, "izin")
                notify(f"{'✅' if ok else '❓'} Monev {tgl} dikirim otomatis: Tidak Hadir Dengan Keterangan — {alasan}")
                return
            isi = teks_laporan(tanggal)
            if dry:
                print("[dry-run] akan kirim HADIR:")
                for k, v in isi.items():
                    print(f"  {k} ({len(v)} kar): {v}")
                return
            m.kirim_hadir(tanggal, isi)
            ok = m.sudah_isi(tanggal)
            if ok:
                tandai_aman(tanggal, "otomatis")
                notify(f"✅ Monev {tgl} dikirim otomatis (Hadir, tanpa lokasi).")
            else:
                notify(f"❓ Monev {tgl} sudah dikirim tapi belum terlihat di sistem. Cek manual: {APP}")
        else:
            print(__doc__)
    except Exception as e:
        notify(f"❌ AutoMonev error ({cmd}) {tgl}: {e}\nIsi manual sekarang: {APP}")
        raise
    finally:
        m.close()


if __name__ == "__main__":
    if sys.stdout is None:  # dijalankan lewat pythonw (Task Scheduler): tulis log ke file
        sys.stdout = sys.stderr = open(HERE / "automonev.log", "a", encoding="utf-8", buffering=1)
        print(f"--- {datetime.now(WIB):%Y-%m-%d %H:%M} {' '.join(sys.argv[1:])}")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
