<#
.SYNOPSIS
  Show how Windows sees the CM5 hid-bridge (run on the target PC, no admin needed).

.DESCRIPTION
  Lists the USB device and its two HID children with hardware IDs, driver,
  and status, so you can confirm the PC sees only "USB Input Device",
  "HID Keyboard Device" and "HID-compliant mouse" bound to Microsoft's
  in-box class drivers.

.PARAMETER Vid
  USB vendor ID as 4 hex digits (default 1209, matching config.toml).
.PARAMETER Pid
  USB product ID as 4 hex digits (default 0001).
#>
param(
    [string]$Vid = "1209",
    [string]$Pid = "0001"
)

$pattern = "VID_$Vid&PID_$Pid"
$devices = Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -match $pattern }
if (-not $devices) {
    Write-Host "No present device with $pattern. Is the CM5 plugged in and hid-gadget active?" -ForegroundColor Yellow
    Write-Host "All present USB/HID devices:"
    Get-PnpDevice -PresentOnly -Class USB,HIDClass,Keyboard,Mouse | Sort-Object Class | Format-Table Class, FriendlyName, InstanceId -AutoSize
    exit 1
}

foreach ($d in $devices | Sort-Object InstanceId) {
    Write-Host ""
    Write-Host ("[{0}] {1}" -f $d.Class, $d.FriendlyName) -ForegroundColor Cyan
    Write-Host ("  InstanceId : {0}" -f $d.InstanceId)
    Write-Host ("  Status     : {0}" -f $d.Status)
    $props = Get-PnpDeviceProperty -InstanceId $d.InstanceId -KeyName `
        'DEVPKEY_Device_HardwareIds', 'DEVPKEY_Device_CompatibleIds', 'DEVPKEY_Device_Service', `
        'DEVPKEY_Device_DriverProvider', 'DEVPKEY_Device_BusReportedDeviceDesc' -ErrorAction SilentlyContinue
    foreach ($p in $props) {
        $value = if ($p.Data -is [array]) { $p.Data -join ", " } else { $p.Data }
        Write-Host ("  {0,-30}: {1}" -f ($p.KeyName -replace 'DEVPKEY_Device_', ''), $value)
    }
}

Write-Host ""
Write-Host "Expected: one 'USB Input Device' per interface (Service HidUsb, provider Microsoft)," 
Write-Host "          one 'HID Keyboard Device' (kbdhid) and one 'HID-compliant mouse' (mouhid)."
Write-Host "For raw descriptors use Microsoft's USBView (Windows SDK) or Thesycon USB Descriptor Dumper."
