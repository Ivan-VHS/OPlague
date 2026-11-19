use duckdriver_core::{HardwareReport, inventory, snapshot, udrv};
use std::error::Error;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

slint::include_modules!();

fn main() -> Result<(), Box<dyn Error>> {
    if std::env::args().any(|argument| argument == "--scan-json") {
        let report = inventory::scan().map_err(std::io::Error::other)?;
        println!("{}", serde_json::to_string_pretty(&report)?);
        return Ok(());
    }

    run_desktop()
}

fn run_desktop() -> Result<(), Box<dyn Error>> {
    let window = MainWindow::new()?;
    let latest_report: Arc<Mutex<Option<HardwareReport>>> = Arc::new(Mutex::new(None));
    let scan_generation = Arc::new(AtomicU64::new(0));

    let scan_window = window.as_weak();
    let scan_state = Arc::clone(&latest_report);
    let scan_sequence = Arc::clone(&scan_generation);

    window.on_scan_requested(move || {
        let generation = scan_sequence.fetch_add(1, Ordering::SeqCst) + 1;
        if let Some(window) = scan_window.upgrade() {
            window.set_status_text("Scanning PCI/PCIe and USB inventory…".into());
            window.set_device_list(
                "Reading operating-system inventory surfaces. No drivers will be changed."
                    .into(),
            );
        }

        let window_weak = scan_window.clone();
        let latest = Arc::clone(&scan_state);
        let sequence = Arc::clone(&scan_sequence);

        let _worker = std::thread::spawn(move || {
            let result = inventory::scan();
            let update = move || {
                if sequence.load(Ordering::SeqCst) != generation {
                    return;
                }

                let Some(window) = window_weak.upgrade() else {
                    return;
                };

                match result {
                    Ok(report) => {
                        let devices = if report.devices.is_empty() {
                            "No devices were returned by the available provider.".to_owned()
                        } else {
                            report
                                .devices
                                .iter()
                                .take(18)
                                .map(|device| {
                                    format!(
                                        "• {}\n  {} · {} · {}",
                                        device.name,
                                        device.bus.label(),
                                        device.id,
                                        device.driver.label()
                                    )
                                })
                                .collect::<Vec<_>>()
                                .join("\n\n")
                        };

                        let warnings = if report.warnings.is_empty() {
                            "No provider warnings.".to_owned()
                        } else {
                            report.warnings.join("\n")
                        };

                        window.set_device_count(report.devices.len().to_string().into());
                        window.set_pci_count(report.pci_count().to_string().into());
                        window.set_usb_count(report.usb_count().to_string().into());
                        window.set_scan_summary(report.summary().into());
                        window.set_device_list(devices.into());
                        window.set_warnings_text(warnings.into());
                        window.set_status_text(
                            format!("Inventory complete · {}", report.platform).into(),
                        );

                        match latest.lock() {
                            Ok(mut stored) => *stored = Some(report),
                            Err(_) => {
                                window.set_status_text(
                                    "Inventory complete, but the in-memory report lock was unavailable."
                                        .into(),
                                );
                            }
                        }
                    }
                    Err(error) => {
                        window.set_status_text(format!("Inventory failed: {error}").into());
                        window.set_scan_summary("No report was created.".into());
                        window.set_warnings_text(
                            "Check platform permissions and the inventory provider.".into(),
                        );
                    }
                }
            };

            if let Err(error) = slint::invoke_from_event_loop(update) {
                eprintln!("Could not update the desktop window: {error}");
            }
        });
    });

    let export_window = window.as_weak();
    let export_state = Arc::clone(&latest_report);
    window.on_export_requested(move || {
        let report = export_state.lock().ok().and_then(|stored| stored.clone());

        let Some(report) = report else {
            if let Some(window) = export_window.upgrade() {
                window.set_status_text("Run a hardware scan before exporting a snapshot.".into());
            }
            return;
        };

        match snapshot::export_report(&report) {
            Ok(path) => {
                if let Some(window) = export_window.upgrade() {
                    window.set_status_text(
                        format!("Inventory snapshot saved: {}", path.display()).into(),
                    );
                }
            }
            Err(error) => {
                if let Some(window) = export_window.upgrade() {
                    window.set_status_text(format!("Snapshot export failed: {error}").into());
                }
            }
        }
    });

    let forge_sources = Arc::new(Mutex::new(Vec::<std::path::PathBuf>::new()));

    let folder_window = window.as_weak();
    let folder_sources = Arc::clone(&forge_sources);
    window.on_forge_add_folder(move || {
        let Some(path) = rfd::FileDialog::new()
            .set_title("Select a folder to add to the UDRV data bundle")
            .pick_folder()
        else {
            return;
        };

        let count = match folder_sources.lock() {
            Ok(mut sources) => {
                sources.push(path);
                sources.len()
            }
            Err(_) => 0,
        };

        if let Some(window) = folder_window.upgrade() {
            window.set_source_summary(format!("{count} source item(s) selected").into());
            window.set_status_text("Folder added. The .UDRV builder stores files as data only.".into());
        }
    });

    let files_window = window.as_weak();
    let files_sources = Arc::clone(&forge_sources);
    window.on_forge_add_files(move || {
        let Some(paths) = rfd::FileDialog::new()
            .set_title("Select files to add to the UDRV data bundle")
            .pick_files()
        else {
            return;
        };

        let count = match files_sources.lock() {
            Ok(mut sources) => {
                sources.extend(paths);
                sources.len()
            }
            Err(_) => 0,
        };

        if let Some(window) = files_window.upgrade() {
            window.set_source_summary(format!("{count} source item(s) selected").into());
            window.set_status_text("Files added. No installer or driver binary will be executed.".into());
        }
    });

    let clear_window = window.as_weak();
    let clear_sources = Arc::clone(&forge_sources);
    window.on_forge_clear_sources(move || {
        let cleared = clear_sources
            .lock()
            .map(|mut sources| {
                let count = sources.len();
                sources.clear();
                count
            })
            .unwrap_or(0);

        if let Some(window) = clear_window.upgrade() {
            window.set_source_summary("No source items selected".into());
            window.set_bundle_summary("No bundle has been created or verified.".into());
            window.set_status_text(format!("Cleared {cleared} source item(s).").into());
        }
    });

    let build_window = window.as_weak();
    let build_sources = Arc::clone(&forge_sources);
    window.on_forge_build_requested(move || {
        let sources = match build_sources.lock() {
            Ok(sources) => sources.clone(),
            Err(_) => {
                if let Some(window) = build_window.upgrade() {
                    window.set_status_text("Could not access the source selection.".into());
                }
                return;
            }
        };

        if sources.is_empty() {
            if let Some(window) = build_window.upgrade() {
                window.set_status_text("Add at least one file or folder before building a .UDRV bundle.".into());
            }
            return;
        }

        let Some(output) = rfd::FileDialog::new()
            .set_title("Save DuckDriver data bundle")
            .set_file_name("duckdriver-core.udrv")
            .add_filter("DuckDriver bundle", &["udrv"])
            .save_file()
        else {
            return;
        };

        if let Some(window) = build_window.upgrade() {
            window.set_status_text("Building a data-only UDRV container in the background…".into());
        }

        let window_weak = build_window.clone();
        let _worker = std::thread::spawn(move || {
            let result = udrv::build_archive(&sources, &output, "DuckDriver Core bundle");
            let update = move || {
                let Some(window) = window_weak.upgrade() else {
                    return;
                };

                match result {
                    Ok(summary) => {
                        window.set_bundle_summary(summary.describe().into());
                        window.set_status_text(
                            format!("UDRV data container created: {}", output.display()).into(),
                        );
                    }
                    Err(error) => {
                        window.set_status_text(format!("UDRV build failed: {error}").into());
                    }
                }
            };

            if let Err(error) = slint::invoke_from_event_loop(update) {
                eprintln!("Could not report UDRV build result: {error}");
            }
        });
    });

    let verify_window = window.as_weak();
    window.on_forge_verify_requested(move || {
        let Some(path) = rfd::FileDialog::new()
            .set_title("Select a DuckDriver data bundle to verify")
            .add_filter("DuckDriver bundle", &["udrv"])
            .pick_file()
        else {
            return;
        };

        if let Some(window) = verify_window.upgrade() {
            window.set_status_text("Verifying UDRV header, manifest, payload and content hashes…".into());
        }

        let window_weak = verify_window.clone();
        let _worker = std::thread::spawn(move || {
            let result = udrv::verify_archive(&path);
            let update = move || {
                let Some(window) = window_weak.upgrade() else {
                    return;
                };

                match result {
                    Ok(summary) => {
                        window.set_bundle_summary(summary.describe().into());
                        window.set_status_text(
                            format!("UDRV integrity verification passed: {}", path.display()).into(),
                        );
                    }
                    Err(error) => {
                        window.set_status_text(format!("UDRV verification failed: {error}").into());
                    }
                }
            };

            if let Err(error) = slint::invoke_from_event_loop(update) {
                eprintln!("Could not report UDRV verification result: {error}");
            }
        });
    });

    window.run()?;
    Ok(())
}
