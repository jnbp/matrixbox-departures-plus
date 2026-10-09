#!/usr/bin/env python3
"""Builds what a release ships, into dist/:

    departuresplus-install.bat   Windows: double-click, enter the board's IP, done
    departuresplus-<version>.zip the app folder plus install.py for every other system
"""
import base64, os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "departuresplus")
DIST = os.path.join(ROOT, "dist")
NAMES = sorted(n for n in os.listdir(APP) if not n.startswith((".", "__pycache__")) and n != "departuresplus.json")
with open(os.path.join(APP, "dp_cfg.py"), encoding="utf-8") as f:
    VERSION = [line for line in f if line.startswith("VERSION")][0].split('"')[1]

# The .bat starts PowerShell on its own tail: everything after the marker line.
HEAD = ("@echo off\r\ntitle Install Departures Plus on the MatrixBOX board\r\n"
        "powershell -NoProfile -ExecutionPolicy Bypass -Command \"$ip='%~1'; iex (((Get-Content -Raw -LiteralPath '%~f0') "
        "-split ('#PS'+'START#'),2)[1])\"\r\necho.\r\npause\r\nexit /b\r\n#PSSTART#\r\n")
PS = r'''
$ErrorActionPreference = 'Stop'
while (-not $ip) { $ip = Read-Host "IP address of the board" }
$ip = $ip -replace '^https?://', '' -replace '/.*$', ''
$dir = '/departuresplus'
$files = [ordered]@{}
__FILES__
function Send-Raw([string]$method, [string]$url, [string]$path, [byte[]]$body) {
  $req = [System.Net.HttpWebRequest]::Create($url)
  $req.Method = $method
  $req.Timeout = 30000
  $req.ReadWriteTimeout = 30000
  $req.KeepAlive = $false
  $req.Proxy = $null
  $req.ServicePoint.Expect100Continue = $false
  if ($method -eq 'POST') {
    $req.Headers.Add('x-path', $path)
    $req.ContentType = 'application/octet-stream'
    $req.ContentLength = $body.Length
    $s = $req.GetRequestStream()
    if ($body.Length -gt 0) { $s.Write($body, 0, $body.Length) }
    $s.Close()
  }
  $resp = $req.GetResponse()
  $reader = New-Object System.IO.StreamReader($resp.GetResponseStream(), [System.Text.Encoding]::UTF8)
  $text = $reader.ReadToEnd()
  $reader.Close()
  $resp.Close()
  return $text
}
function Send-Board([string]$route, [string]$path, [byte[]]$body) {
  return ((Send-Raw 'POST' "http://$ip$prefix/$route" $path $body) | ConvertFrom-Json)
}
$none = [byte[]]@()
Write-Host ""
Write-Host "Departures Plus __VERSION__ -> http://$ip$dir"
Write-Host ""
# The file manager only answers on the board's home screen, so stop whatever app is running.
try { $null = Send-Raw 'GET' "http://$ip/exit" '' $none } catch { }
Start-Sleep -Seconds 3
# Newer firmware serves the file manager under /system/fm, older (e.g. v0.97) under /fm.
$prefix = $null
$lastErr = ''
for ($try = 0; $try -lt 4 -and -not $prefix; $try++) {
  foreach ($cand in @('/system/fm', '/fm')) {
    $prefix = $cand
    try {
      $probe = Send-Board 'ls' '/' $none
      if ($probe.items) { break }
    } catch { $lastErr = $_.Exception.Message }
    $prefix = $null
  }
  if (-not $prefix) { Start-Sleep -Seconds 2 }
}
if (-not $prefix) {
  Write-Host "No file manager found at $ip : $lastErr" -ForegroundColor Red
  Write-Host "Check the IP, that this PC is in the same network, and that the board shows its home screen."
  return
}
try { $null = Send-Board 'mkdir' $dir $none } catch { }
# Remove the previous version first. The board has little room, and overwriting a file
# needs space for both copies. Your stations and settings (departuresplus.json) stay.
$removed = 0
try {
  (Send-Board 'ls' $dir $none).items | Where-Object { $_.n -ne 'departuresplus.json' } | ForEach-Object {
    try { $null = Send-Board 'del' "$dir/$($_.n)" $none; $removed++ } catch { }
  }
} catch { }
if ($removed) { Write-Host "removed the previous version ($removed files), kept your settings" }
$failed = @()
foreach ($name in $files.Keys) {
  $bytes = [System.Convert]::FromBase64String($files[$name])
  $ok = $false
  $err = ''
  for ($i = 0; $i -lt 3 -and -not $ok; $i++) {
    try {
      $res = Send-Board 'write' "$dir/$name" $bytes
      if ($res.ok) { $ok = $true } else { $err = [string]$res.error }
    } catch { $err = $_.Exception.Message; Start-Sleep -Seconds 1 }
  }
  if ($ok) { Write-Host ("ok      {0}  ({1} bytes)" -f $name, $bytes.Length) -ForegroundColor Green }
  else { Write-Host ("FAILED  {0}  {1}" -f $name, $err) -ForegroundColor Red; $failed += $name }
}
$onBoard = @{}
try { (Send-Board 'ls' $dir $none).items | ForEach-Object { $onBoard[$_.n] = [int]$_.s } } catch { }
foreach ($name in $files.Keys) {
  $want = [System.Convert]::FromBase64String($files[$name]).Length
  if ($onBoard[$name] -ne $want -and $failed -notcontains $name) { $failed += $name }
}
Write-Host ""
if ($failed.Count -eq 0) {
  Write-Host "Done: all $($files.Count) files are in $dir." -ForegroundColor Green
  try { $null = Send-Raw 'GET' "http://$ip/?run=departuresplus" '' $none; Write-Host "Started the app." } catch { }
  Write-Host "Settings page: http://$ip/"
  if (-not $noBrowser) { Start-Sleep -Seconds 4; Start-Process "http://$ip/" }
} else {
  Write-Host ("INCOMPLETE: " + ($failed -join ', ')) -ForegroundColor Red
  Write-Host "Is the board plugged into a computer by USB? Then its storage is read-only."
  Write-Host "Is its storage full? Remove an app you do not need. Otherwise just run this again."
}
'''


def read(name):
    with open(os.path.join(APP, name), "rb") as f: return f.read()


def main():
    os.makedirs(DIST, exist_ok=True)
    files = "\n".join("$files['%s'] = '%s'" % (n, base64.b64encode(read(n)).decode()) for n in NAMES)
    ps = PS.replace("__FILES__", files).replace("__VERSION__", VERSION).strip() + "\n"
    with open(os.path.join(DIST, "departuresplus-install.bat"), "wb") as f:
        f.write((HEAD + ps.replace("\n", "\r\n")).encode("ascii"))
    with zipfile.ZipFile(os.path.join(DIST, "departuresplus-%s.zip" % VERSION), "w", zipfile.ZIP_DEFLATED) as z:
        for n in NAMES: z.write(os.path.join(APP, n), "departuresplus/" + n)
        z.write(os.path.join(ROOT, "install.py"), "install.py")
        z.write(os.path.join(ROOT, "LICENSE"), "LICENSE")
    print("Departures Plus", VERSION, "->", ", ".join(sorted(os.listdir(DIST))))


if __name__ == "__main__":
    main()
