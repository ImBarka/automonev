# Pasang jadwal AutoMonev di Windows Task Scheduler.
# Jalankan sekali:  powershell -ExecutionPolicy Bypass -File pasang-jadwal.ps1
# Hapus jadwal:     Unregister-ScheduledTask -TaskName "AutoMonev*" -Confirm:$false

$dir = $PSScriptRoot
$pythonw = Join-Path (Split-Path (Get-Command python).Source) "pythonw.exe"
$script = Join-Path $dir "automonev.py"

$jadwal = @(
    @{ Nama = "AutoMonev 1600 ingat"; Jam = "16:00"; Cmd = "ingat" },
    @{ Nama = "AutoMonev 1900 ingat"; Jam = "19:00"; Cmd = "ingat" },
    @{ Nama = "AutoMonev 2100 ingat"; Jam = "21:00"; Cmd = "ingat" },
    @{ Nama = "AutoMonev 2230 kirim"; Jam = "22:30"; Cmd = "kirim" },
    @{ Nama = "AutoMonev 2315 kirim"; Jam = "23:15"; Cmd = "kirim" }
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
