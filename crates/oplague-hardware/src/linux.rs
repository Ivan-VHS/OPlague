//! Read-only Linux PCI and USB inventory using sysfs.

use std::{collections::HashSet, fs, path::Path};

use oplague_core::{
    BusType, DeviceStatus, DriverBinding, HardwareDevice, InventorySnapshot, SignatureState,
};

/// Enumerate visible PCI and USB functions from sysfs.
pub(super) fn discover() -> InventorySnapshot {
    let mut snapshot = InventorySnapshot::empty("Linux", true);
    let mut seen = HashSet::new();

    scan_pci(Path::new("/sys/bus/pci/devices"), &mut snapshot, &mut seen);
    scan_usb(Path::new("/sys/bus/usb/devices"), &mut snapshot, &mut seen);

    snapshot
        .devices
        .sort_by(|left, right| left.friendly_name.cmp(&right.friendly_name));
    snapshot.coverage_complete = false;
    snapshot.warnings.push(
        "Покрытие ограничено PCI и USB sysfs; это не полный аудит всех классов устройств."
            .to_owned(),
    );
    snapshot
}

fn scan_pci(root: &Path, snapshot: &mut InventorySnapshot, seen: &mut HashSet<String>) {
    let entries = match fs::read_dir(root) {
        Ok(entries) => entries,
        Err(error) => {
            snapshot
                .warnings
                .push(format!("Не удалось прочитать {}: {error}", root.display()));
            return;
        }
    };

    for entry in entries.flatten() {
        let path = entry.path();
        let Some(vendor) = read_hex_id(&path.join("vendor")) else {
            continue;
        };
        let Some(device_id) = read_hex_id(&path.join("device")) else {
            continue;
        };
        let instance_id = entry.file_name().to_string_lossy().into_owned();
        if !seen.insert(instance_id.clone()) {
            continue;
        }

        snapshot.devices.push(HardwareDevice {
            instance_id,
            friendly_name: format!("PCI {vendor}:{device_id}"),
            bus: BusType::Pci,
            hardware_ids: vec![format!("PCI\\VEN_{vendor}&DEV_{device_id}")],
            driver: driver_binding(&path),
            status: DeviceStatus::Present,
        });
    }
}

fn scan_usb(root: &Path, snapshot: &mut InventorySnapshot, seen: &mut HashSet<String>) {
    let entries = match fs::read_dir(root) {
        Ok(entries) => entries,
        Err(error) => {
            snapshot
                .warnings
                .push(format!("Не удалось прочитать {}: {error}", root.display()));
            return;
        }
    };

    for entry in entries.flatten() {
        let path = entry.path();
        let entry_name = entry.file_name().to_string_lossy().into_owned();
        if entry_name.contains(':') {
            continue;
        }

        let Some(vendor) = read_hex_id(&path.join("idVendor")) else {
            continue;
        };
        let Some(product_id) = read_hex_id(&path.join("idProduct")) else {
            continue;
        };

        let instance_id = format!("USB:{entry_name}");
        if !seen.insert(instance_id.clone()) {
            continue;
        }

        let manufacturer = read_text(&path.join("manufacturer"));
        let product = read_text(&path.join("product"));
        let friendly_name = match (manufacturer, product) {
            (Some(manufacturer), Some(product)) => format!("{manufacturer} {product}"),
            (_, Some(product)) => product,
            (Some(manufacturer), None) => manufacturer,
            (None, None) => format!("USB {vendor}:{product_id}"),
        };

        snapshot.devices.push(HardwareDevice {
            instance_id,
            friendly_name,
            bus: BusType::Usb,
            hardware_ids: vec![format!("USB\\VID_{vendor}&PID_{product_id}")],
            driver: driver_binding(&path),
            status: DeviceStatus::Present,
        });
    }
}

fn read_text(path: &Path) -> Option<String> {
    fs::read_to_string(path)
        .ok()
        .map(|value| value.trim().to_owned())
        .filter(|value| !value.is_empty())
}

fn read_hex_id(path: &Path) -> Option<String> {
    let value = read_text(path)?;
    normalize_hex_id(&value)
}

fn normalize_hex_id(value: &str) -> Option<String> {
    let value = value.trim().trim_start_matches("0x");
    let parsed = u16::from_str_radix(value, 16).ok()?;
    Some(format!("{parsed:04X}"))
}

fn driver_binding(device_path: &Path) -> Option<DriverBinding> {
    let target = fs::read_link(device_path.join("driver")).ok()?;
    let name = target.file_name()?.to_string_lossy().into_owned();
    Some(DriverBinding {
        name,
        version: None,
        signature: SignatureState::Unknown,
    })
}

#[cfg(test)]
mod tests {
    use super::normalize_hex_id;

    #[test]
    fn normalizes_sysfs_hex_ids() {
        assert_eq!(normalize_hex_id("0x1a2b"), Some("1A2B".to_owned()));
        assert_eq!(normalize_hex_id("00ff"), Some("00FF".to_owned()));
    }

    #[test]
    fn rejects_invalid_or_overflowing_ids() {
        assert_eq!(normalize_hex_id("not-hex"), None);
        assert_eq!(normalize_hex_id("10000"), None);
    }
}
