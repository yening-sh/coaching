from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List
from sqlalchemy.orm import Session
from datetime import date
import json

from database import get_db
from models.user import User
from models.subscription import Subscription
from models.record import Record
from models.exercise_type import ExerciseType
from core.security import get_current_user
from services import ai_client, storage

router = APIRouter(prefix="/records", tags=["批改记录"])


def check_subscription(db: Session, student_id: str, subject: str) -> Subscription:
    """检查学生是否有有效的科目订阅"""
    sub = db.query(Subscription).filter(
        Subscription.student_id == student_id,
        Subscription.subject == subject,
        Subscription.is_active == True,
        Subscription.end_date >= date.today(),
    ).first()
    if not sub:
        raise HTTPException(status_code=403, detail=f"未开通该科目，请联系管理员")
    return sub


@router.post("/submit")
async def submit(
    subject: str = Form(...),
    files: List[UploadFile] = File(...),
    exercise_type_id: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="请上传至少一张图片")
    if len(files) > 4:
        raise HTTPException(status_code=400, detail="最多上传4张图片")

    sub = check_subscription(db, current_user.id, subject)

    # 解析题型
    exercise_type = None
    if exercise_type_id:
        exercise_type = db.query(ExerciseType).filter(ExerciseType.id == exercise_type_id).first()

    # 上传所有图片
    image_urls = []
    for f in files:
        url = await storage.upload_image(f)
        image_urls.append(url)

    # 调用 AI 批改（多图）
    ai_result = ai_client.correct_homework(
        db, image_urls, subject, sub.grade_level, exercise_type=exercise_type
    )

    # 保存记录，image_url 存 JSON 数组
    record = Record(
        student_id=current_user.id,
        subject=subject,
        exercise_type_id=exercise_type_id,
        image_url=json.dumps(image_urls, ensure_ascii=False),
        is_correct=ai_result["is_correct"],
        ai_feedback=json.dumps(ai_result["result"], ensure_ascii=False),
        token_input=ai_result["token_input"],
        token_output=ai_result["token_output"],
        llm_provider=ai_result["llm_provider"],
        llm_model=ai_result["llm_model"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "is_correct": record.is_correct,
        "output_schema": ai_result["output_schema"],
        "result": ai_result["result"],
        "subject": record.subject,
        "image_urls": image_urls,
        "image_url": json.dumps(image_urls, ensure_ascii=False),
    }


@router.post("/{record_id}/thinking")
def get_thinking(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.student_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 懒加载：已有缓存直接返回
    if record.ai_thinking:
        return {"thinking": json.loads(record.ai_thinking)}

    sub = check_subscription(db, current_user.id, record.subject)
    # image_url may be a JSON array string
    import json as _json
    try:
        image_url_for_thinking = _json.loads(record.image_url)
    except Exception:
        image_url_for_thinking = record.image_url
    ai_result = ai_client.get_thinking(db, image_url_for_thinking, record.subject, sub.grade_level)

    thinking_json = json.dumps(ai_result["result"], ensure_ascii=False)
    record.ai_thinking = thinking_json
    record.token_input += ai_result["token_input"]
    record.token_output += ai_result["token_output"]
    db.commit()

    return {"thinking": ai_result["result"]}


@router.get("/recent")
def get_recent(
    subject: str = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Record).filter(Record.student_id == current_user.id)
    if subject:
        query = query.filter(Record.subject == subject)
    records = query.order_by(Record.created_at.desc()).limit(limit).all()

    from datetime import timedelta
    return [
        {
            "id": r.id,
            "subject": r.subject,
            "is_correct": r.is_correct,
            "image_url": r.image_url,
            "llm_model": r.llm_model or "",
            "created_at": (r.created_at + timedelta(hours=8)).isoformat() if r.created_at else "",
        }
        for r in records
    ]


@router.get("/{record_id}")
def get_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.student_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    result = json.loads(record.ai_feedback) if record.ai_feedback else {}
    # 从题型配置中读取 output_schema，避免 essay/simple 误判
    if record.exercise_type_id:
        et = db.query(ExerciseType).filter(ExerciseType.id == record.exercise_type_id).first()
        output_schema = et.output_schema if et else ("items" if isinstance(result, list) else "simple")
    else:
        output_schema = "items" if isinstance(result, list) else "simple"

    return {
        "id": record.id,
        "is_correct": record.is_correct,
        "output_schema": output_schema,
        "result": result,
        "subject": record.subject,
        "image_url": record.image_url,
    }


@router.delete("/{record_id}")
def delete_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Record).filter(
        Record.id == record_id,
        Record.student_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(record)
    db.commit()
    return {"message": "已删除"}
