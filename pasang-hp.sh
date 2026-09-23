#!/data/data/com.termux/files/usr/bin/bash
# Pasang AutoMonev di Termux (Android). Jalankan dari folder repo:
#   bash pasang-hp.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "== 1/4 Install Python + requests"
pkg install -y python >/dev/null
pip install -q requests

echo "== 2/4 Isi kredensial (.env)"
if [ -f .env ]; then
  echo ".env sudah ada, dilewati (hapus dulu kalau mau isi ulang)."
else
  read -rp "Email/No HP SiapKerja : " MU
  read -rsp "Password SiapKerja    : " MP; echo
  read -rp "Token bot Telegram    : " TT
  read -rp "Chat ID Telegram [7075945474]: " TC
  TC=${TC:-7075945474}
  printf 'MONEV_USER=%s\nMONEV_PASS=%s\nTG_TOKEN=%s\nTG_CHAT_ID=%s\nAUTO_SUBMIT=1\n' "$MU" "$MP" "$TT" "$TC" > .env
  chmod 600 .env
fi

echo "== 3/4 Buat perintah untuk Termux:Tasker"
mkdir -p ~/.termux/tasker
for cmd in ingat kirim; do
  cat > ~/.termux/tasker/automonev-$cmd <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$DIR"
echo "--- \$(date '+%Y-%m-%d %H:%M') $cmd" >> automonev.log
python automonev.py $cmd >> automonev.log 2>&1
EOF
  chmod 700 ~/.termux/tasker/automonev-$cmd
done
mkdir -p ~/.termux
grep -q '^allow-external-apps' ~/.termux/termux.properties 2>/dev/null \
  || echo 'allow-external-apps=true' >> ~/.termux/termux.properties
termux-reload-settings 2>/dev/null || true

echo "== 4/4 Tes login"
python automonev.py cek

echo
echo "Selesai. Sekarang atur MacroDroid (lihat README bagian HP)."
