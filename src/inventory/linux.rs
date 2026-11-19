use crate::{BusKind, Device, DriverBinding, HardwareReport};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

pub(super) fn scan() -> HardwareReport {
    scan_sysfs(Path::new("/sys"))
}

fn scan_sysfs(sys_root: &Path) -> HardwareReport {
    let mut report = HardwareReport::new(format!(
        "Linux {}",
        read_value(&sys_root.join("class/dmi/id/sys_vendor"))
            .filter(|value| !value.is_empty())
            .unwrap_or_else(|| "sysfs".to_owned())
    ));

    collect_pci(sys_root, &mut report);
    collect_usb(sys_root, &mut report);
    report.devices.sort_by(|left, right| left.id.cmp(&right.id));
    report
}

fn collect_pci(sys_root: &Path, report: &mut HardwareReport) {
    let root = sys_root.join("bus/pci/devices");
    let entries = match read_entries(&root) {
        Ok(entries) => entries,
        Err(error) => {
            report.warnings.push(format!(
                "PCI inventory unavailable at {}: {error}",
                root.display()
            ));
            return;
        }
    };

    for path in entries {
        let id = path
            .file_name()
            .map(|name| name.to_string_lossy().into_owned())
            .unwrap_or_else(|| "unknown-pci-device".to_owned());

        let vendor_id = read_value(&path.join("vendor"))
            .map(|value| value.trim_start_matches("0x").to_ascii_uppercase());
        let product_id = read_value(&path.join("device"))
            .map(|value| value.trim_start_matches("0x").to_ascii_uppercase());
        let class_code = read_value(&path.join("class")).unwrap_or_default();
        let driver = read_driver_binding(&path);

        let name = match (&vendor_id, &product_id) {
            (Some(vendor), Some(product)) => format!("PCI device {vendor}:{product}"),
            _ => format!("PCI device {id}"),
        };

        report.devices.push(Device {
            id,
            name,
            bus: BusKind::Pci,
            device_class: format!("PCI class {class_code}"),
            vendor_id,
            product_id,
            driver,
            platform_status: None,
        });
    }
}

fn collect_usb(sys_root: &Path, report: &mut HardwareReport) {
    let root = sys_root.join("bus/usb/devices");
    let entries = match read_entries(&root) {
        Ok(entries) => entries,
        Err(error) => {
            report.warnings.push(format!(
                "USB inventory unavailable at {}: {error}",
                root.display()
            ));
            return;
        }
    };

    for path in entries {
        let Some(vendor_id) = read_value(&path.join("idVendor")) else {
            // USB interface directories and root-hub metadata do not always
            // represent a standalone USB device entry.
            continue;
        };
        let product_id = read_value(&path.join("idProduct"));
        let manufacturer = read_value(&path.join("manufacturer")).unwrap_or_default();
        let product = read_value(&path.join("product")).unwrap_or_default();
        let id = path
            .file_name()
            .map(|name| name.to_string_lossy().into_owned())
            .unwrap_or_else(|| "unknown-usb-device".to_owned());

        let name = match (manufacturer.is_empty(), product.is_empty()) {
            (false, false) => format!("{manufacturer} {product}"),
            (false, true) => manufacturer,
            (true, false) => product,
            (true, true) => format!(
                "USB device {}:{}",
                vendor_id,
                product_id.as_deref().unwrap_or("unknown")
            ),
        };

        report.devices.push(Device {
            id,
            name,
            bus: BusKind::Usb,
            device_class: "USB".to_owned(),
            vendor_id: Some(vendor_id.to_ascii_uppercase()),
            product_id: product_id.map(|value| value.to_ascii_uppercase()),
            driver: read_driver_binding(&path),
            platform_status: None,
        });
    }
}

fn read_entries(path: &Path) -> io::Result<Vec<PathBuf>> {
    let mut entries = fs::read_dir(path)?
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .collect::<Vec<_>>();
    entries.sort();
    Ok(entries)
}

fn read_value(path: &Path) -> Option<String> {
    fs::read_to_string(path)
        .ok()
        .map(|value| value.trim().to_owned())
        .filter(|value| !value.is_empty())
}

fn read_driver_binding(device_path: &Path) -> DriverBinding {
    match fs::read_link(device_path.join("driver")) {
        Ok(target) => {
            let driver_name = target
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or_else(|| target.display().to_string());
            DriverBinding::Bound(driver_name)
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => DriverBinding::Unbound,
        Err(_) => DriverBinding::Unknown,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temporary_sysfs() -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        std::env::temp_dir().join(format!("ddc-sysfs-test-{}-{nonce}", std::process::id()))
    }

    #[test]
    fn scans_pci_and_usb_entries_without_mutating_them() {
        let root = temporary_sysfs();
        let pci = root.join("bus/pci/devices/0000:01:00.0");
        let usb = root.join("bus/usb/devices/1-1");
        fs::create_dir_all(&pci).expect("create PCI fixture");
        fs::create_dir_all(&usb).expect("create USB fixture");
        fs::write(pci.join("vendor"), "0x10DE").expect("write vendor");
        fs::write(pci.join("device"), "0x2684").expect("write device");
        fs::write(pci.join("class"), "0x030000").expect("write class");
        fs::write(usb.join("idVendor"), "046D").expect("write USB vendor");
        fs::write(usb.join("idProduct"), "C547").expect("write USB product");
        fs::write(usb.join("manufacturer"), "Example").expect("write manufacturer");
        fs::write(usb.join("product"), "Input Device").expect("write product");

        let report = scan_sysfs(&root);

        assert_eq!(report.pci_count(), 1);
        assert_eq!(report.usb_count(), 1);
        assert_eq!(report.devices.len(), 2);
        assert_eq!(report.devices[0].driver, DriverBinding::Unbound);
        fs::remove_dir_all(root).expect("remove fixture");
    }

    #[test]
    fn missing_sysfs_roots_produce_warnings_instead_of_panics() {
        let root = temporary_sysfs();
        let report = scan_sysfs(&root);
        assert!(report.devices.is_empty());
        assert_eq!(report.warnings.len(), 2);
    }
}
