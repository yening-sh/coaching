"""
LLM 统一调用层。
后台切换 LLM 配置后，所有调用自动使用新配置，无需重启服务。
"""
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.llm_config import LLMConfig
from models.general_prompt import GeneralPrompt

SUBJECT_NAMES = {
    "math": "数学", "chinese": "语文", "english": "英语",
    "physics": "物理", "chemistry": "化学", "biology": "生物",
}
GRADE_NAMES = {"junior": "初中", "senior": "高中"}

CORRECT_PROMPT = """你是一个{grade}{subject}作业批改助手。
请仔细观察图片中学生的解题过程和答案，进行批改。

要求：
1. 判断答案是否正确
2. 如果有错误，指出具体错在哪一步，用简洁清晰的语言解释原因
3. 给出简短的改进提示，引导学生思考，但【绝对不能给出完整答案】
4. 语气鼓励，适合{grade}学生

请用以下JSON格式返回（不要有其他内容）：
{{
  "is_correct": true或false,
  "feedback": "批改说明，指出错误位置和原因",
  "hint": "给学生的改进提示，引导思考但不给答案"
}}"""

THINKING_PROMPT = """你是一个{grade}{subject}解题辅导老师。
根据图片中的题目，给出详细的解题思路引导。

要求：
1. 分步骤引导，每步说明思路和方法
2. 【绝对不能直接给出最终答案】，最后一步引导学生自己算出答案
3. 语言清晰，适合{grade}学生理解
4. 鼓励学生自己动手尝试

请用以下JSON格式返回（不要有其他内容）：
{{
  "steps": [
    {{"title": "第一步标题", "content": "具体说明"}},
    {{"title": "第二步标题", "content": "具体说明"}}
  ],
  "encouragement": "结尾的鼓励语"
}}"""


def get_active_config(db: Session) -> LLMConfig:
    config = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
    if not config:
        raise HTTPException(status_code=500, detail="未配置可用的AI模型，请联系管理员")
    return config


def call_llm(config: LLMConfig, prompt: str, image_url: str | list[str], max_tokens: int = 1024) -> tuple[str, int, int]:
    """
    调用 LLM，返回 (response_text, input_tokens, output_tokens)
    image_url 可以是单个字符串或字符串列表（多图）
    """
    image_urls = [image_url] if isinstance(image_url, str) else image_url
    if config.provider == "anthropic":
        return _call_anthropic(config, prompt, image_urls, max_tokens)
    elif config.provider == "openai":
        return _call_openai(config, prompt, image_urls, max_tokens)
    else:
        raise HTTPException(status_code=500, detail=f"不支持的LLM provider: {config.provider}")


