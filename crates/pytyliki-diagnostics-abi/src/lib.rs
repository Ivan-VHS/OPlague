use core::ffi::c_char;
use core::mem::{align_of, offset_of, size_of};
use std::ffi::CStr;

pub const CORE_ABI_VERSION: u32 = 1;
pub const DIAGNOSTICS_ABI_VERSION: u32 = 1;
pub const DIAGNOSTIC_V1_SIZE: usize = 144;
pub const DIAGNOSTIC_MESSAGE_CAP: usize = 96;

pub const STATUS_OK: i32 = 0;
pub const STATUS_INVALID_ARGUMENT: i32 = -1;
pub const STATUS_UNSUPPORTED_ABI: i32 = -2;
pub const STATUS_BUFFER_TOO_SMALL: i32 = -3;
pub const STATUS_LIMIT_EXCEEDED: i32 = -5;
pub const STATUS_NON_FINITE_INPUT: i32 = -6;
pub const STATUS_NUMERIC_OVERFLOW: i32 = -7;

pub const DIAG_OK: i32 = 0;
pub const DIAG_INVALID_ARGUMENT: i32 = 1001;
pub const DIAG_BUFFER_TOO_SMALL: i32 = 1002;
pub const DIAG_UNSUPPORTED_ABI: i32 = 1003;
pub const DIAG_LIMIT_EXCEEDED: i32 = 1004;
pub const DIAG_NON_FINITE_INPUT: i32 = 1005;
pub const DIAG_NUMERIC_OVERFLOW: i32 = 1006;

#[repr(C, align(8))]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DiagnosticV1 {
    pub struct_size: u32,
    pub abi_version: u32,
    pub code: i32,
    pub severity: u32,
    pub source_offset: u64,
    pub source_length: u64,
    pub detail: u64,
    pub message_size: u32,
    pub reserved: u32,
    pub message: [c_char; DIAGNOSTIC_MESSAGE_CAP],
}

impl Default for DiagnosticV1 {
    fn default() -> Self {
        Self {
            struct_size: size_of::<Self>() as u32,
            abi_version: DIAGNOSTICS_ABI_VERSION,
            code: DIAG_OK,
            severity: 0,
            source_offset: u64::MAX,
            source_length: 0,
            detail: 0,
            message_size: 0,
            reserved: 0,
            message: [0; DIAGNOSTIC_MESSAGE_CAP],
        }
    }
}

