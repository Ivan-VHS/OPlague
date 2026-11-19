//! Versioned DuckDriver container format (.udrv).
//!
//! UDRV v1 is a portable, integrity-checked package container. It stores
//! source files as data; it is not an executable driver, bytecode VM, or
//! cross-OS kernel compatibility layer.

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

const MAGIC: &[u8; 8] = b"DUCKOMNI";
const FORMAT_VERSION: u32 = 1;
const HEADER_LEN: usize = 56;
const MAX_MANIFEST_BYTES: usize = 16 * 1024 * 1024;
const MAX_ENTRY_BYTES: u64 = 1024 * 1024 * 1024;
const MAX_PAYLOAD_BYTES: u64 = 4 * 1024 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
enum StorageCodec {
    Raw,
    Zstd,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct Manifest {
    format: String,
    format_version: u32,
    bundle_name: String,
    entry_count: u32,
    entries: Vec<ManifestEntry>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
struct ManifestEntry {
    path: String,
    offset: u64,
    stored_size: u64,
    original_size: u64,
    codec: StorageCodec,
    blake3: String,
}

#[derive(Clone, Debug)]
struct StoredBlob {
    offset: u64,
    stored_size: u64,
    codec: StorageCodec,
}

#[derive(Clone, Debug, Default)]
pub struct BundleSummary {
    pub entry_count: usize,
    pub unique_blobs: usize,
    pub original_bytes: u64,
    pub stored_bytes: u64,
    pub container_bytes: u64,
}

impl BundleSummary {
    pub fn describe(&self) -> String {
        format!(
            "{} files · {} unique blobs · {} → {} bytes",
            self.entry_count,
            self.unique_blobs,
            self.original_bytes,
            self.stored_bytes
        )
    }
}

/// Build a .udrv data container from one or more files and directories.
///
/// Exact duplicate files are stored once by BLAKE3 content hash. Each unique
/// file is compressed with Zstandard only when compression makes it smaller.
pub fn build_archive(
    sources: &[PathBuf],
    output: &Path,
    bundle_name: &str,
) -> Result<BundleSummary, String> {
    if sources.is_empty() {
        return Err("Add at least one source file or directory first.".to_owned());
    }

    let mut payload = Vec::<u8>::new();
    let mut entries = Vec::<ManifestEntry>::new();
    let mut deduplicated = HashMap::<String, StoredBlob>::new();
    let mut original_bytes = 0_u64;

    for (index, source) in sources.iter().enumerate() {
        let canonical = fs::canonicalize(source)
            .map_err(|error| format!("Cannot access {}: {error}", source.display()))?;
        let prefix = format!("source_{:03}", index + 1);

        if canonical.is_file() {
            let file_name = canonical
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .filter(|name| !name.is_empty())
                .ok_or_else(|| format!("Invalid file name: {}", canonical.display()))?;
            add_file(
                &canonical,
                format!("{prefix}/{file_name}"),
                &mut payload,
                &mut entries,
                &mut deduplicated,
                &mut original_bytes,
            )?;
        } else if canonical.is_dir() {
            for item in WalkDir::new(&canonical).follow_links(false) {
                let item = item.map_err(|error| {
                    format!("Cannot walk source directory {}: {error}", canonical.display())
                })?;
                if item.depth() == 0 || !item.file_type().is_file() {
                    // Symlinks are deliberately not followed or packaged.
                    continue;
                }

                let relative = item
                    .path()
                    .strip_prefix(&canonical)
                    .map_err(|error| format!("Cannot normalize source path: {error}"))?
                    .to_string_lossy()
                    .replace('\\', "/");
                add_file(
                    item.path(),
                    format!("{prefix}/{relative}"),
                    &mut payload,
                    &mut entries,
                    &mut deduplicated,
                    &mut original_bytes,
                )?;
            }
        } else {
            return Err(format!(
                "Source is neither a regular file nor a directory: {}",
                source.display()
            ));
        }
    }

    if entries.is_empty() {
        return Err("The selected sources contain no regular files.".to_owned());
    }

    let entry_count = u32::try_from(entries.len())
        .map_err(|_| "Too many entries for UDRV v1.".to_owned())?;
    let manifest = Manifest {
        format: "DUCK-OMNI".to_owned(),
        format_version: FORMAT_VERSION,
        bundle_name: bundle_name.to_owned(),
        entry_count,
        entries,
    };
    let manifest_bytes = serde_json::to_vec(&manifest)
        .map_err(|error| format!("Cannot encode UDRV manifest: {error}"))?;

    if manifest_bytes.len() > MAX_MANIFEST_BYTES {
        return Err("The UDRV manifest exceeds the v1 size limit.".to_owned());
    }
    if payload.len() as u64 > MAX_PAYLOAD_BYTES {
        return Err("The UDRV payload exceeds the v1 size limit.".to_owned());
    }

    let mut hasher = blake3::Hasher::new();
    hasher.update(&manifest_bytes);
    hasher.update(&payload);
    let digest = hasher.finalize();

    let mut header = Vec::with_capacity(HEADER_LEN);
    header.extend_from_slice(MAGIC);
    header.extend_from_slice(&FORMAT_VERSION.to_le_bytes());
    header.extend_from_slice(&(manifest_bytes.len() as u32).to_le_bytes());
    header.extend_from_slice(&(payload.len() as u64).to_le_bytes());
    header.extend_from_slice(digest.as_bytes());
    debug_assert_eq!(header.len(), HEADER_LEN);

    write_atomically(output, &header, &manifest_bytes, &payload)?;

    let summary = verify_archive(output)?;
    Ok(BundleSummary {
        entry_count: summary.entry_count,
        unique_blobs: summary.unique_blobs,
        original_bytes,
        stored_bytes: payload.len() as u64,
        container_bytes: fs::metadata(output)
            .map_err(|error| format!("Cannot inspect created archive: {error}"))?
            .len(),
    })
}

fn add_file(
    source: &Path,
    archive_path: String,
    payload: &mut Vec<u8>,
    entries: &mut Vec<ManifestEntry>,
    deduplicated: &mut HashMap<String, StoredBlob>,
    total_original_bytes: &mut u64,
) -> Result<(), String> {
    validate_archive_path(&archive_path)?;
    let data = fs::read(source)
        .map_err(|error| format!("Cannot read {}: {error}", source.display()))?;
    let original_size = data.len() as u64;

    if original_size > MAX_ENTRY_BYTES {
        return Err(format!(
            "{} exceeds the UDRV v1 per-file size limit.",
            source.display()
        ));
    }

    *total_original_bytes = total_original_bytes
        .checked_add(original_size)
        .ok_or_else(|| "Original source size overflow.".to_owned())?;

    let content_hash = blake3::hash(&data).to_hex().to_string();
    let blob = if let Some(existing) = deduplicated.get(&content_hash) {
        if existing.stored_size == 0 && original_size != 0 {
            return Err("Conflicting content-hash metadata.".to_owned());
        }
        existing.clone()
    } else {
        let compressed = zstd::bulk::compress(&data, 5)
            .map_err(|error| format!("Zstandard compression failed: {error}"))?;
        let (stored, codec) = if compressed.len() < data.len() {
            (compressed, StorageCodec::Zstd)
        } else {
            (data.clone(), StorageCodec::Raw)
        };

        let new_payload_size = (payload.len() as u64)
            .checked_add(stored.len() as u64)
            .ok_or_else(|| "UDRV payload size overflow.".to_owned())?;
        if new_payload_size > MAX_PAYLOAD_BYTES {
            return Err("The UDRV payload exceeds the v1 size limit.".to_owned());
        }

        let blob = StoredBlob {
            offset: payload.len() as u64,
            stored_size: stored.len() as u64,
            codec,
        };
        payload.extend_from_slice(&stored);
        deduplicated.insert(content_hash.clone(), blob.clone());
        blob
    };

    entries.push(ManifestEntry {
        path: archive_path,
        offset: blob.offset,
        stored_size: blob.stored_size,
        original_size,
        codec: blob.codec,
        blake3: content_hash,
    });
    Ok(())
}

fn validate_archive_path(path: &str) -> Result<(), String> {
    if path.is_empty() || path.starts_with('/') || path.contains('\\') {
        return Err(format!("Unsafe archive path: {path}"));
    }
    if path.split('/').any(|part| part.is_empty() || part == "." || part == "..") {
        return Err(format!("Unsafe archive path: {path}"));
    }
    Ok(())
}

fn write_atomically(
    output: &Path,
    header: &[u8],
    manifest: &[u8],
    payload: &[u8],
) -> Result<(), String> {
    if let Some(parent) = output.parent().filter(|path| !path.as_os_str().is_empty()) {
        fs::create_dir_all(parent)
            .map_err(|error| format!("Cannot create output directory: {error}"))?;
    }

    let parent = output
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let file_name = output
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_else(|| "archive.udrv".to_owned());
    let nonce = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let temporary = parent.join(format!(
        ".{file_name}.{}.{nonce}.tmp",
        std::process::id()
    ));

    let write_result = (|| -> Result<(), String> {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary)
            .map_err(|error| format!("Cannot create temporary archive: {error}"))?;
        file.write_all(header)
            .and_then(|_| file.write_all(manifest))
            .and_then(|_| file.write_all(payload))
            .map_err(|error| format!("Cannot write archive: {error}"))?;
        file.sync_all()
            .map_err(|error| format!("Cannot flush archive to disk: {error}"))?;
        drop(file);

        if output.exists() {
            fs::remove_file(output)
                .map_err(|error| format!("Cannot replace existing archive: {error}"))?;
        }
        fs::rename(&temporary, output)
            .map_err(|error| format!("Cannot finalize archive: {error}"))?;
        Ok(())
    })();

    if write_result.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    write_result
}

/// Verify the header, container digest, manifest bounds, decompression and
/// per-entry BLAKE3 hashes. No packaged file is executed or installed.
pub fn verify_archive(path: &Path) -> Result<BundleSummary, String> {
    let file_size = fs::metadata(path)
        .map_err(|error| format!("Cannot inspect {}: {error}", path.display()))?
        .len();
    let max_size = MAX_PAYLOAD_BYTES + MAX_MANIFEST_BYTES as u64 + HEADER_LEN as u64;
    if file_size > max_size {
        return Err("Archive exceeds the UDRV v1 size limit.".to_owned());
    }

    let bytes = fs::read(path)
        .map_err(|error| format!("Cannot read {}: {error}", path.display()))?;
    if bytes.len() < HEADER_LEN {
        return Err("File is too small to be a UDRV container.".to_owned());
    }
    if &bytes[0..8] != MAGIC {
        return Err("Invalid UDRV magic signature.".to_owned());
    }

    let version = u32::from_le_bytes(bytes[8..12].try_into().expect("fixed header slice"));
    if version != FORMAT_VERSION {
        return Err(format!("Unsupported UDRV container version: {version}."));
    }

    let manifest_len =
        u32::from_le_bytes(bytes[12..16].try_into().expect("fixed header slice")) as usize;
    let payload_len_u64 =
        u64::from_le_bytes(bytes[16..24].try_into().expect("fixed header slice"));
    let payload_len = usize::try_from(payload_len_u64)
        .map_err(|_| "Archive payload does not fit this platform.".to_owned())?;

    if manifest_len > MAX_MANIFEST_BYTES || payload_len_u64 > MAX_PAYLOAD_BYTES {
        return Err("Archive declares sizes above the UDRV v1 limits.".to_owned());
    }

    let expected_len = HEADER_LEN
        .checked_add(manifest_len)
        .and_then(|value| value.checked_add(payload_len))
        .ok_or_else(|| "Archive length overflow.".to_owned())?;
    if expected_len != bytes.len() {
        return Err("Archive length does not match its header.".to_owned());
    }

    let manifest_start = HEADER_LEN;
    let payload_start = manifest_start + manifest_len;
    let manifest_bytes = &bytes[manifest_start..payload_start];
    let payload = &bytes[payload_start..];

    let mut hasher = blake3::Hasher::new();
    hasher.update(manifest_bytes);
    hasher.update(payload);
    if hasher.finalize().as_bytes() != &bytes[24..56] {
        return Err("Container BLAKE3 digest mismatch.".to_owned());
    }

    let manifest: Manifest = serde_json::from_slice(manifest_bytes)
        .map_err(|error| format!("Invalid UDRV manifest: {error}"))?;
    if manifest.format != "DUCK-OMNI" || manifest.format_version != FORMAT_VERSION {
        return Err("Manifest format/version mismatch.".to_owned());
    }
    if manifest.entry_count as usize != manifest.entries.len() {
        return Err("Manifest entry count is inconsistent.".to_owned());
    }

    let mut seen_paths = HashSet::new();
    let mut unique_blobs = HashSet::new();
    let mut original_bytes = 0_u64;

    for entry in &manifest.entries {
        validate_archive_path(&entry.path)?;
        if !seen_paths.insert(entry.path.clone()) {
            return Err(format!("Duplicate archive path: {}", entry.path));
        }
        if entry.original_size > MAX_ENTRY_BYTES {
            return Err(format!("Entry exceeds the size limit: {}", entry.path));
        }

        let start = usize::try_from(entry.offset)
            .map_err(|_| "Entry offset does not fit this platform.".to_owned())?;
        let stored_size = usize::try_from(entry.stored_size)
            .map_err(|_| "Entry size does not fit this platform.".to_owned())?;
        let end = start
            .checked_add(stored_size)
            .ok_or_else(|| "Entry range overflow.".to_owned())?;
        if end > payload.len() {
            return Err(format!("Entry points outside payload: {}", entry.path));
        }

        let stored = &payload[start..end];
        let decoded = match entry.codec {
            StorageCodec::Raw => stored.to_vec(),
            StorageCodec::Zstd => {
                let decoded_limit = usize::try_from(entry.original_size)
                    .map_err(|_| "Entry size does not fit this platform.".to_owned())?;
                zstd::bulk::decompress(stored, decoded_limit)
                    .map_err(|error| format!("Cannot decompress {}: {error}", entry.path))?
            }
        };

        if decoded.len() as u64 != entry.original_size {
            return Err(format!("Unpacked size mismatch: {}", entry.path));
        }
        if blake3::hash(&decoded).to_hex().as_str() != entry.blake3 {
            return Err(format!("Entry BLAKE3 mismatch: {}", entry.path));
        }

        original_bytes = original_bytes
            .checked_add(entry.original_size)
            .ok_or_else(|| "Original size overflow.".to_owned())?;
        unique_blobs.insert((entry.offset, entry.stored_size, entry.blake3.clone()));
    }

    Ok(BundleSummary {
        entry_count: manifest.entries.len(),
        unique_blobs: unique_blobs.len(),
        original_bytes,
        stored_bytes: payload.len() as u64,
        container_bytes: bytes.len() as u64,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn builds_verifies_and_deduplicates_identical_files() {
        let directory = tempfile::tempdir().expect("temporary directory");
        let first = directory.path().join("first.inf");
        let second = directory.path().join("second.inf");
        let archive = directory.path().join("test.udrv");
        let contents = b"[Version]\nSignature=\"$Windows NT$\"\n";
        fs::write(&first, contents).expect("write first source");
        fs::write(&second, contents).expect("write second source");

        let summary = build_archive(
            &[first, second],
            &archive,
            "OPlague test bundle",
        )
        .expect("build archive");

        assert_eq!(summary.entry_count, 2);
        assert_eq!(summary.unique_blobs, 1);
        assert!(summary.stored_bytes < summary.original_bytes);

        let verified = verify_archive(&archive).expect("verify archive");
        assert_eq!(verified.entry_count, 2);
        assert_eq!(verified.unique_blobs, 1);
    }

    #[test]
    fn rejects_corrupted_container_payload() {
        let directory = tempfile::tempdir().expect("temporary directory");
        let source = directory.path().join("driver.inf");
        let archive = directory.path().join("corrupt.udrv");
        fs::write(&source, b"driver metadata").expect("write source");
        build_archive(&[source], &archive, "corruption test").expect("build archive");

        let mut bytes = fs::read(&archive).expect("read archive");
        let last = bytes.len() - 1;
        bytes[last] ^= 0x5A;
        fs::write(&archive, bytes).expect("corrupt archive");

        assert!(verify_archive(&archive).is_err());
    }

    #[test]
    fn rejects_path_traversal_entries() {
        assert!(validate_archive_path("../outside.sys").is_err());
        assert!(validate_archive_path("source_001/../../outside.sys").is_err());
        assert!(validate_archive_path("source_001/drivers/audio.inf").is_ok());
    }
}
