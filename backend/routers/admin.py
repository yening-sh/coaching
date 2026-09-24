"""
后台管理接口：账号管理、LLM配置、Token统计
所有接口需要 admin 权限
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timedelta

from database import get_db
from models.user import User
from models.subscription import Subscription
from models.record import Record
from models.llm_config import LLMConfig
from models.exercise_type import ExerciseType
from models.exercise_type_prompt import ExerciseTypePrompt
from core.security import require_admin, hash_password

router = APIRouter(prefix="/admin", tags=["后台管理"])

EXCHANGE_RATE = 6.7  # USD → CNY

def calc_cost(tok_in, tok_out, price_in, price_out, currency="CNY"):
    """返回 {"cny": x, "usd": x}，统一按汇率6.7换算"""
    if not tok_in:
        return {"cny": 0, "usd": 0}
    raw = tok_in / 1_000_000 * price_in + tok_out / 1_000_000 * price_out
    if currency == "USD":
        usd = round(raw, 4)
        cny = round(raw * EXCHANGE_RATE, 4)
    else:
        cny = round(raw, 4)
        usd = round(raw / EXCHANGE_RATE, 4)
    return {"cny": cny, "usd": usd}


# ==================== 账号管理 ====================

class CreateUserRequest(BaseModel):
    username: str
    password: str
    name: str
    grade_level: str   # junior | senior


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    grade_level: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


@router.get("/users")
def list_users(
    page: int = 1,
    limit: int = 20,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(User).filter(User.role == "student")
    if keyword:
        query = query.filter(
            (User.username.ilike(f"%{keyword}%")) | (User.name.ilike(f"%{keyword}%"))
        )
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset((page - 1) * limit).limit(limit).all()

    result = []
    today = date.today()
    first_day = today.replace(day=1)

    for u in users:
        # 当前有效订阅
        active_subs = db.query(Subscription).filter(
            Subscription.student_id == u.id,
            Subscription.is_active == True,
            Subscription.end_date >= today,
        ).all()

        # 本月 token 消耗
        month_tokens = db.query(
            func.sum(Record.token_input + Record.token_output)
        ).filter(
            Record.student_id == u.id,
            Record.created_at >= first_day,
        ).scalar() or 0

        result.append({
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "grade_level": u.grade_level,
            "is_active": u.is_active,
            "subjects": [s.subject for s in active_subs],
            "subscriptions": [
                {
                    "id": s.id,
                    "subject": s.subject,
                    "start_date": s.start_date.isoformat(),
                    "end_date": s.end_date.isoformat(),
                }
                for s in active_subs
            ],
            "month_tokens": month_tokens,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {"total": total, "items": result}


@router.post("/users")
def create_user(
    req: CreateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="账号已存在")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        name=req.name,
        role="student",
        grade_level=req.grade_level,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "message": "账号创建成功"}


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    req: UpdateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.name is not None:
        user.name = req.name
    if req.grade_level is not None:
        user.grade_level = req.grade_level
    if req.is_active is not None:
        user.is_active = req.is_active
        if not req.is_active:
            user.session_token = None  # 禁用时踢下线
    if req.password:
        user.password_hash = hash_password(req.password)

    db.commit()
    return {"message": "更新成功"}


# ==================== 科目订阅管理 ====================

class AddSubscriptionRequest(BaseModel):
    student_id: str
    subject: str
    grade_level: Optional[str] = None
    end_date: str   # YYYY-MM-DD
    note: Optional[str] = "管理员手动开通"


@router.get("/users/{user_id}/records")
def user_records(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取某用户每次批改的 token 明细"""
    query = db.query(Record).filter(Record.student_id == user_id).order_by(desc(Record.created_at))
    total = query.count()
    records = query.offset((page - 1) * limit).limit(limit).all()

    # 预加载所有 LLM 配置，按 model_id 索引
    all_configs = {c.model_id: c for c in db.query(LLMConfig).all()}

    SUBJECT_NAMES = {"math": "数学", "chinese": "语文", "english": "英语",
                     "physics": "物理", "chemistry": "化学", "biology": "生物"}

    items = []
    for r in records:
        tok_in = r.token_input or 0
        tok_out = r.token_output or 0
        cfg = all_configs.get(r.llm_model)
        price_in = cfg.price_input if cfg else 0
        price_out = cfg.price_output if cfg else 0
        currency = cfg.price_currency if cfg else "CNY"
        cost = calc_cost(tok_in, tok_out, price_in, price_out, currency)
        items.append({
            "id": r.id,
            "subject": SUBJECT_NAMES.get(r.subject, r.subject),
            "token_input": tok_in,
            "token_output": tok_out,
            "cost_cny": cost["cny"],
            "cost_usd": cost["usd"],
            "model": r.llm_model or "-",
            "created_at": (r.created_at + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M") if r.created_at else "",
        })

    return {"total": total, "items": items}


@router.post("/subscriptions")
def add_subscription(
    req: AddSubscriptionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    # 若已有相同科目有效订阅，先将其关闭
    db.query(Subscription).filter(
        Subscription.student_id == req.student_id,
        Subscription.subject == req.subject,
        Subscription.is_active == True,
    ).update({"is_active": False})

    user = db.query(User).filter(User.id == req.student_id).first()

    sub = Subscription(
        student_id=req.student_id,
        subject=req.subject,
        grade_level=req.grade_level or user.grade_level,
        start_date=date.today(),
        end_date=date.fromisoformat(req.end_date),
        note=req.note,
    )
    db.add(sub)
    db.commit()
    return {"message": "订阅开通成功"}


@router.delete("/subscriptions/{sub_id}")
def remove_subscription(
    sub_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")
    sub.is_active = False
    db.commit()
    return {"message": "已关闭订阅"}


# ==================== LLM 配置 ====================

class LLMConfigRequest(BaseModel):
    name: str
    provider: str
    model_id: str
    api_key: str
    api_base_url: Optional[str] = None
    price_input: float = 0.0
    price_output: float = 0.0
    price_currency: str = "CNY"
    note: Optional[str] = None


class UpdateLLMConfigRequest(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    price_input: Optional[float] = None
    price_output: Optional[float] = None
    price_currency: Optional[str] = None
    note: Optional[str] = None


@router.get("/llm-configs")
def list_llm_configs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    configs = db.query(LLMConfig).order_by(desc(LLMConfig.created_at)).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "provider": c.provider,
            "model_id": c.model_id,
            "api_base_url": c.api_base_url,
            "is_active": c.is_active,
            "price_input": c.price_input,
            "price_output": c.price_output,
            "price_currency": c.price_currency or "CNY",
            "note": c.note,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            # api_key 不返回完整值
            "api_key_hint": f"...{c.api_key[-6:]}" if c.api_key else "",
        }
        for c in configs
    ]


@router.post("/llm-configs")
def create_llm_config(
    req: LLMConfigRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = LLMConfig(**req.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return {"id": config.id, "message": "配置已添加"}


@router.post("/llm-configs/{config_id}/activate")
def activate_llm_config(
    config_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    # 先关闭所有
    db.query(LLMConfig).update({"is_active": False})
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    config.is_active = True
    db.commit()
    return {"message": f"已切换到 {config.name}"}


@router.delete("/llm-configs/{config_id}")
def delete_llm_config(
    config_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    if config.is_active:
        raise HTTPException(status_code=400, detail="不能删除当前激活的配置，请先切换到其他配置")
    db.delete(config)
    db.commit()
    return {"message": "已删除"}


@router.patch("/llm-configs/{config_id}")
def update_llm_config(
    config_id: str,
    req: UpdateLLMConfigRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    data = req.model_dump(exclude_none=True)
    if not data.get('api_key'):
        data.pop('api_key', None)  # 留空时不覆盖原有 key
    for field, value in data.items():
        setattr(config, field, value)
    db.commit()
    return {"message": "更新成功"}


@router.post("/llm-configs/{config_id}/test")
def test_llm_config(
    config_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """发送一条纯文本消息验证 API Key 和连通性（不需要图片）"""
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    try:
        if config.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=config.api_key)
            msg = client.messages.create(
                model=config.model_id,
                max_tokens=16,
                messages=[{"role": "user", "content": "reply: ok"}],
            )
            reply = msg.content[0].text
        else:
            from openai import OpenAI
            client = OpenAI(
                api_key=config.api_key,
                base_url=config.api_base_url or None,
            )
            try:
                resp = client.chat.completions.create(
                    model=config.model_id,
                    max_tokens=16,
                    messages=[{"role": "user", "content": "reply: ok"}],
                )
            except Exception:
                resp = client.chat.completions.create(
                    model=config.model_id,
                    max_completion_tokens=16,
                    messages=[{"role": "user", "content": "reply: ok"}],
                )
            reply = resp.choices[0].message.content

        return {"success": True, "reply": reply}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Token 统计 ====================

@router.get("/stats/overview")
def stats_overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    today = date.today()
    first_day = today.replace(day=1)

    # 今日
    today_stats = db.query(
        func.count(Record.id),
        func.sum(Record.token_input),
        func.sum(Record.token_output),
    ).filter(func.date(Record.created_at) == today).first()

    # 本月
    month_stats = db.query(
        func.count(Record.id),
        func.sum(Record.token_input),
        func.sum(Record.token_output),
    ).filter(Record.created_at >= first_day).first()

    # 当前激活的LLM价格
    active_llm = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
    price_in = active_llm.price_input if active_llm else 0
    price_out = active_llm.price_output if active_llm else 0
    currency = active_llm.price_currency if active_llm else "CNY"

    def _cost(tok_in, tok_out):
        return calc_cost(tok_in or 0, tok_out or 0, price_in, price_out, currency)

    return {
        "today": {
            "records": today_stats[0] or 0,
            "token_input": today_stats[1] or 0,
            "token_output": today_stats[2] or 0,
            "cost_cny": _cost(today_stats[1], today_stats[2])["cny"],
            "cost_usd": _cost(today_stats[1], today_stats[2])["usd"],
        },
        "month": {
            "records": month_stats[0] or 0,
            "token_input": month_stats[1] or 0,
            "token_output": month_stats[2] or 0,
            "cost_cny": _cost(month_stats[1], month_stats[2])["cny"],
            "cost_usd": _cost(month_stats[1], month_stats[2])["usd"],
        },
        "active_llm": active_llm.name if active_llm else "未配置",
    }


@router.get("/stats/by-user")
def stats_by_user(
    days: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    since = datetime.utcnow() - timedelta(days=days)

    rows = db.query(
        Record.student_id,
        func.count(Record.id).label("records"),
        func.sum(Record.token_input).label("tok_in"),
        func.sum(Record.token_output).label("tok_out"),
    ).filter(
        Record.created_at >= since
    ).group_by(Record.student_id).order_by(desc("tok_in")).limit(50).all()

    active_llm = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
    price_in = active_llm.price_input if active_llm else 0
    price_out = active_llm.price_output if active_llm else 0
    currency = active_llm.price_currency if active_llm else "CNY"

    result = []
    for row in rows:
        user = db.query(User).filter(User.id == row.student_id).first()
        tok_in = row.tok_in or 0
        tok_out = row.tok_out or 0
        cost = calc_cost(tok_in, tok_out, price_in, price_out, currency)
        result.append({
            "student_id": row.student_id,
            "name": user.name if user else "未知",
            "username": user.username if user else "",
            "records": row.records,
            "token_input": tok_in,
            "token_output": tok_out,
            "cost_cny": cost["cny"],
            "cost_usd": cost["usd"],
        })

    return result


@router.get("/stats/daily")
def stats_daily(
    days: int = 30,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """最近N天每日统计，用于趋势图"""
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.query(
        func.date(Record.created_at).label("day"),
        func.count(Record.id).label("records"),
        func.sum(Record.token_input).label("tok_in"),
        func.sum(Record.token_output).label("tok_out"),
    ).filter(
        Record.created_at >= since
    ).group_by("day").order_by("day").all()

    active_llm = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
    price_in = active_llm.price_input if active_llm else 0
    price_out = active_llm.price_output if active_llm else 0
    currency = active_llm.price_currency if active_llm else "CNY"

    result = []
    for r in rows:
        tok_in = r.tok_in or 0
        tok_out = r.tok_out or 0
        cost = calc_cost(tok_in, tok_out, price_in, price_out, currency)
        result.append({
            "date": str(r.day),
            "records": r.records,
            "tokens": tok_in + tok_out,
            "token_input": tok_in,
            "token_output": tok_out,
            "cost_cny": cost["cny"],
            "cost_usd": cost["usd"],
        })
    return result


# ==================== 题型管理 ====================

class ExerciseTypeRequest(BaseModel):
    subject: str
    name: str
    prompt_template: str
    output_schema: str = "simple"
    sort_order: str = "0"


class UpdateExerciseTypeRequest(BaseModel):
    name: Optional[str] = None
    prompt_template: Optional[str] = None
    output_schema: Optional[str] = None
    sort_order: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/exercise-types")
def list_exercise_types(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    types = db.query(ExerciseType).order_by(ExerciseType.subject, ExerciseType.sort_order).all()
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "name": t.name,
            "output_schema": t.output_schema,
            "is_active": t.is_active,
            "sort_order": t.sort_order,
            "prompt_template": t.prompt_template,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in types
    ]


@router.post("/exercise-types")
def create_exercise_type(
    req: ExerciseTypeRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    et = ExerciseType(**req.model_dump())
    db.add(et)
    db.commit()
    db.refresh(et)
    return {"id": et.id, "message": "题型已添加"}


@router.patch("/exercise-types/{type_id}")
def update_exercise_type(
    type_id: str,
    req: UpdateExerciseTypeRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    et = db.query(ExerciseType).filter(ExerciseType.id == type_id).first()
    if not et:
        raise HTTPException(status_code=404, detail="题型不存在")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(et, field, value)
    db.commit()
    return {"message": "更新成功"}


@router.delete("/exercise-types/{type_id}")
def delete_exercise_type(
    type_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    et = db.query(ExerciseType).filter(ExerciseType.id == type_id).first()
    if not et:
        raise HTTPException(status_code=404, detail="题型不存在")
    db.delete(et)
    db.commit()
    return {"message": "已删除"}


# ==================== Prompt 版本管理 ====================

class PromptVersionRequest(BaseModel):
    version_name: str
    prompt_template: str


class UpdatePromptVersionRequest(BaseModel):
    version_name: Optional[str] = None
    prompt_template: Optional[str] = None


@router.get("/exercise-types/{type_id}/prompts")
def list_prompt_versions(
    type_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    et = db.query(ExerciseType).filter(ExerciseType.id == type_id).first()
    if not et:
        raise HTTPException(status_code=404, detail="题型不存在")
    prompts = db.query(ExerciseTypePrompt).filter(
        ExerciseTypePrompt.exercise_type_id == type_id
    ).order_by(ExerciseTypePrompt.created_at).all()
    return {
        "exercise_type": {"id": et.id, "name": et.name, "subject": et.subject, "output_schema": et.output_schema},
        "prompts": [
            {
                "id": p.id,
                "version_name": p.version_name,
                "prompt_template": p.prompt_template,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in prompts
        ],
    }


@router.post("/exercise-types/{type_id}/prompts")
def create_prompt_version(
    type_id: str,
    req: PromptVersionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    et = db.query(ExerciseType).filter(ExerciseType.id == type_id).first()
    if not et:
        raise HTTPException(status_code=404, detail="题型不存在")
    p = ExerciseTypePrompt(
        exercise_type_id=type_id,
        version_name=req.version_name,
        prompt_template=req.prompt_template,
        is_active=False,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "message": "版本已添加"}


@router.patch("/exercise-types/{type_id}/prompts/{prompt_id}")
def update_prompt_version(
    type_id: str,
    prompt_id: str,
    req: UpdatePromptVersionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    p = db.query(ExerciseTypePrompt).filter(
        ExerciseTypePrompt.id == prompt_id,
        ExerciseTypePrompt.exercise_type_id == type_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="版本不存在")
    for field, value in req.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    return {"message": "更新成功"}


@router.post("/exercise-types/{type_id}/prompts/{prompt_id}/activate")
def activate_prompt_version(
    type_id: str,
    prompt_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    p = db.query(ExerciseTypePrompt).filter(
        ExerciseTypePrompt.id == prompt_id,
        ExerciseTypePrompt.exercise_type_id == type_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="版本不存在")
    # 先关闭同题型下所有版本
    db.query(ExerciseTypePrompt).filter(
        ExerciseTypePrompt.exercise_type_id == type_id
    ).update({"is_active": False})
    p.is_active = True
    db.commit()
    return {"message": f"已激活「{p.version_name}」"}


@router.delete("/exercise-types/{type_id}/prompts/{prompt_id}")
def delete_prompt_version(
    type_id: str,
    prompt_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    p = db.query(ExerciseTypePrompt).filter(
        ExerciseTypePrompt.id == prompt_id,
        ExerciseTypePrompt.exercise_type_id == type_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="版本不存在")
    if p.is_active:
        raise HTTPException(status_code=400, detail="不能删除当前激活的版本，请先切换到其他版本")
    db.delete(p)
    db.commit()
    return {"message": "已删除"}

