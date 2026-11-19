slint::include_modules!();

use slint::ComponentHandle;

fn inventory_text(snapshot: &oplague_core::InventorySnapshot) -> (String, String) {
    if !snapshot.supported {
        let detail = snapshot
            .warnings
            .first()
            .cloned()
            .unwrap_or_else(|| "Системный адаптер этой платформы ещё не подключён.".to_owned());
        return ("Адаптер недоступен".to_owned(), detail);
    }

    if snapshot.devices.is_empty() {
        return (
            "Устройства не обнаружены".to_owned(),
            "Сканирование завершено; проверьте доступность sysfs и подключение оборудования."
                .to_owned(),
        );
    }

    let names = snapshot
        .devices
        .iter()
        .take(5)
        .map(|device| format!("• {}", device.friendly_name))
        .collect::<Vec<_>>()
        .join("\n");
    let overflow = snapshot.devices.len().saturating_sub(5);
    let summary = if overflow > 0 {
        format!("{} устройств обнаружено (+ ещё {})", snapshot.devices.len(), overflow)
    } else {
        format!("{} устройств обнаружено", snapshot.devices.len())
    };
    let detail = format!(
        "{}\n\nТолько чтение: конфигурация и драйверы не изменялись.",
        names
    );
    (summary, detail)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let window = MainWindow::new()?;

    let initial = oplague_hardware::discover();
    let (summary, detail) = inventory_text(&initial);
    window.set_devices_summary(summary.into());
    window.set_status_message(detail.into());

    let weak_window = window.as_weak();
    window.on_scan_requested(move || {
        let snapshot = oplague_hardware::discover();
        let (summary, detail) = inventory_text(&snapshot);
        if let Some(window) = weak_window.upgrade() {
            window.set_devices_summary(summary.into());
            window.set_status_message(detail.into());
        }
    });

    window.run()?;
    Ok(())
}
