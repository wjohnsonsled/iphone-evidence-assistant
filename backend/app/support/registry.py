"""Fail-closed supported parser registry and output quarantine gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Iterable
from uuid import UUID, uuid4

from app.support.domain import ProcessingResultStatus, SUPPORTED_SUCCESS_STATUSES


class ParserDisposition(str, Enum):
    APPROVED = "APPROVED"
    CANDIDATE = "CANDIDATE"
    LEGACY = "LEGACY"
    COMPATIBILITY = "COMPATIBILITY"
    EXPERIMENTAL = "EXPERIMENTAL"
    EXCLUDED = "EXCLUDED"
    UNKNOWN = "UNKNOWN"


class CurrentSupportStatus(str, Enum):
    """Registry-admissible current state; non-Supported states stay outside."""

    SUPPORTED = "SUPPORTED"


class ParserQuarantinedError(RuntimeError):
    """Structured denial that never exposes parser or evidence content."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _required(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}_required")
    return value.strip()


@dataclass(frozen=True, slots=True)
class ApprovedParserEntry:
    artifact_id: str
    artifact_family: str
    parser_id: str
    parser_version: str
    schema_profiles: tuple[str, ...]
    owner_decision_id: str
    validation_package_id: str
    acceptance_record_ids: tuple[str, ...]
    promotion_date: date
    current_support_status: CurrentSupportStatus
    retirement_date: date | None = None

    def __post_init__(self) -> None:
        for field in (
            "artifact_id",
            "artifact_family",
            "parser_id",
            "parser_version",
            "owner_decision_id",
            "validation_package_id",
        ):
            object.__setattr__(self, field, _required(getattr(self, field), field))
        profiles = tuple(sorted({_required(item, "schema_profile") for item in self.schema_profiles}))
        if not profiles:
            raise ValueError("schema_profiles_required")
        object.__setattr__(self, "schema_profiles", profiles)
        records = tuple(sorted({_required(item, "acceptance_record_id") for item in self.acceptance_record_ids}))
        if not records:
            raise ValueError("acceptance_record_ids_required")
        object.__setattr__(self, "acceptance_record_ids", records)
        if self.current_support_status is not CurrentSupportStatus.SUPPORTED:
            raise ValueError("current_support_status_must_be_supported")
        if self.retirement_date is not None and self.retirement_date < self.promotion_date:
            raise ValueError("retirement_precedes_promotion_date")

    @property
    def identity(self) -> tuple[str, str, str]:
        return self.artifact_id, self.parser_id, self.parser_version


@dataclass(frozen=True, slots=True)
class ParserAuthorization:
    registry_instance_id: UUID
    registry_version: str
    entry: ApprovedParserEntry
    schema_profile: str


@dataclass(frozen=True, slots=True)
class OutputAdmission:
    status: ProcessingResultStatus
    records: tuple[dict[str, Any], ...]
    authorization: ParserAuthorization


class SupportedParserRegistry:
    """Explicit registry that issues authorization only for exact approved entries."""

    def __init__(
        self,
        version: str,
        entries: Iterable[ApprovedParserEntry] = (),
        *,
        instance_id: UUID | None = None,
    ) -> None:
        self.version = _required(version, "registry_version")
        self._instance_id = instance_id or uuid4()
        indexed: dict[tuple[str, str, str], ApprovedParserEntry] = {}
        for entry in entries:
            if entry.identity in indexed:
                raise ValueError("duplicate_registry_entry")
            indexed[entry.identity] = entry
        self._entries = indexed

    @property
    def entries(self) -> tuple[ApprovedParserEntry, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))

    def authorize(
        self,
        *,
        artifact_id: str,
        parser_id: str,
        parser_version: str,
        schema_profile: str,
        disposition: ParserDisposition,
        on_date: date,
    ) -> ParserAuthorization:
        if disposition is not ParserDisposition.APPROVED:
            raise ParserQuarantinedError(f"parser_disposition_{disposition.value.lower()}")
        entry = self._entries.get((artifact_id, parser_id, parser_version))
        if entry is None:
            raise ParserQuarantinedError("parser_not_in_supported_registry")
        if schema_profile not in entry.schema_profiles:
            raise ParserQuarantinedError("schema_profile_not_approved")
        if on_date < entry.promotion_date:
            raise ParserQuarantinedError("approval_not_effective")
        if entry.retirement_date is not None and on_date > entry.retirement_date:
            raise ParserQuarantinedError("approval_retired")
        return ParserAuthorization(self._instance_id, self.version, entry, schema_profile)

    def issued(self, authorization: ParserAuthorization) -> bool:
        return (
            authorization.registry_instance_id == self._instance_id
            and authorization.registry_version == self.version
            and self._entries.get(authorization.entry.identity) == authorization.entry
            and authorization.schema_profile in authorization.entry.schema_profiles
        )


class SupportedOutputGate:
    def __init__(self, registry: SupportedParserRegistry) -> None:
        self._registry = registry

    def admit(
        self,
        authorization: ParserAuthorization,
        *,
        status: ProcessingResultStatus,
        records: Iterable[dict[str, Any]],
        records_examined: int,
        records_emitted: int,
        records_excluded: int,
        records_rejected: int,
        records_failed: int,
        records_indeterminate: int,
        provenance_complete: bool,
    ) -> OutputAdmission:
        materialized = tuple(records)
        if not self._registry.issued(authorization):
            raise ParserQuarantinedError("authorization_not_issued_by_registry")
        if status not in SUPPORTED_SUCCESS_STATUSES:
            raise ParserQuarantinedError("processing_status_not_supported_success")
        if not provenance_complete:
            raise ParserQuarantinedError("provenance_incomplete")
        total = records_emitted + records_excluded + records_rejected + records_failed + records_indeterminate
        if records_examined != total or records_emitted != len(materialized):
            raise ParserQuarantinedError("coverage_not_reconciled")
        if status is ProcessingResultStatus.SUPPORTED_NO_RECORDS:
            if records_examined != 0 or materialized:
                raise ParserQuarantinedError("no_records_status_contains_records")
        elif not materialized:
            raise ParserQuarantinedError("complete_status_contains_no_records")
        return OutputAdmission(status, materialized, authorization)


def create_supported_registry() -> SupportedParserRegistry:
    """Production composition root: intentionally empty pending owner promotion."""

    return SupportedParserRegistry("supported-registry-v0-empty")
