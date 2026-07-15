"""Case processing orchestration and evidence-engine integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApiError
from app.models.case import utcnow
from app.repositories.cases import CaseRepository
from app.repositories.devices import DeviceRepository
from app.repositories.jobs import JobRepository
from app.services.evidence_persistence import EvidenceEngineResult, EvidencePersistenceService

logger = logging.getLogger(__name__)


class LocalBackupPathValidator:
    """Validate server-local backup paths against configured evidence roots."""

    def __init__(self, roots: list[Path]) -> None:
        self.roots = [root.resolve() for root in roots]

    def validate(self, backup_path: str) -> Path:
        """Return resolved path or raise a structured API error."""

        try:
            candidate = Path(backup_path).expanduser().resolve()
        except RuntimeError as exc:
            raise ApiError(400, "invalid_backup_path", "Backup path could not be resolved.") from exc
        if not any(_is_relative_to(candidate, root) for root in self.roots):
            raise ApiError(400, "backup_path_outside_evidence_root", "Backup path is outside configured evidence roots.")
        if not candidate.exists():
            raise ApiError(404, "backup_path_not_found", "Backup path was not found.")
        if not candidate.is_dir():
            raise ApiError(400, "backup_path_not_directory", "Backup path must be a directory.")
        if not appears_supported_backup(candidate):
            raise ApiError(400, "unsupported_backup_structure", "Path does not appear to be a supported iPhone backup.")
        return candidate


def appears_supported_backup(path: Path) -> bool:
    """Return whether a directory resembles a supported decrypted backup/case."""

    markers = [
        path / "Manifest.db",
        path / "Info.plist",
        path / "decrypted",
        path / "HomeDomain",
        path / "Library" / "SMS" / "sms.db",
        path / "decrypted" / "HomeDomain",
        path / "decrypted" / "HomeDomain" / "Library" / "SMS" / "sms.db",
    ]
    return any(marker.exists() for marker in markers)


class EvidenceEngineRunner:
    """Run the refactored evidence engine and return domain results."""

    def run(self, backup_path: Path) -> EvidenceEngineResult:
        """Run the evidence engine against a local decrypted backup path."""

        from evidence_engine._legacy import (
            CaseContext,
            apply_confidence,
            build_case_knowledge,
            build_correlation_clusters,
            dedupe_events,
            extract_device_metadata,
            link_message_attachments,
            parse_dt,
            plugins,
        )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        ctx = CaseContext(backup_path, parse_dt("1970-01-01 00:00:00"), now, context_minutes=0)
        all_events = []
        for plugin in plugins():
            before = len(all_events)
            all_events.extend(plugin.safe_collect(ctx))
            ctx.plugin_stats[plugin.name] = {"events": len(all_events) - before}
        all_events = dedupe_events(all_events)
        apply_confidence(all_events)
        link_message_attachments(all_events)
        clusters = build_correlation_clusters(ctx, all_events)
        case_knowledge = build_case_knowledge(ctx, all_events, clusters, ctx.coverage_records, ctx.app_coverage_records, [])
        return EvidenceEngineResult(
            events=all_events,
            normalized_events=case_knowledge.get("events", []),
            coverage_records=ctx.coverage_records,
            app_coverage_records=ctx.app_coverage_records,
            warnings=[],
            errors=[record.get("message", str(record)) for record in ctx.errors.records],
            device_metadata=extract_device_metadata(ctx),
            statistics={"event_count": len(all_events), "plugin_stats": ctx.plugin_stats},
        )


class CaseProcessingService:
    """Synchronous MVP processor designed for later background execution."""

    def __init__(
        self,
        settings: Settings,
        case_repo: CaseRepository | None = None,
        device_repo: DeviceRepository | None = None,
        job_repo: JobRepository | None = None,
        runner: EvidenceEngineRunner | None = None,
        persistence: EvidencePersistenceService | None = None,
    ) -> None:
        self.settings = settings
        self.case_repo = case_repo or CaseRepository()
        self.device_repo = device_repo or DeviceRepository()
        self.job_repo = job_repo or JobRepository()
        self.runner = runner or EvidenceEngineRunner()
        self.persistence = persistence or EvidencePersistenceService()
        self.path_validator = LocalBackupPathValidator(settings.evidence_roots)

    def process_local_backup(self, session: Session, case_id: UUID, backup_path: str):
        """Validate, process, persist, and update job/case status."""

        case = self.case_repo.get(session, case_id)
        if not case:
            raise ApiError(404, "case_not_found", "Case was not found.")
        if self.job_repo.active_for_case(session, case_id):
            raise ApiError(409, "processing_already_in_progress", "Processing is already in progress for this case.")
        resolved_path = self.path_validator.validate(backup_path)
        job = self.job_repo.create(session, case_id, status="running", stage="validating")
        case.status = "processing"
        session.commit()

        logger.info("processing_start case_id=%s job_id=%s", case_id, job.id)
        try:
            job.stage = "extracting"
            job.started_at = utcnow()
            session.commit()
            result = self.runner.run(resolved_path)
            device = self.device_repo.first_for_case(session, case_id)
            if device is None:
                device = self.device_repo.create(session, case_id, metadata_json=result.device_metadata)
            job.stage = "persisting"
            session.flush()
            stats = self.persistence.persist_result(session, case_id, device.id, result)
            case.status = "completed_with_warnings" if result.errors or result.warnings else "completed"
            case.processed_at = utcnow()
            job.status = "completed"
            job.stage = "completed"
            job.progress_percent = 100
            job.completed_at = utcnow()
            job.warnings_json = result.warnings
            job.statistics_json = {**result.statistics, **stats.as_dict()}
            session.commit()
            logger.info(
                "processing_complete case_id=%s job_id=%s events=%s coverage=%s",
                case_id,
                job.id,
                stats.inserted_events,
                stats.inserted_coverage_records,
            )
            return job
        except Exception as exc:
            session.rollback()
            case = self.case_repo.get(session, case_id)
            job = session.get(type(job), job.id)
            if case:
                case.status = "failed"
            if job:
                job.status = "failed"
                job.stage = "failed"
                job.error_message = "Evidence processing failed."
                job.completed_at = utcnow()
            session.commit()
            logger.exception("processing_failure case_id=%s job_id=%s", case_id, getattr(job, "id", None))
            raise ApiError(500, "evidence_engine_failure", "Evidence processing failed.") from exc


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
