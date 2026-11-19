use crate::{BusKind, Device, DriverBinding, HardwareReport};
use serde_json::Value;
use std::process::Command;

const POWERSHELL_INVENTORY: &str = r#"$ErrorActionPreference = 'Stop'; Get-PnpDevice -PresentOnly | Select-Object InstanceId,FriendlyName,Class,Status | ConvertTo-Json -Compress"#;

/// Query Windows PnP inventory through the built-in read-only Get-PnpDevice
/// cmdlet. No vendor installer, registry mutation, or driver replacement is
/// performed.
pub(super) fn scan() -> Result<HardwareReport, String> {
    let output = Command::new("powershell.exe")
        .args([
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            POWERSHELL_INVENTORY,
        ])
        .output()
        .map_err(|error| format!("Could not start PowerShell PnP inventory: {error}"))?;

    if !output.status.success() {
        let detail = String::from_utf8_lossy(&output.stderr).trim().to_owned();
        return Err(if detail.is_empty() {
            format!("Get-PnpDevice failed with status {}", output.status)
        } else {
            format!("Get-PnpDevice failed: {detail}")
        });
    }

    let value: Value = serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("Could not decode the PnP inventory JSON: {error}"))?;

    let mut report = HardwareReport::new("Windows PnP");
    let devices = match value {
        Value::Array(items) => items,
        Value::Null => Vec::new(),
        item => vec![item],
    };

    for item in devices {
        let id = field(&item, "InstanceId");
        if id.is_empty() {
            report
                .warnings
                .push("Skipped a PnP item without an InstanceId.".to_owned());
            continue;
        }

        let name = field(&item, "FriendlyName");
        let class = field(&item, "Class");
        let status = field(&item, "Status");
        let bus = classify_instance_id(&id);

        report.devices.push(Device {
            id,
            name: if name.is_empty() {
                "Unnamed PnP device".to_owned()
            } else {
                name
            },
            bus,
            device_class: if class.is_empty() {
                "Unclassified PnP device".to_owned()
            } else {
                class
            },
            vendor_id: None,
            product_id: None,
            // Get-PnpDevice Status is not proof of a particular driver binary
            // or version. Keep binding state unknown until a provider can
            // verify the driver stack separately.
            driver: DriverBinding::Unknown,
            platform_status: if status.is_empty() {
                None
            } else {
                Some(status)
            },
        });
    }

    report.devices.sort_by(|left, right| left.id.cmp(&right.id));
    Ok(report)
}

fn field(value: &Value, key: &str) -> String {
    value
        .get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .trim()
        .to_owned()
}

fn classify_instance_id(instance_id: &str) -> BusKind {
    let normalized = instance_id.to_ascii_uppercase();
    if normalized.starts_with("PCI\\") {
        BusKind::Pci
    } else if normalized.starts_with("USB\\") {
        BusKind::Usb
    } else {
        BusKind::Other
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn classifies_common_windows_pnp_instance_prefixes() {
        assert_eq!(classify_instance_id("PCI\\VEN_10DE&DEV_2684"), BusKind::Pci);
        assert_eq!(classify_instance_id("USB\\VID_046D&PID_C547"), BusKind::Usb);
        assert_eq!(classify_instance_id("ACPI\\PNP0A08"), BusKind::Other);
    }

    #[test]
    fn field_reader_handles_missing_or_non_string_values() {
        assert_eq!(field(&Value::Null, "FriendlyName"), "");
        assert_eq!(
            field(
                &serde_json::json!({"FriendlyName": "Keyboard"}),
                "FriendlyName"
            ),
            "Keyboard"
        );
    }
}
