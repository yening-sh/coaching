from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from database import get_db
from models.user import User
from models.record import Record
from models.mistake import Mistake
from core.security import get_current_user

router = APIRouter(prefix="/mistakes", tags=["错题集"])


class AddMistakeRequest(BaseModel):
    record_id: str


@router.post("")
def add_mistake(
    req: AddMistakeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Record).filter(
        Record.id == req.record_id,
        Record.student_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 避免重复添加
    existing = db.query(Mistake).filter(Mistake.record_id == req.record_id).first()
    if existing:
        return {"mistake_id": existing.id, "message": "已在错题集中"}

    parsed = json.loads(record.ai_feedback) if record.ai_feedback else {}
    if isinstance(parsed, list):
        note = " | ".join(item.get("feedback", "") for item in parsed if not item.get("is_correct", True))
    else:
        note = parsed.get("feedback", "")
    output_schema = "translation" if isinstance(parsed, list) else "math"
    mistake = Mistake(
        student_id=current_user.id,
        record_id=record.id,
        subject=record.subject,
        note=note,
        image_url=record.image_url,
        ai_feedback=record.ai_feedback,
        output_schema=output_schema,
    )
    db.add(mistake)
    db.commit()
    db.refresh(mistake)

    return {"mistake_id": mistake.id}


@router.get("")
def list_mistakes(
    subject: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Mistake).filter(Mistake.student_id == current_user.id)
    if subject:
        query = query.filter(Mistake.subject == subject)
    if status:
        query = query.filter(Mistake.status == status)

    total = query.count()
    items = query.order_by(Mistake.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": m.id,
                "subject": m.subject,
                "note": m.note,
                "status": m.status,
                "retry_count": m.retry_count,
                "image_url": m.image_url,
                "record_id": m.record_id,
                "ai_feedback": m.ai_feedback,
                "output_schema": m.output_schema or "simple",
                "created_at": m.created_at.isoformat(),
            }
            for m in items
        ],
    }


@router.patch("/{mistake_id}")
def update_mistake(
    mistake_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.student_id == current_user.id,
    ).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="不存在")

    if status == "mastered":
        from datetime import datetime
        mistake.status = "mastered"
        mistake.mastered_at = datetime.utcnow()
    elif status == "pending":
        mistake.status = "pending"
        mistake.retry_count += 1

    db.commit()
    return {"message": "已更新"}