def _call_anthropic(config: LLMConfig, prompt: str, image_urls: list[str], max_tokens: int = 1024) -> tuple[str, int, int]:
    import anthropic, base64
    client = anthropic.Anthropic(api_key=config.api_key)

    def _load_image(image_url: str):
        if image_url.startswith("/uploads/"):
            from pathlib import Path
            abs_path = Path(__file__).parent.parent / image_url.lstrip("/")
            image_bytes = abs_path.read_bytes()
            ext = abs_path.suffix.lstrip(".").lower()
            media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        else:
            resp = httpx.get(image_url, timeout=30)
            image_bytes = resp.content
            media_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        return base64.standard_b64encode(image_bytes).decode("utf-8"), media_type

    content = []
    for url in image_urls:
        data, media_type = _load_image(url)
        content.append({"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}})
    content.append({"type": "text", "text": prompt})

    message = client.messages.create(
        model=config.model_id,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    )
    text = message.content[0].text
    return text, message.usage.input_tokens, message.usage.output_tokens


def _local_path_to_data_url(image_url: str) -> str:
    """将本地文件路径转为 base64 data URL（开发模式下使用）"""
    import base64
    from pathlib import Path
    # /uploads/xxx.jpg → backend/uploads/xxx.jpg
    rel_path = image_url.lstrip("/")
    abs_path = Path(__file__).parent.parent / rel_path
    data = abs_path.read_bytes()
    ext = abs_path.suffix.lstrip(".").lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    b64 = base64.standard_b64encode(data).decode()
    return f"data:{mime};base64,{b64}"


def _call_openai(config: LLMConfig, prompt: str, image_urls: list[str], max_tokens: int = 1024) -> tuple[str, int, int]:
    from openai import OpenAI
    client = OpenAI(api_key=config.api_key, base_url=config.api_base_url or None)

    content = []
    for url in image_urls:
        if url.startswith("/uploads/"):
            url = _local_path_to_data_url(url)
        content.append({"type": "image_url", "image_url": {"url": url}})
    content.append({"type": "text", "text": prompt})

    kwargs = dict(model=config.model_id, messages=[{"role": "user", "content": content}])
    # o-series / reasoning models require max_completion_tokens; standard models use max_tokens
    model_id = config.model_id.lower()
    use_completion_tokens = any(model_id.startswith(p) for p in ("o1", "o3", "o4", "gpt-5", "gpt-o"))
    try:
        if use_completion_tokens:
            response = client.chat.completions.create(**kwargs, max_completion_tokens=max_tokens)
        else:
            response = client.chat.completions.create(**kwargs, max_tokens=max_tokens)
    except Exception as e:
        print(f"[ai_client] first call failed ({e}), retrying with max_completion_tokens")
        response = client.chat.completions.create(**kwargs, max_completion_tokens=max_tokens)
    choice = response.choices[0]
    text = choice.message.content or ""
    print(f"[ai_client] finish_reason={choice.finish_reason}, text_len={len(text)}, text[:300]={text[:300]!r}")
    usage = response.usage
    return text, usage.prompt_tokens, usage.completion_tokens


def correct_homework(db: Session, image_urls: list[str], subject: str, grade_level: str,
                     exercise_type=None) -> dict:
    """
    image_urls: 图片URL列表（单张或多张）
    AI 自行判断哪些是题目、哪些是学生作答
    """
    import json, re
    config = get_active_config(db)
    grade = GRADE_NAMES.get(grade_level, "初中")
    subj = SUBJECT_NAMES.get(subject, subject)

    if exercise_type:
        # 优先用该题型下激活的 prompt 版本
        from models.exercise_type_prompt import ExerciseTypePrompt
        active_prompt = db.query(ExerciseTypePrompt).filter(
            ExerciseTypePrompt.exercise_type_id == exercise_type.id,
            ExerciseTypePrompt.is_active == True,
        ).first()
        prompt_tpl = active_prompt.prompt_template if active_prompt else exercise_type.prompt_template
        prompt = prompt_tpl.replace("{grade}", grade).replace("{subject}", subj)
        output_schema = exercise_type.output_schema
    else:
        prompt = CORRECT_PROMPT.format(grade=grade, subject=subj)
        output_schema = "simple"

    if len(image_urls) > 1:
        prompt = f"以下共 {len(image_urls)} 张图片，请自行判断哪些是题目、哪些是学生的手写作答，然后进行批改。\n\n" + prompt

    # 追加通用 prompt 模版（按 subject + grade_level 匹配）
    general = db.query(GeneralPrompt).filter(
        GeneralPrompt.subject == subject,
        GeneralPrompt.grade_level == grade_level,
        GeneralPrompt.is_active == True,
    ).first()

    if output_schema == "summary":
        # summary 的词汇积累和识别文本已内置于 prompt，general prompt 只追加红色文字规则
        if general:
            prompt += "\n\n【通用补充规则】红色文字识别：如果图片中同时存在黑色/蓝色文字和红色文字，红色是老师或学生的批改标注，请忽略红色内容，只批改黑色/蓝色的学生原始作答。"
    else:
        if general:
            prompt += "\n\n" + general.prompt_template

    # 追加 ocr_text 要求（供后续双模型改造用）
    if output_schema == "translation":
        prompt += "\n\n另外，请将返回格式改为：{\"items\": [...原数组内容...], \"ocr_text\": \"图片中识别到的全部文字\"}"
    elif output_schema != "summary":
        # summary 的识别文本已内置于 prompt
        prompt += "\n\n另外，请在返回的 JSON 中额外加入一个字段 \"ocr_text\"，值为你从图片中识别到的全部文字（原文照录，不作修改）。"

    raw, tok_in, tok_out = call_llm(config, prompt, image_urls, max_tokens=16000)
    print(f"[ai_client] output_schema={output_schema}, images={len(image_urls)}, raw[:200]={raw[:200]!r}")

    if output_schema == "translation":
        # 期望返回包含 items 数组和 ocr_text 的对象，或直接返回数组（兼容旧格式）
        ocr_text = ""
        # 先尝试解析外层对象
        obj_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if obj_match:
            try:
                outer = json.loads(obj_match.group())
                if "items" in outer:
                    result = outer["items"]
                    ocr_text = outer.get("ocr_text", "")
                else:
                    result = []
            except json.JSONDecodeError:
                result = []
        else:
            # fallback：直接匹配数组
            arr_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if arr_match:
                try:
                    result = json.loads(arr_match.group())
                except json.JSONDecodeError:
                    result = []
            else:
                result = []
        # 整体 is_correct：所有题都对才算全对
        all_correct = all(item.get("is_correct", False) for item in result) if result else False
        print(f"[ai_client] parsed translation count={len(result)}, all_correct={all_correct}")
    elif output_schema == "essay":
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group()) if match else {"score": 0, "overall": raw, "sentences": [], "revised": "", "suggestions": "", "model_essay": ""}
        all_correct = result.get("score", 0) >= 18
        ocr_text = result.get("ocr_text", "") if isinstance(result, dict) else ""
    elif output_schema in ("grammar", "cloze"):
        # 期望返回 JSON 对象，含 total_score/full_score/blanks 等
        full_score_default = 15 if output_schema == "grammar" else 10
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                result = {"total_score": 0, "full_score": full_score_default, "overall_comment": raw, "blanks": []}
        else:
            result = {"total_score": 0, "full_score": full_score_default, "overall_comment": raw, "blanks": []}
        all_correct = result.get("total_score", 0) >= result.get("full_score", full_score_default)
        ocr_text = result.get("ocr_text", "") if isinstance(result, dict) else ""
    elif output_schema == "summary":
        # 返回 Markdown，从末尾「## 识别文本」节提取 ocr_text，其余作为 feedback
        ocr_match = re.search(r'##\s*识别文本\s*\n(.*)', raw, re.DOTALL)
        if ocr_match:
            ocr_text = ocr_match.group(1).strip()
            result = {"feedback": raw[:ocr_match.start()].rstrip()}
        else:
            ocr_text = ""
            result = {"feedback": raw}
        all_correct = True
    else:
        # math / 其他：返回 JSON 对象
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(match.group()) if match else {"is_correct": False, "feedback": raw, "hint": ""}
        all_correct = result.get("is_correct", False)
        ocr_text = result.get("ocr_text", "") if isinstance(result, dict) else ""

    return {
        "result": result,
        "output_schema": output_schema,
        "is_correct": all_correct,
        "ocr_text": ocr_text,
        "token_input": tok_in,
        "token_output": tok_out,
        "llm_provider": config.provider,
        "llm_model": config.model_id,
    }


def get_thinking(db: Session, image_url: str, subject: str, grade_level: str) -> dict:
    config = get_active_config(db)
    prompt = THINKING_PROMPT.format(
        grade=GRADE_NAMES.get(grade_level, "初中"),
        subject=SUBJECT_NAMES.get(subject, subject),
    )
    raw, tok_in, tok_out = call_llm(config, prompt, image_url)

    import json, re
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    result = json.loads(match.group()) if match else {"steps": [], "encouragement": raw}

    return {
        "result": result,
        "token_input": tok_in,
        "token_output": tok_out,
    }
