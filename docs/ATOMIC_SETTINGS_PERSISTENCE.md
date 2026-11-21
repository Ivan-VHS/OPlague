# Atomic UI Settings Persistence

OPlague theme preferences are stored as a small versioned JSON document.

The writer validates the selected mode, creates a temporary file in the destination directory, writes and flushes complete JSON, calls fsync on the file, then replaces the destination with os.replace. Keeping both paths in one directory avoids a cross-filesystem move and gives readers an old-or-new file boundary rather than a partially written document.

Persistence remains best-effort: inability to save a preference does not prevent the read-only workbench from starting. A failed replacement leaves the previous settings document intact, and temporary files are cleaned up when possible.

This mechanism is for non-critical UI preferences only. It is not a transaction system for driver operations, device state, or security-sensitive records.