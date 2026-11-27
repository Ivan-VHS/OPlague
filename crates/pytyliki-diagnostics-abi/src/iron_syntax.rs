//! Read-only provenance validation for Pytyliki Iron Syntax AST records.
//!
//! This module deliberately validates metadata only. It does not parse Iron
//! source, execute records, authorize device operations, or change diagnostics
//! ABI layout.

pub const IRON_SYNTAX_SCHEMA_V1: &str = "pytyliki.iron-syntax-ast.v1";
pub const IRON_SYNTAX_VERSION_V1: &str = "1.0.0";
pub const IRON_SYNTAX_OWNER: &str = "Pytyliki";
pub const IRON_SYNTAX_RECORD_COUNT: u8 = 20;
pub const IRON_SYNTAX_MAX_RECORDS: u32 = 4096;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct IronSyntaxEnvelopeV1<'a> {
    pub schema: &'a str,
    pub version: &'a str,
    pub canonical_owner: &'a str,
    pub execution_performed: bool,
    pub record_count: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct IronSyntaxRecordV1 {
    pub record_id: u8,
    pub record_index: u32,
    pub source_offset: u64,
    pub source_length: u64,
    pub line: u32,
    pub column: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum IronSyntaxMetadataError {
    UnsupportedSchema,
    UnsupportedVersion,
    InvalidCanonicalOwner,
    ExecutionNotAllowed,
    EmptyDocument,
    RecordLimitExceeded,
    InvalidRecordId,
    RecordIndexOutOfRange,
    EmptySourceSpan,
    SourceSpanOverflow,
    InvalidLine,
    InvalidColumn,
    SourceOrderViolation,
    LineOrderViolation,
}

/// Validate a syntax-only AST envelope and one record's provenance.
///
/// `previous_end` and `previous_line` should be the end offset and line
/// number of the preceding record in source order. Pass `None` for the first
/// record. This keeps source provenance deterministic across consumers.
pub fn validate_record(
    envelope: IronSyntaxEnvelopeV1<'_>,
    record: IronSyntaxRecordV1,
    previous_end: Option<u64>,
    previous_line: Option<u32>,
) -> Result<(), IronSyntaxMetadataError> {
    if envelope.schema != IRON_SYNTAX_SCHEMA_V1 {
        return Err(IronSyntaxMetadataError::UnsupportedSchema);
    }
    if envelope.version != IRON_SYNTAX_VERSION_V1 {
        return Err(IronSyntaxMetadataError::UnsupportedVersion);
    }
    if envelope.canonical_owner != IRON_SYNTAX_OWNER {
        return Err(IronSyntaxMetadataError::InvalidCanonicalOwner);
    }
    if envelope.execution_performed {
        return Err(IronSyntaxMetadataError::ExecutionNotAllowed);
    }
    if envelope.record_count == 0 {
        return Err(IronSyntaxMetadataError::EmptyDocument);
    }
    if envelope.record_count > IRON_SYNTAX_MAX_RECORDS {
        return Err(IronSyntaxMetadataError::RecordLimitExceeded);
    }
    if record.record_id >= IRON_SYNTAX_RECORD_COUNT {
        return Err(IronSyntaxMetadataError::InvalidRecordId);
    }
    if record.record_index >= envelope.record_count {
        return Err(IronSyntaxMetadataError::RecordIndexOutOfRange);
    }
    if record.source_length == 0 {
        return Err(IronSyntaxMetadataError::EmptySourceSpan);
    }
    let end = record
        .source_offset
        .checked_add(record.source_length)
        .ok_or(IronSyntaxMetadataError::SourceSpanOverflow)?;
    if record.line == 0 {
        return Err(IronSyntaxMetadataError::InvalidLine);
    }
    if record.column == 0 {
        return Err(IronSyntaxMetadataError::InvalidColumn);
    }
    if previous_end.is_some_and(|end_before| record.source_offset < end_before) {
        return Err(IronSyntaxMetadataError::SourceOrderViolation);
    }
    if previous_line.is_some_and(|line_before| record.line < line_before) {
        return Err(IronSyntaxMetadataError::LineOrderViolation);
    }
    let _ = end;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn envelope(record_count: u32) -> IronSyntaxEnvelopeV1<'static> {
        IronSyntaxEnvelopeV1 {
            schema: IRON_SYNTAX_SCHEMA_V1,
            version: IRON_SYNTAX_VERSION_V1,
            canonical_owner: IRON_SYNTAX_OWNER,
            execution_performed: false,
            record_count,
        }
    }

    fn record(record_id: u8) -> IronSyntaxRecordV1 {
        IronSyntaxRecordV1 {
            record_id,
            record_index: 0,
            source_offset: 0,
            source_length: 12,
            line: 1,
            column: 1,
        }
    }

    #[test]
    fn accepts_all_twenty_record_identifiers() {
        let metadata = envelope(u32::from(IRON_SYNTAX_RECORD_COUNT));
        for id in 0..IRON_SYNTAX_RECORD_COUNT {
            let mut item = record(id);
            item.record_index = u32::from(id);
            item.source_offset = u64::from(id) * 16;
            assert_eq!(validate_record(metadata, item, None, None), Ok(()));
        }
    }

    #[test]
    fn rejects_unknown_schema_version_and_owner() {
        let valid = envelope(1);
        let mut bad_schema = valid;
        bad_schema.schema = "pytyliki.iron-syntax-ast.v2";
        assert_eq!(
            validate_record(bad_schema, record(0), None, None),
            Err(IronSyntaxMetadataError::UnsupportedSchema)
        );

        let mut bad_version = valid;
        bad_version.version = "2.0.0";
        assert_eq!(
            validate_record(bad_version, record(0), None, None),
            Err(IronSyntaxMetadataError::UnsupportedVersion)
        );

        let mut bad_owner = valid;
        bad_owner.canonical_owner = "OPlague";
        assert_eq!(
            validate_record(bad_owner, record(0), None, None),
            Err(IronSyntaxMetadataError::InvalidCanonicalOwner)
        );
    }

    #[test]
    fn rejects_execution_and_empty_or_oversized_documents() {
        let mut executed = envelope(1);
        executed.execution_performed = true;
        assert_eq!(
            validate_record(executed, record(0), None, None),
            Err(IronSyntaxMetadataError::ExecutionNotAllowed)
        );
        assert_eq!(
            validate_record(envelope(0), record(0), None, None),
            Err(IronSyntaxMetadataError::EmptyDocument)
        );
        assert_eq!(
            validate_record(envelope(IRON_SYNTAX_MAX_RECORDS + 1), record(0), None, None),
            Err(IronSyntaxMetadataError::RecordLimitExceeded)
        );
    }

    #[test]
    fn rejects_out_of_range_ids_and_indices() {
        assert_eq!(
            validate_record(envelope(1), record(IRON_SYNTAX_RECORD_COUNT), None, None),
            Err(IronSyntaxMetadataError::InvalidRecordId)
        );
        let mut bad_index = record(0);
        bad_index.record_index = 1;
        assert_eq!(
            validate_record(envelope(1), bad_index, None, None),
            Err(IronSyntaxMetadataError::RecordIndexOutOfRange)
        );
    }

    #[test]
    fn validates_spans_and_source_locations() {
        let mut item = record(0);
        item.source_length = 0;
        assert_eq!(
            validate_record(envelope(1), item, None, None),
            Err(IronSyntaxMetadataError::EmptySourceSpan)
        );

        let mut item = record(0);
        item.source_offset = u64::MAX;
        item.source_length = 2;
        assert_eq!(
            validate_record(envelope(1), item, None, None),
            Err(IronSyntaxMetadataError::SourceSpanOverflow)
        );

        let mut item = record(0);
        item.line = 0;
        assert_eq!(
            validate_record(envelope(1), item, None, None),
            Err(IronSyntaxMetadataError::InvalidLine)
        );

        let mut item = record(0);
        item.column = 0;
        assert_eq!(
            validate_record(envelope(1), item, None, None),
            Err(IronSyntaxMetadataError::InvalidColumn)
        );
    }

    #[test]
    fn enforces_monotonic_source_order() {
        let item = record(1);
        assert_eq!(
            validate_record(envelope(2), item, Some(13), Some(1)),
            Err(IronSyntaxMetadataError::SourceOrderViolation)
        );
        assert_eq!(
            validate_record(envelope(2), item, Some(0), Some(2)),
            Err(IronSyntaxMetadataError::LineOrderViolation)
        );
    }
}
