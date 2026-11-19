//! Shared, platform-independent domain model for OPlague.

#![forbid(unsafe_code)]

/// Hardware bus used to discover a device.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BusType {
    /// PCI or PCI Express.
    Pci,
    /// USB device.
    Usb,
    /// Human interface device.
    Hid,
    /// ACPI-enumerated device.
    Acpi,
    /// Audio endpoint or audio interface.
    Audio,
    /// Network interface.
    Network,
    /// Platform did not provide a bus classification.
    Unknown,
}

/// Confidence in the signature state of a driver package.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SignatureState {
    /// Signature was verified by a trusted platform API.
    Verified,
    /// Platform verification explicitly reported an invalid signature.
    Invalid,
    /// The provider did not return enough evidence.
    Unknown,
}

/// Presence or health state reported by a platform provider.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DeviceStatus {
    /// Device is enumerated and present.
    Present,
    /// Provider reported a problem code or failed state.
    Problem,
    /// Provider could not establish the state.
    Unknown,
}

/// Driver package currently associated with a device.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DriverBinding {
    /// Provider-reported driver service or package name.
    pub name: String,
    /// Version returned by the platform, when available.
    pub version: Option<String>,
    /// Signature result returned by a trusted verification API.
    pub signature: SignatureState,
}

/// A normalized, platform-independent hardware device record.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HardwareDevice {
    /// Stable platform instance identifier.
    pub instance_id: String,
    /// Human-readable name, or an explicit fallback derived from hardware IDs.
    pub friendly_name: String,
    /// Bus classification.
    pub bus: BusType,
    /// Hardware IDs reported by the operating system.
    pub hardware_ids: Vec<String>,
    /// Current driver binding, if known.
    pub driver: Option<DriverBinding>,
    /// Provider-reported presence or problem state.
    pub status: DeviceStatus,
}

/// Result of a local hardware inventory pass.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InventorySnapshot {
    /// Human-readable platform identifier.
    pub platform: String,
    /// Whether a real provider ran for this platform.
    pub supported: bool,
    /// Whether the provider enumerated all device classes in its contract.
    pub coverage_complete: bool,
    /// Discovered devices.
    pub devices: Vec<HardwareDevice>,
    /// Non-fatal provider limitations or read errors.
    pub warnings: Vec<String>,
}

impl InventorySnapshot {
    /// Create an empty snapshot for a named platform.
    pub fn empty(platform: impl Into<String>, supported: bool) -> Self {
        Self {
            platform: platform.into(),
            supported,
            coverage_complete: false,
            devices: Vec::new(),
            warnings: Vec::new(),
        }
    }
}

/// Evidence required to calculate an explainable health index.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HealthEvidence {
    /// The provider completed every required inventory category.
    pub coverage_complete: bool,
    /// Number of devices included in the assessment.
    pub total_devices: u32,
    /// Devices for which the OS reported a failure state.
    pub failed_devices: u32,
    /// Unresolved conflicts confirmed by a diagnostic provider.
    pub unresolved_conflicts: u32,
    /// Driver packages with explicitly invalid signatures.
    pub invalid_signatures: u32,
}

/// A bounded health index from 0 to 100.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct HealthScore(u8);

impl HealthScore {
    /// Calculate a score only when the evidence is complete and non-empty.
    ///
    /// Penalties: 25 points per failed device, 15 per confirmed unresolved
    /// conflict, and 20 per invalid driver signature. Result is clamped to 0..=100.
    pub fn from_evidence(evidence: HealthEvidence) -> Option<Self> {
        if !evidence.coverage_complete || evidence.total_devices == 0 {
            return None;
        }

        let penalty = evidence
            .failed_devices
            .saturating_mul(25)
            .saturating_add(evidence.unresolved_conflicts.saturating_mul(15))
            .saturating_add(evidence.invalid_signatures.saturating_mul(20));
        let score = 100_u32.saturating_sub(penalty).min(100);
        Some(Self(u8::try_from(score).ok()?))
    }

    /// Return the score as an integer percentage.
    pub const fn value(self) -> u8 {
        self.0
    }
}

/// Types of operations exposed by the future orchestration service.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OperationKind {
    /// Read-only inventory.
    Inventory,
    /// Read-only package inspection.
    AnalyzePackage,
    /// Install a driver package.
    InstallDriver,
    /// Remove a driver package.
    RemoveDriver,
    /// Restore a previously captured driver/configuration snapshot.
    RestoreSnapshot,
    /// Write an allowed device configuration.
    WriteDeviceConfiguration,
}

/// Safety gates that must be satisfied before an operation may execute.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OperationPolicy {
    /// Whether the operation requires an elevated system service.
    pub requires_elevation: bool,
    /// Whether a verified recovery point must exist before execution.
    pub requires_snapshot: bool,
    /// Whether the user must explicitly confirm the exact change set.
    pub requires_confirmation: bool,
    /// Whether this operation may change OS or device state.
    pub mutates_system: bool,
}

impl OperationKind {
    /// Return the conservative default policy for this operation.
    pub const fn policy(self) -> OperationPolicy {
        match self {
            Self::Inventory | Self::AnalyzePackage => OperationPolicy {
                requires_elevation: false,
                requires_snapshot: false,
                requires_confirmation: false,
                mutates_system: false,
            },
            Self::InstallDriver
            | Self::RemoveDriver
            | Self::RestoreSnapshot
            | Self::WriteDeviceConfiguration => OperationPolicy {
                requires_elevation: true,
                requires_snapshot: true,
                requires_confirmation: true,
                mutates_system: true,
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn health_score_is_unknown_without_complete_evidence() {
        let evidence = HealthEvidence {
            coverage_complete: false,
            total_devices: 10,
            failed_devices: 0,
            unresolved_conflicts: 0,
            invalid_signatures: 0,
        };
        assert_eq!(HealthScore::from_evidence(evidence), None);
    }

    #[test]
    fn health_score_is_unknown_for_empty_inventory() {
        let evidence = HealthEvidence {
            coverage_complete: true,
            total_devices: 0,
            failed_devices: 0,
            unresolved_conflicts: 0,
            invalid_signatures: 0,
        };
        assert_eq!(HealthScore::from_evidence(evidence), None);
    }

    #[test]
    fn health_score_uses_documented_penalties() {
        let evidence = HealthEvidence {
            coverage_complete: true,
            total_devices: 8,
            failed_devices: 1,
            unresolved_conflicts: 1,
            invalid_signatures: 1,
        };
        assert_eq!(
            HealthScore::from_evidence(evidence).map(HealthScore::value),
            Some(40)
        );
    }

    #[test]
    fn read_only_operations_do_not_require_elevation_or_rollback() {
        let policy = OperationKind::Inventory.policy();
        assert!(!policy.requires_elevation);
        assert!(!policy.requires_snapshot);
        assert!(!policy.requires_confirmation);
        assert!(!policy.mutates_system);
    }

    #[test]
    fn system_mutations_require_all_safety_gates() {
        for kind in [
            OperationKind::InstallDriver,
            OperationKind::RemoveDriver,
            OperationKind::RestoreSnapshot,
            OperationKind::WriteDeviceConfiguration,
        ] {
            let policy = kind.policy();
            assert!(policy.requires_elevation);
            assert!(policy.requires_snapshot);
            assert!(policy.requires_confirmation);
            assert!(policy.mutates_system);
        }
    }
}
