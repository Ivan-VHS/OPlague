//! Atomic export of application-level hardware inventory snapshots.
//!
//! These files are diagnostic reports. They are not Windows restore points,
//! kernel snapshots, or backups of the operating-system driver store.

use crate::HardwareReport;
use std::error::Error;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

pub fn default_snapshot_dir() -> PathBuf {
    #[cfg(target_os = "windows")]
    {
        if let Some(root) = std::env::var_os("LOCALAPPDATA") {
            return PathBuf::from(root).join("DuckDriverCore").join("Snapshots");
        }
    }

    #[cfg(target_os = "macos")]
    {
        if let Some(home) = std::env::var_os("HOME") {
            return PathBuf::from(home)
                .join("Library")
                .join("Application Support")
                .join("DuckDriverCore")
                .join("Snapshots");
        }
    }

    #[cfg(target_os = "linux")]
    {
        if let Some(root) = std::env::var_os("XDG_STATE_HOME") {
            return PathBuf::from(root).join("duckdriver-core").join("snapshots");
        }
        if let Some(home) = std::env::var_os("HOME") {
            return PathBuf::from(home)
                .join(".local")
                .join("state")
                .join("duckdriver-core")
                .join("snapshots");
        }
    }

    std::env::temp_dir()
        .join("duckdriver-core")
        .join("snapshots")
}

/// Write a JSON report through a temporary file and an atomic rename.
pub fn export_report(
    report: &HardwareReport,
) -> Result<PathBuf, Box<dyn Error + Send + Sync>> {
    let directory = default_snapshot_dir();
    fs::create_dir_all(&directory)?;

    let payload = serde_json::to_vec_pretty(report)?;
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)?
        .as_secs();

    for sequence in 0_u32..100 {
        let file_name = format!(
            "duckdriver-inventory-{timestamp}-{}-{sequence}.json",
            std::process::id()
        );
        let destination = directory.join(&file_name);
        if destination.exists() {
            continue;
        }

        let temporary = directory.join(format!(".{file_name}.tmp"));
        let mut file = match OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary)
        {
            Ok(file) => file,
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(error) => return Err(Box::new(error)),
        };

        file.write_all(&payload)?;
        file.sync_all()?;
        drop(file);
        fs::rename(&temporary, &destination)?;
        return Ok(destination);
    }

    Err("Could not allocate a unique inventory snapshot filename.".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::HardwareReport;

    #[test]
    fn snapshot_directory_is_not_the_current_working_directory() {
        let path = default_snapshot_dir();
        assert!(path.to_string_lossy().contains("duckdriver")
            || path.to_string_lossy().contains("DuckDriver"));
    }

    #[test]
    fn json_serialization_includes_schema_version() {
        let report = HardwareReport::new("test");
        let value = serde_json::to_value(report).expect("serialize report");
        assert_eq!(value["schema_version"], 1);
        assert_eq!(value["devices"].as_array().map(Vec::len), Some(0));
    }
}
