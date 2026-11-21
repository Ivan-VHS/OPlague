param(
  [Parameter(Mandatory=$true)][string]$FilePath,
  [string[]]$Arguments = @(),
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [string]$ActionKey = "",
  [int]$StartupSeconds = 15
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class OPlagueCaptureNative {
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@

try {
  Set-DisplayResolution -Width 1920 -Height 1080 -Force -ErrorAction Stop
} catch {
  Write-Warning "Runner resolution could not be changed; the captured desktop will be normalized."
}

$resolvedPath = (Resolve-Path -LiteralPath $FilePath).Path
$processName = [System.IO.Path]::GetFileNameWithoutExtension($resolvedPath)
$startedAt = Get-Date
$launcher = Start-Process -FilePath $resolvedPath -ArgumentList $Arguments -PassThru -WindowStyle Normal
$windowProcess = $null

# PyInstaller --onefile starts a short-lived bootloader and then a second
# process that owns the Tk window. Start-Process may return the bootloader,
# whose MainWindowHandle remains zero. Find the visible process created by
# this launch instead of assuming the launcher PID owns the application UI.
for ($i = 0; $i -lt ($StartupSeconds * 4); $i++) {
  $candidates = @(
    Get-Process -Name $processName -ErrorAction SilentlyContinue |
      Where-Object {
        try {
          $_.StartTime -ge $startedAt.AddSeconds(-3) -and
          $_.MainWindowHandle -ne [IntPtr]::Zero
        } catch {
          $false
        }
      }
  )
  if ($candidates.Count -gt 0) {
    $windowProcess = $candidates | Sort-Object StartTime | Select-Object -First 1
    break
  }
  Start-Sleep -Milliseconds 250
}

if ($null -eq $windowProcess) {
  $observed = Get-Process -Name $processName -ErrorAction SilentlyContinue |
    Select-Object Id, MainWindowTitle, MainWindowHandle
  throw "No visible application window was created by $resolvedPath. Processes observed: $($observed | ConvertTo-Json -Compress)"
}

[void][OPlagueCaptureNative]::ShowWindowAsync($windowProcess.MainWindowHandle, 3)
[void][OPlagueCaptureNative]::SetForegroundWindow($windowProcess.MainWindowHandle)
Start-Sleep -Seconds 2
if ($ActionKey) {
  [System.Windows.Forms.SendKeys]::SendWait($ActionKey)
  Start-Sleep -Seconds 2
}

$target = Join-Path (Get-Location) $OutputPath
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$source = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
$sourceGraphics = [System.Drawing.Graphics]::FromImage($source)
$sourceGraphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

$bitmap = New-Object System.Drawing.Bitmap(1920, 1080)
$canvas = [System.Drawing.Graphics]::FromImage($bitmap)
$canvas.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$canvas.DrawImage($source, 0, 0, 1920, 1080)
$bitmap.Save($target, [System.Drawing.Imaging.ImageFormat]::Png)

$canvas.Dispose()
$bitmap.Dispose()
$sourceGraphics.Dispose()
$source.Dispose()
Write-Host "Saved live Windows application capture: $OutputPath (source: $($bounds.Width)x$($bounds.Height))."

# The runner is disposable; stop only processes of this application started
# during this capture, including the PyInstaller one-file child process.
$ownedProcesses = @(
  Get-Process -Name $processName -ErrorAction SilentlyContinue |
    Where-Object {
      try { $_.StartTime -ge $startedAt.AddSeconds(-3) } catch { $false }
    }
)
foreach ($owned in $ownedProcesses) {
  try { Stop-Process -Id $owned.Id -Force -ErrorAction SilentlyContinue } catch {}
}
try { Stop-Process -Id $launcher.Id -Force -ErrorAction SilentlyContinue } catch {}
