# are_watchdog.ps1 - penjaga ketersediaan ARE (rev6, owner 2026-09-11).
#
# Latar: driver demo & bridge MT5 dulunya anak proses Next/shell Freebuff dan
# mewarisi Windows JOB OBJECT kill-on-close - Freebuff ditutup => bridge+driver
# mati diam-diam (kasus 11 Sep: tanpa eksekusi 01:26 sampai 06:04).
#
# Watchdog ini DI-SPAWN VIA WMI (di luar job Freebuff) sehingga kebal, dan:
#   1. Cek bridge /health (HTTP + token) tiap 30 detik.
#   2. Cek heartbeat driver (driver_state.json last_poll_ts <= 90s).
#   3. Transisi ok->down / down->ok  => notifikasi TOAST Windows (fallback balloon).
#   4. Driver mati                   => auto-restart via WMI (cooldown 120s).
#      Bridge HTTP down              => auto-restart via WMI (cooldown 180s).
#      mt5_connected false 2x        => auto-restart bridge (cooldown 180s).
#   5. Menulis data/logs/are_watchdog.log + are_watchdog_heartbeat.json
#      (dibaca UI untuk badge "WATCHDOG AKTIF").
#
# Semua proses yang di-restart adalah komponen DEMO (bridge lokal + driver demo
# R1). Tidak pernah menyentuh posisi: driver start tidak pernah kirim order,
# bridge hanya server lokal ber-token. File ini sengaja 100% ASCII (PS 5.1
# membaca .ps1 tanpa BOM sebagai ANSI - karakter non-ASCII merusak parsing).

param([int]$IntervalSec = 30)

$ErrorActionPreference = 'Continue'
$repo        = Split-Path -Parent $PSScriptRoot
$tokenFile   = Join-Path $repo 'data\bridge_token.txt'
$stateFile   = Join-Path $repo 'data\research\r1\demo\driver_state.json'
$logFile     = Join-Path $repo 'data\logs\are_watchdog.log'
$hbFile      = Join-Path $repo 'data\logs\are_watchdog_heartbeat.json'
$pidFile     = Join-Path $repo 'data\logs\are_watchdog.pid'
$spawnScript = Join-Path $PSScriptRoot 'wmi-spawn.ps1'
$driverPy    = Join-Path $repo 'strategy_v2\demo_driver.py'

# single instance: pid lock
try {
  if (Test-Path $pidFile) {
    $old = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($old -match '^\d+$' -and (Get-Process -Id ([int]$old) -ErrorAction SilentlyContinue)) {
      Write-Output "watchdog sudah jalan (pid $old) - exit"
      exit 0
    }
  }
  Set-Content -Path $pidFile -Value "$PID"
} catch { }

# python: utamakan interpreter asli (bukan shim WindowsApps)
$py = $null
try {
  $core = Get-ChildItem "$env:LocalAppData\Python" -Filter 'python.exe' -Recurse -ErrorAction SilentlyContinue |
          Where-Object { $_.FullName -match 'pythoncore' } | Select-Object -First 1
  if ($core) { $py = $core.FullName }
} catch { }
if (-not $py) { try { $py = (Get-Command python.exe -ErrorAction Stop).Source } catch { $py = 'python' } }

function Write-Log([string]$msg) {
  try {
    $dir = Split-Path -Parent $logFile
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if ((Test-Path $logFile) -and ((Get-Item $logFile).Length -gt 2000000)) {
      Move-Item -Force $logFile "$logFile.1"
    }
    Add-Content -Path $logFile -Value ("{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg)
  } catch { }
}

function Send-Toast([string]$title, [string]$body) {
  try {
    $eT = [System.Net.WebUtility]::HtmlEncode($title)
    $eB = [System.Net.WebUtility]::HtmlEncode($body)
    $xmlStr = '<toast><visual><binding template="ToastGeneric"><text>' + $eT + '</text><text>' + $eB + '</text></binding></visual></toast>'
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType=WindowsRuntime] | Out-Null
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($xmlStr)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('AHFMES ARE Watchdog').Show($toast)
  } catch {
    try {
      Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
      Add-Type -AssemblyName System.Drawing -ErrorAction SilentlyContinue
      $ni = New-Object System.Windows.Forms.NotifyIcon
      $ni.Icon = [System.Drawing.SystemIcons]::Warning
      $ni.Visible = $true
      $ni.ShowBalloonTip(8000, $title, $body, [System.Windows.Forms.ToolTipIcon]::Warning)
      Start-Sleep -Seconds 10
      $ni.Dispose()
    } catch { Write-Log "toast gagal total: $title / $body" }
  }
}

# toast anti-spam: transisi selalu kirim; ulangan outage sama dibatasi cooldown
$script:lastToast = @{}
function Send-ToastIfDue([string]$key, [int]$cooldownSec, [string]$title, [string]$body) {
  $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  $last = 0
  if ($script:lastToast.ContainsKey($key)) { $last = $script:lastToast[$key] }
  if (($now - $last) -lt $cooldownSec) { return }
  $script:lastToast[$key] = $now
  Send-Toast $title $body
}

# $cmdLine = command line utuh, contoh: "C:\...python.exe" -m are.mt5_server --port 18888
function Spawn-Detached([string]$cmdLine) {
  try {
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $spawnScript -CommandLine $cmdLine -WorkDir $repo 2>&1
    Write-Log ("spawn " + $cmdLine + " -> " + ($out -join ' '))
    return ("$out" -match '^OK')
  } catch {
    Write-Log "spawn gagal: $_"
    return $false
  }
}

