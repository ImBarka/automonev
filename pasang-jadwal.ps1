# Pasang jadwal AutoMonev di Windows Task Scheduler — CADANGAN untuk HP.
# HP (Termux + MacroDroid) menjalankan pengingat dan kirim 22.30/23.15.
# Laptop hanya mengirim jam 23.30 kalau HP gagal; bot selalu cek "sudah terisi?"
# dulu, jadi tidak akan terkirim dobel.
#
# Jalankan sekali:  powershell -ExecutionPolicy Bypass -File pasang-jadwal.ps1
# Hapus jadwal:     Unregister-ScheduledTask -TaskName "AutoMonev*" -Confirm:$false

$dir = $PSScriptRoot
$pythonw = Join-Path (Split-Path (Get-Command python).Source) "pythonw.exe"
$script = Join-Path $dir "automonev.py"

# Bersihkan jadwal lama (versi sebelum HP dipakai)
Get-ScheduledTask -TaskName "AutoMonev*" -ErrorAction SilentlyContinue |
    Unregister-ScheduledTask -Confirm:$false

$jadwal = @(
    @{ Nama = "AutoMonev 2330 kirim cadangan"; Jam = "23:30"; Cmd = "kirim" }
)

# StartWhenAvailable: kalau laptop mati/tidur saat jadwal, jalankan begitu nyala lagi.
# WakeToRun: bangunkan laptop dari mode Sleep (bukan dari Shut down).
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

foreach ($j in $jadwal) {
    $action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$script`" $($j.Cmd)" -WorkingDirectory $dir
    $trigger = New-ScheduledTaskTrigger -Daily -At $j.Jam
    Register-ScheduledTask -TaskName $j.Nama -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "OK  $($j.Nama)"
}
Write-Host "`nSelesai. Log ada di $dir\automonev.log"
