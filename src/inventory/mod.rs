//! Read-only hardware inventory providers.
//!
//! Platform providers only query operating-system inventory surfaces. They
//! never write device configuration or invoke a driver installer.

#[cfg(target_os = "linux")]
mod linux;
#[cfg(target_os = "windows")]
mod windows;

use crate::HardwareReport;

/// Collect a best-effort hardware inventory for the current platform.
///
/// Unsupported platforms return a report with a clear warning rather than
/// fabricated devices or inferred driver state.
pub fn scan() -> Result<HardwareReport, String> {
    #[cfg(target_os = "linux")]
    {
        return Ok(linux::scan());
    }

    #[cfg(target_os = "windows")]
    {
        return windows::scan();
    }

    #[allow(unreachable_code)]
    {
        let mut report = HardwareReport::new(std::env::consts::OS);
        report.warnings.push(
            "This platform inventory provider is not implemented yet. No device data was fabricated."
                .to_owned(),
        );
        Ok(report)
    }
}
