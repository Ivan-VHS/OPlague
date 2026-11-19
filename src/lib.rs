//! DuckDriver Core domain model and safe orchestration primitives.
//!
//! The first milestone is deliberately read-only: it inventories devices and
//! exports an application-level report. It does not install, replace, disable,
//! unload, or patch operating-system drivers.

pub mod inventory;
pub mod snapshot;
pub mod udrv;

use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

pub const APP_VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BusKind {
    Pci,
    Usb,
    Other,
}

impl BusKind {
    pub fn label(&self) -> &'static str {
        match self {
            Self::Pci => "PCI / PCIe",
            Self::Usb => "USB",
            Self::Other => "Other",
        }
    }
}

/// The binding state reported by the platform inventory provider.
///
/// Unknown is intentionally distinct from Unbound: a provider that cannot
/// prove a driver binding must not be presented as proof that no driver exists.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "state", content = "driver", rename_all = "snake_case")]
pub enum DriverBinding {
    Bound(String),
    Unbound,
    Unknown,
}

impl DriverBinding {
    pub fn label(&self) -> String {
        match self {
            Self::Bound(name) => format!("Bound: {name}"),
            Self::Unbound => "No bound driver reported".to_owned(),
            Self::Unknown => "Not reported by this provider".to_owned(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Device {
    pub id: String,
    pub name: String,
    pub bus: BusKind,
    pub device_class: String,
    pub vendor_id: Option<String>,
    pub product_id: Option<String>,
    pub driver: DriverBinding,
    /// Platform-reported status, retained verbatim where available.
    pub platform_status: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct HardwareReport {
    pub schema_version: u32,
    pub app_version: String,
    pub platform: String,
    pub collected_at_unix_secs: u64,
    pub devices: Vec<Device>,
    pub warnings: Vec<String>,
}

impl HardwareReport {
    pub fn new(platform: impl Into<String>) -> Self {
        let collected_at_unix_secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        Self {
            schema_version: 1,
            app_version: APP_VERSION.to_owned(),
            platform: platform.into(),
            collected_at_unix_secs,
            devices: Vec::new(),
            warnings: Vec::new(),
        }
    }

    pub fn pci_count(&self) -> usize {
        self.devices
            .iter()
            .filter(|device| device.bus == BusKind::Pci)
            .count()
    }

    pub fn usb_count(&self) -> usize {
        self.devices
            .iter()
            .filter(|device| device.bus == BusKind::Usb)
            .count()
    }

    pub fn summary(&self) -> String {
        format!(
            "{} devices discovered · {} PCI/PCIe · {} USB · {} provider warnings",
            self.devices.len(),
            self.pci_count(),
            self.usb_count(),
            self.warnings.len()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn summary_counts_only_matching_bus_types() {
        let mut report = HardwareReport::new("test");
        report.devices = vec![
            Device {
                id: "pci-0".into(),
                name: "Test PCI device".into(),
                bus: BusKind::Pci,
                device_class: "Test".into(),
                vendor_id: None,
                product_id: None,
                driver: DriverBinding::Unknown,
                platform_status: None,
            },
            Device {
                id: "usb-0".into(),
                name: "Test USB device".into(),
                bus: BusKind::Usb,
                device_class: "Test".into(),
                vendor_id: None,
                product_id: None,
                driver: DriverBinding::Unbound,
                platform_status: None,
            },
            Device {
                id: "other-0".into(),
                name: "Test other device".into(),
                bus: BusKind::Other,
                device_class: "Test".into(),
                vendor_id: None,
                product_id: None,
                driver: DriverBinding::Bound("test-driver".into()),
                platform_status: None,
            },
        ];

        assert_eq!(report.pci_count(), 1);
        assert_eq!(report.usb_count(), 1);
        assert!(report.summary().contains("3 devices discovered"));
    }

    #[test]
    fn unknown_driver_binding_is_not_misrepresented_as_unbound() {
        assert_ne!(DriverBinding::Unknown, DriverBinding::Unbound);
        assert!(DriverBinding::Unknown.label().contains("Not reported"));
    }

    #[test]
    fn report_has_a_versioned_schema() {
        let report = HardwareReport::new("test");
        assert_eq!(report.schema_version, 1);
        assert!(!report.app_version.is_empty());
    }
}