$pyBridge = '"' + $py + '" -m are.mt5_server --port 18888'
$pyDriver = '"' + $py + '" "' + $driverPy + '"'

$script:wasBad       = @{ bridge = $false; driver = $false }
$script:mt5BadCount  = 0
$script:lastDrvStart = 0
$script:lastBrgStart = 0

Write-Log "== ARE watchdog mulai (interval ${IntervalSec}s, pid $PID, python=$py) =="
Send-Toast 'ARE Watchdog aktif' 'Penjaga bridge MT5 + driver demo berjalan. Notifikasi muncul bila koneksi terputus.'

while ($true) {
  Start-Sleep -Seconds $IntervalSec
  $epoch = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  $actions = @()

  # 1. bridge /health
  $bridgeOk = $false; $mt5Ok = $false
  try {
    $tok = (Get-Content $tokenFile -Raw -ErrorAction Stop).Trim()
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:18888/health' -Headers @{ Authorization = "Bearer $tok" } -TimeoutSec 8 -UseBasicParsing
    if ($resp.StatusCode -eq 200) {
      $h = $resp.Content | ConvertFrom-Json
      $bridgeOk = $true
      $mt5Ok = [bool]$h.mt5_connected
    }
  } catch { $bridgeOk = $false }

  if (-not $bridgeOk) {
    Send-ToastIfDue 'bridge' 180 'ARE: BRIDGE MT5 TERPUTUS' 'Bridge 127.0.0.1:18888 tidak merespons. Auto-restart bridge dicoba otomatis.'
    Write-Log 'ALERT bridge DOWN'
    if (($epoch - $script:lastBrgStart) -ge 180) {
      if (Spawn-Detached $pyBridge) {
        $script:lastBrgStart = $epoch
        $actions += 'restart-bridge'
        Send-Toast 'ARE: bridge MT5 direstart' 'Watchdog menyalakan ulang bridge (python -m are.mt5_server).'
      }
    }
  } elseif (-not $mt5Ok) {
    $script:mt5BadCount++
    if ($script:mt5BadCount -ge 2) {
      Send-ToastIfDue 'mt5' 300 'ARE: MT5 terminal tidak terkoneksi' 'Bridge hidup tetapi mt5_connected=false. Auto-restart bridge (re-connect MT5) dicoba.'
      Write-Log "ALERT mt5 disconnected (x$script:mt5BadCount)"
      if (($epoch - $script:lastBrgStart) -ge 180) {
        if (Spawn-Detached $pyBridge) {
          $script:lastBrgStart = $epoch
          $actions += 'restart-bridge(mt5)'
        }
      }
    }
  } else {
    $script:mt5BadCount = 0
  }

  if ($script:wasBad.bridge -and $bridgeOk) {
    Send-Toast 'ARE: Bridge MT5 pulih' 'Koneksi bridge 18888 kembali normal.'
    Write-Log "RECOVER bridge OK (mt5=$mt5Ok)"
  }
  $script:wasBad.bridge = (-not $bridgeOk)

  # 2. heartbeat driver
  $driverOk = $false; $drvPid = $null
  try {
    $st = Get-Content $stateFile -Raw -ErrorAction Stop | ConvertFrom-Json
    $drvPid = $st.pid
    if ($drvPid) {
      $age = $epoch - [int64]$st.last_poll_ts
      if ($age -le 90) {
        $driverOk = $true
      } else {
        # heartbeat basi: proses macet/hampir mati - bunuh agar restart bersih
        Write-Log "driver heartbeat basi (${age}s, pid $drvPid) - kill untuk restart bersih"
        try { Stop-Process -Id ([int]$drvPid) -Force -ErrorAction SilentlyContinue } catch { }
      }
    }
  } catch { $driverOk = $false }

  if (-not $driverOk) {
    Send-ToastIfDue 'driver' 180 'ARE: DRIVER DEMO BERHENTI' 'Driver demo R1 tidak merespons. Auto-restart dicoba otomatis (posisi tetap di broker).'
    Write-Log 'ALERT driver DOWN'
    if (($epoch - $script:lastDrvStart) -ge 120) {
      if (Spawn-Detached $pyDriver) {
        $script:lastDrvStart = $epoch
        $actions += 'restart-driver'
        Send-Toast 'ARE: driver demo direstart' 'Watchdog menyalakan ulang demo_driver.py.'
      }
    }
  }
  if ($script:wasBad.driver -and $driverOk) {
    Send-Toast 'ARE: Driver demo pulih' 'Heartbeat driver normal kembali.'
    Write-Log 'RECOVER driver OK'
  }
  $script:wasBad.driver = (-not $driverOk)

  # 3. heartbeat watchdog (dibaca UI)
  try {
    $hb = @{ last_tick = $epoch; interval_s = $IntervalSec; bridge_ok = $bridgeOk; mt5_ok = $mt5Ok;
             driver_ok = $driverOk; driver_pid = $drvPid; actions = ($actions -join ','); watchdog_pid = $PID }
    $hb | ConvertTo-Json -Compress | Set-Content -Path $hbFile
  } catch { }

  if ($actions.Count -gt 0) { Write-Log ("tick actions: " + ($actions -join ',')) }
}
