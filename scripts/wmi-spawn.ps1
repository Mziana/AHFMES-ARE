# wmi-spawn.ps1 - spawn proses DETACHED PENUH via WMI Win32_Process.Create.
#
# Mengapa WMI: proses anak dari node.exe (Next dev server) atau shell Freebuff
# mewarisi Windows JOB OBJECT kill-on-close - saat Freebuff/preview ditutup,
# SELURUH pohon ikut dibunuh walau `detached:true` + `unref()` di Node.
# Proses yang dibuat lewat WMI dianakkan ke WmiPrvSE.exe (proses sistem di
# luar job kita) sehingga hidup terlepas dari nasib Freebuff.
#
# Pakai:
#   Mode 1 (disarankan, quoting sederhana):
#     -CommandLine '"C:\...\python.exe" "D:\...\demo_driver.py"'
#   Mode 2 (kompatibilitas lama):
#     -File "C:\...\python.exe" -Args '"D:\...\demo_driver.py"' [-WorkDir ...]
#
# Output stdout: "OK <returnvalue> <pid>" saat sukses, "ERR <...>" saat gagal.
param(
  [string]$CommandLine = '',
  [string]$File = '',
  [string]$Args = '',
  [string]$WorkDir = ''
)

$ErrorActionPreference = 'Stop'

if (-not $WorkDir) {
  # default: root repo (parent dari scripts/)
  $WorkDir = Split-Path -Parent $PSScriptRoot
}

if ($CommandLine -and $CommandLine.Trim().Length -gt 0) {
  $CmdLine = $CommandLine
} elseif ($File) {
  $CmdLine = "`"$File`""
  if ($Args -and $Args.Trim().Length -gt 0) { $CmdLine = "$CmdLine $Args" }
} else {
  Write-Output 'ERR no CommandLine or File given'
  exit 1
}

try {
  $result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine                = $CmdLine
    CurrentDirectory           = $WorkDir
    ProcessStartupInformation  = $null
  }
  if ($result.ReturnValue -eq 0) {
    Write-Output "OK 0 $($result.ProcessId)"
    exit 0
  }
  Write-Output "ERR $($result.ReturnValue)"
  exit 1
}
catch {
  Write-Output "ERR $($_.Exception.Message)"
  exit 1
}