impl DiagnosticV1 {
    pub fn message(&self) -> &str {
        if self.message_size == 0 || self.message_size as usize > self.message.len() {
            return "";
        }

        // The C ABI guarantees a NUL-terminated message within the fixed buffer.
        unsafe { CStr::from_ptr(self.message.as_ptr()) }
            .to_str()
            .unwrap_or("")
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DistanceError {
    DimensionMismatch {
        left: usize,
        right: usize,
    },
    UnsupportedAbi {
        core: u32,
        diagnostics: u32,
    },
    Native {
        status: i32,
        diagnostic: DiagnosticV1,
    },
}

unsafe extern "C" {
    fn pytyliki_abi_version() -> u32;
    fn pytyliki_diagnostics_abi_version() -> u32;
    fn pytyliki_v1_diagnostic_init(out_size: u32, out: *mut DiagnosticV1) -> i32;
    fn pytyliki_v1_distance_f64_ex(
        left: *const f64,
        right: *const f64,
        count: u64,
        out: *mut f64,
        diagnostic_buffer_size: u32,
        diagnostic: *mut DiagnosticV1,
    ) -> i32;
}

pub fn abi_versions() -> (u32, u32) {
    // The shared library is selected explicitly by the build environment.
    unsafe { (pytyliki_abi_version(), pytyliki_diagnostics_abi_version()) }
}

pub fn euclidean_distance(left: &[f64], right: &[f64]) -> Result<f64, DistanceError> {
    if left.len() != right.len() {
        return Err(DistanceError::DimensionMismatch {
            left: left.len(),
            right: right.len(),
        });
    }

    let versions = abi_versions();
    if versions != (CORE_ABI_VERSION, DIAGNOSTICS_ABI_VERSION) {
        return Err(DistanceError::UnsupportedAbi {
            core: versions.0,
            diagnostics: versions.1,
        });
    }

    let mut diagnostic = DiagnosticV1::default();
    let diagnostic_size = size_of::<DiagnosticV1>() as u32;
    let init_status = unsafe { pytyliki_v1_diagnostic_init(diagnostic_size, &mut diagnostic) };
    if init_status != STATUS_OK {
        return Err(DistanceError::Native {
            status: init_status,
            diagnostic,
        });
    }

    let count = u64::try_from(left.len()).unwrap_or(u64::MAX);
    let mut output = 0.0;
    let status = unsafe {
        pytyliki_v1_distance_f64_ex(
            left.as_ptr(),
            right.as_ptr(),
            count,
            &mut output,
            diagnostic_size,
            &mut diagnostic,
        )
    };

    if status == STATUS_OK {
        Ok(output)
    } else {
        Err(DistanceError::Native { status, diagnostic })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn c_layout_matches_diagnostics_v1() {
        assert_eq!(size_of::<DiagnosticV1>(), DIAGNOSTIC_V1_SIZE);
        assert_eq!(align_of::<DiagnosticV1>(), 8);
        assert_eq!(offset_of!(DiagnosticV1, code), 8);
        assert_eq!(offset_of!(DiagnosticV1, source_offset), 16);
        assert_eq!(offset_of!(DiagnosticV1, detail), 32);
        assert_eq!(offset_of!(DiagnosticV1, message_size), 40);
        assert_eq!(offset_of!(DiagnosticV1, message), 48);
    }

    #[test]
    fn native_library_exposes_both_abi_versions() {
        assert_eq!(abi_versions(), (CORE_ABI_VERSION, DIAGNOSTICS_ABI_VERSION));
    }

    #[test]
    fn native_distance_uses_the_real_c_library() {
        let distance = euclidean_distance(&[3.0, 4.0], &[0.0, 0.0]).unwrap();
        assert_eq!(distance, 5.0);
    }

    #[test]
    fn native_diagnostics_preserve_error_code_and_message() {
        let error = euclidean_distance(&[1.0, f64::NAN], &[0.0, 0.0])
            .expect_err("non-finite input must be rejected by the C ABI");

        match error {
            DistanceError::Native { status, diagnostic } => {
                assert_eq!(status, STATUS_NON_FINITE_INPUT);
                assert_eq!(diagnostic.code, DIAG_NON_FINITE_INPUT);
                assert_eq!(diagnostic.detail, 1);
                assert_eq!(diagnostic.message(), "Vector contains a non-finite value");
            }
            other => panic!("unexpected error: {other:?}"),
        }
    }

    #[test]
    fn native_empty_input_is_rejected_without_panicking() {
        let error =
            euclidean_distance(&[], &[]).expect_err("zero-dimensional input must be rejected");

        match error {
            DistanceError::Native { status, diagnostic } => {
                assert_eq!(status, STATUS_INVALID_ARGUMENT);
                assert_eq!(diagnostic.code, DIAG_INVALID_ARGUMENT);
            }
            other => panic!("unexpected error: {other:?}"),
        }
    }

    #[test]
    fn wrapper_rejects_mismatched_slice_lengths_before_ffi() {
        assert_eq!(
            euclidean_distance(&[1.0, 2.0], &[1.0]),
            Err(DistanceError::DimensionMismatch { left: 2, right: 1 })
        );
    }

    #[test]
    fn native_dimension_limit_is_enforced() {
        let left = vec![1.0; 4097];
        let right = vec![0.0; 4097];
        let error = euclidean_distance(&left, &right)
            .expect_err("the C ABI dimension limit must be enforced");

        match error {
            DistanceError::Native { status, diagnostic } => {
                assert_eq!(status, STATUS_LIMIT_EXCEEDED);
                assert_eq!(diagnostic.code, DIAG_LIMIT_EXCEEDED);
                assert_eq!(diagnostic.detail, 4096);
            }
            other => panic!("unexpected error: {other:?}"),
        }
    }
}
