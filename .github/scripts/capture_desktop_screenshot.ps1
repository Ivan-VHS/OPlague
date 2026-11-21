param(
  [Parameter(Mandatory=$true)][string]$FilePath,
  [string[]]$Arguments = @(),
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [string]$ActionKey = "",
  [int]$StartupSeconds = 12
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class DesktopCaptureNative {
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
try { Set-DisplayResolution -Width 1920 -Height 1080 -Force -ErrorAction Stop } catch { Write-Warning "Runner resolution could not be changed; captured desktop will be normalized." }
$target = Join-Path (Get-Location) $OutputPath
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
$process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -PassThru -WindowStyle Normal
$handle = [IntPtr]::Zero
$visibleProcess = $null
$processName = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
for ($i = 0; $i -lt ($StartupSeconds * 4); $i++) {
  Start-Sleep -Milliseconds 250
  # GUI bootloaders (including PyInstaller one-file apps) may spawn a child
  # process. Poll all matching processes and capture the one with a real window.
  $candidates = @(Get-Process -Name $processName -ErrorAction SilentlyContinue)
  foreach ($candidate in $candidates) {
    $candidate.Refresh()
    if ($candidate.MainWindowHandle -ne [IntPtr]::Zero) {
      $visibleProcess = $candidate
      $handle = $candidate.MainWindowHandle
      break
    }
  }
  if ($handle -ne [IntPtr]::Zero) { break }
}
if ($handle -eq [IntPtr]::Zero) {
  $remaining = @(Get-Process -Name $processName -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
  throw "No visible application window was created by $FilePath. Remaining process IDs: $($remaining -join ', ')."
}
[void][DesktopCaptureNative]::ShowWindowAsync($handle, 3)
[void][DesktopCaptureNative]::SetForegroundWindow($handle)
Start-Sleep -Seconds 2
if ($ActionKey) { [System.Windows.Forms.SendKeys]::SendWait($ActionKey); Start-Sleep -Seconds 2 }
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$source = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$graphics = [System.Drawing.Graphics]::FromImage($source)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap = New-Object System.Drawing.Bitmap(1920, 1080)
$canvas = [System.Drawing.Graphics]::FromImage($bitmap)
$canvas.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$canvas.DrawImage($source, 0, 0, 1920, 1080)
$bitmap.Save($target, [System.Drawing.Imaging.ImageFormat]::Png)
$canvas.Dispose(); $bitmap.Dispose(); $graphics.Dispose(); $source.Dispose()
Write-Host "Saved live desktop capture: $OutputPath (source: $($bounds.Width)x$($bounds.Height))."
try {
  Get-Process -Name $processName -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue
} catch {}
