from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from models.user import User
from models.subscription import Subscription
from models.exercise_type import ExerciseType
from core.security import get_current_user

router = APIRouter(prefix="/subjects", tags=["学科"])

SUBJECT_META = {
    "math":      {"name": "数学", "icon": "📐"},
    "chinese":   {"name": "语文", "icon": "📗"},
    "english":   {"name": "英语", "icon": "📖"},
    "physics":   {"name": "物理", "icon": "🔬"},
    "chemistry": {"name": "化学", "icon": "⚗️"},
    "biology":   {"name": "生物", "icon": "🧬"},
}


@router.get("/my")
def get_my_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()

    # 有效订阅
    active_subs = db.query(Subscription).filter(
        Subscription.student_id == current_user.id,
        Subscription.is_active == True,
        Subscription.end_date >= today,
    ).all()

    subscribed_subjects = {s.subject for s in active_subs}

    subscribed = []
    for sub in active_subs:
        meta = SUBJECT_META.get(sub.subject, {"name": sub.subject, "icon": "📚"})

        # 本月批改数
        from models.record import Record
        from sqlalchemy import func
        first_day = today.replace(day=1)
        month_total = db.query(func.count(Record.id)).filter(
            Record.student_id == current_user.id,
            Record.subject == sub.subject,
            Record.created_at >= first_day,
        ).scalar()

        subscribed.append({
            "subject": sub.subject,
            "name": meta["name"],
            "icon": meta["icon"],
            "grade_level": sub.grade_level,
            "end_date": sub.end_date.isoformat(),
            "month_total": month_total,
        })

    unsubscribed = [
        {"subject": k, "name": v["name"], "icon": v["icon"]}
        for k, v in SUBJECT_META.items()
        if k not in subscribed_subjects
    ]

    return {"subscribed": subscribed, "unsubscribed": unsubscribed}


@router.get("/exercise-types")
def get_exercise_types(
    subject: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回指定科目的所有有效题型，供学生选择"""
    types = db.query(ExerciseType).filter(
        ExerciseType.subject == subject,
        ExerciseType.is_active == True,
    ).order_by(ExerciseType.sort_order).all()
    return [{"id": t.id, "name": t.name, "output_schema": t.output_schema} for t in types]
