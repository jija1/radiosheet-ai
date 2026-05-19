from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ai import compliance_validator, conflict_detector
from app.api.v1.runsheet.models import RunSheetRecord
from app.api.v1.runsheet.schemas import (
    Conflict,
    FixResponse,
    ProgrammeInput,
    Segment,
)
from app.core.exceptions import NotFoundException
from app.models.audit_log import log_action


async def detect(
    segments: list[Segment],
    programme_input: ProgrammeInput,
) -> list[Conflict]:
    return conflict_detector.detect_conflicts(segments, programme_input)


async def apply_fix(
    runsheet_id: str,
    conflict_id: str,
    db: Session,
) -> FixResponse:
    record = db.query(RunSheetRecord).filter(RunSheetRecord.id == runsheet_id).first()
    if not record:
        raise NotFoundException(f"Run-sheet '{runsheet_id}' not found")

    segments = [Segment(**s) for s in json.loads(record.segments_json)]
    conflicts = [Conflict(**c) for c in json.loads(record.conflicts_json)]
    programme_input = ProgrammeInput(**json.loads(record.programme_input_json))

    # conflict_id is the rule_id (C001–C005); apply the first matching conflict
    target = next((c for c in conflicts if c.rule_id == conflict_id), None)
    if not target:
        raise NotFoundException(
            f"Conflict '{conflict_id}' not found in run-sheet '{runsheet_id}'"
        )

    updated_segments = conflict_detector.apply_fix(segments, target, programme_input)
    remaining_conflicts = conflict_detector.detect_conflicts(updated_segments, programme_input)
    comp = compliance_validator.validate_compliance(updated_segments, programme_input)

    # Persist updated state
    record.segments_json  = json.dumps([s.model_dump(mode="json") for s in updated_segments])
    record.conflicts_json = json.dumps([c.model_dump(mode="json") for c in remaining_conflicts])
    db.commit()
    log_action(db, record.user_id, "fix_applied",
               f"rule={conflict_id}, runsheet={runsheet_id}")

    return FixResponse(
        updated_segments=updated_segments,
        remaining_conflicts=remaining_conflicts,
        compliance_score=comp.compliance_score,
        compliance_risk=comp.compliance_risk,
        compliance_violations=comp.compliance_violations,
    )
