//! Platform hardware discovery adapters.
//!
//! Providers are intentionally read-only. No adapter in this crate installs,
//! removes, disables, or reconfigures a driver.

#![forbid(unsafe_code)]

use oplague_core::InventorySnapshot;

/// Discover devices using the current operating-system provider.
pub fn discover() -> InventorySnapshot {
    #[cfg(target_os = "linux")]
    {
        linux::discover()
    }

    #[cfg(target_os = "windows")]
    {
        let mut snapshot = InventorySnapshot::empty("Windows", false);
        snapshot.warnings.push(
            "Windows SetupAPI / Configuration Manager provider is specified but not implemented yet."
                .to_owned(),
        );
        snapshot
    }

    #[cfg(target_os = "macos")]
    {
        let mut snapshot = InventorySnapshot::empty("macOS", false);
        snapshot
            .warnings
            .push("IOKit provider is not implemented yet.".to_owned());
        snapshot
    }

    #[cfg(not(any(target_os = "linux", target_os = "windows", target_os = "macos")))]
    {
        let mut snapshot = InventorySnapshot::empty(std::env::consts::OS, false);
        snapshot
            .warnings
            .push("No hardware provider is available for this platform.".to_owned());
        snapshot
    }
}

#[cfg(target_os = "linux")]
mod linux;
