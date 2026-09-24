#!/usr/bin/env python3
"""
初始化脚本：建表 + 创建管理员账号 + 可选创建示例 LLM 配置

用法：
    cd backend
    source venv/bin/activate          # 激活虚拟环境
    python init_db.py                  # 使用默认参数
    python init_db.py --admin-password mypass123   # 自定义密码
    python init_db.py --reset          # 危险：清空所有表重建（开发时用）
"""
import argparse
import sys
import os

# 确保能找到项目模块
sys.path.insert(0, os.path.dirname(__file__))


# ── 默认题型数据 ───────────────────────────────────────────────────────────────

EXERCISE_TYPES = [
    {
        "subject": "english",
        "name": "翻译题",
        "output_schema": "items",
        "sort_order": "1",
        "prompt_template": """\
你是一位{grade}{subject}老师，正在批改学生的汉译英翻译题。

图片中包含若干道翻译题（通常 5-10 道），每道题有中文原文和学生手写的英文翻译。

请逐题批改，对每道题给出以下内容：
1. 题目编号（number，整数）
2. 中文原题（original）
3. 学生的英文回答（student_answer，照原文抄录，保留错误）
4. 该题是否基本正确（is_correct，true/false；语法错误较多或关键词错误则为 false）
5. 批改说明（feedback）：
   - 若正确：简短肯定，并指出 1-2 处可优化的地方（如有）
   - 若错误：具体指出错误类型（词汇/语法/时态/主谓一致等），说明错在哪里
6. 修正后的句子（corrected）：基于学生原句最小修改，得到正确表达，不要过度改写

返回格式为 JSON 数组，不要有其他内容：
[
  {{
    "number": 1,
    "original": "中文原题",
    "student_answer": "学生原文",
    "is_correct": false,
    "feedback": "漏译了'年轻人'，应改为 young people；craft 应用复数 crafts",
    "corrected": "More and more young people are aware of the importance of protecting traditional crafts."
  }},
  ...
]

注意：
- 请识别图片中所有题目，不要遗漏
- student_answer 如果难以辨认，尽量还原，无法辨认的字用 [?] 标注
- feedback 用中文，corrected 用英文
- 语气鼓励，适合{grade}学生""",
    },
    {
        "subject": "english",
        "name": "书面表达（作文）",
        "output_schema": "essay",
        "sort_order": "2",
        "prompt_template": """\
你是一位{grade}{subject}高考阅卷老师，正在批改学生的书面表达作文。

请仔细阅读图片中学生的作文，按以下结构完整输出批改结果。

返回 JSON 格式（不要有其他内容）：
{{
  "score": 18,
  "score_comment": "内容基本完整，语言表达有一定错误，结构较清晰",
  "on_topic": true,
  "overall": "整体评价：简要说明文章优缺点，内容/语言/结构三个维度各一句话",
  "sentences": [
    {{
      "original": "学生原句（照原文抄录）",
      "errors": [
        {{"type": "error", "text": "原文中有误的部分", "correction": "修正为", "explanation": "错误原因"}},
        {{"type": "suggestion", "text": "可优化的部分", "correction": "建议改为", "explanation": "说明"}}
      ]
    }}
  ],
  "revised": "依照原文结构，修正所有错误后的完整版本（保留学生风格，不过度改写）",
  "suggestions": "从作文整体出发的 3-4 条提升建议，每条独立一行，用\\n分隔",
  "model_essay": "根据题目要求，重新写一篇高质量范文"
}}

字段说明：
- score：高考作文满分 25 分，根据内容、语言、格式综合评分
- sentences：逐句列出，每句的 errors 数组中：
    type="error" 表示会被扣分的错误（语法/时态/主谓一致/固定搭配等）
    type="suggestion" 表示建议优化但不强制（用词升级/表达更地道等）
    没有问题的句子 errors 可以是空数组 []
- revised：完整修改版，不要省略
- model_essay：完整范文，不要省略
- 所有说明文字用中文，英文文本照英文保留""",
    },
    {
        "subject": "math",
        "name": "解答题",
        "output_schema": "simple",
        "sort_order": "1",
        "prompt_template": """\
你是一位{grade}{subject}老师，正在批改学生的解答题。

请仔细观察图片中学生的解题过程和答案，进行批改。

要求：
1. 判断最终答案是否正确（is_correct）
2. 逐步检查解题过程，指出第一处出错的步骤和原因（feedback）
3. 给出引导性提示（hint），帮助学生发现自己的问题，但不要给出完整解法
4. 语气鼓励，适合{grade}学生

返回 JSON 格式（不要有其他内容）：
{{
  "is_correct": false,
  "feedback": "第3步设定方程时符号出错，应为…",
  "hint": "提示"
}}""",
    },
]


def _seed_exercise_types(db):
    from models.exercise_type import ExerciseType
    print("▶ 初始化题型数据...")
    count = 0
    for et in EXERCISE_TYPES:
        exists = db.query(ExerciseType).filter(
            ExerciseType.subject == et["subject"],
            ExerciseType.name == et["name"],
        ).first()
        if not exists:
            db.add(ExerciseType(**et))
            count += 1
    db.commit()
    if count:
        print(f"  ✓ 插入 {count} 个题型")
    else:
        print("  ✓ 题型数据已是最新，跳过")


def main():
    parser = argparse.ArgumentParser(description="初始化数据库")
    parser.add_argument("--admin-user",     default="admin",   help="管理员账号 (默认: admin)")
    parser.add_argument("--admin-password", default="admin123", help="管理员密码 (默认: admin123)")
    parser.add_argument("--admin-name",     default="管理员",   help="管理员显示名 (默认: 管理员)")
    parser.add_argument("--reset", action="store_true",
                        help="危险：删除所有表后重建（仅开发环境使用）")
    args = parser.parse_args()

    # 延迟导入，确保 .env 已经被 pydantic-settings 读取
    from database import engine, Base, get_db
    from models import user as user_mod      # 触发模型注册
    from models import subscription, record, mistake, llm_config, exercise_type, exercise_type_prompt
    from core.security import hash_password

    print("▶ 连接数据库...")
    try:
        with engine.connect() as conn:
            print("  ✓ 数据库连接成功")
    except Exception as e:
        print(f"\n✗ 无法连接数据库: {e}")
        print("\n请确认：")
        print("  1. PostgreSQL 已启动")
        print("  2. .env 中 DATABASE_URL 配置正确")
        print("  3. 数据库已创建（参考下方命令）")
        print()
        print("  创建数据库命令：")
        print("    psql -U postgres -c \"CREATE DATABASE coaching;\"")
        print("  或使用 brew 启动 PostgreSQL：")
        print("    brew services start postgresql@17")
        sys.exit(1)

    # 重建（开发时）
    if args.reset:
        confirm = input("⚠️  --reset 将删除所有数据，确认输入 yes: ")
        if confirm.strip().lower() != "yes":
            print("已取消")
            sys.exit(0)
        print("▶ 删除所有表...")
        Base.metadata.drop_all(bind=engine)
        print("  ✓ 完成")

    # 建表
    print("▶ 创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("  ✓ 完成")

    # 创建管理员账号（幂等：已存在则跳过）
    from sqlalchemy.orm import Session
    from models.user import User
    from models.exercise_type import ExerciseType

    with Session(engine) as db:
        existing = db.query(User).filter(User.username == args.admin_user).first()
        if existing:
            print(f"▶ 管理员账号 '{args.admin_user}' 已存在，跳过创建")
        else:
            admin = User(
                username=args.admin_user,
                password_hash=hash_password(args.admin_password),
                name=args.admin_name,
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"▶ 创建管理员账号")
            print(f"  账号: {args.admin_user}")
            print(f"  密码: {args.admin_password}")
            print(f"  ⚠️  请登录后台后立即修改密码！")

        # 插入默认题型（幂等）
        _seed_exercise_types(db)

    print()
    print("✅ 初始化完成！")
    print()
    print("下一步：")
    print("  1. 编辑 .env，填写 ANTHROPIC_API_KEY 或 OPENAI_API_KEY")
    print("  2. 启动后端：uvicorn main:app --reload")
    print("  3. 访问后台：http://localhost:5173/login")
    print(f"     账号: {args.admin_user} / 密码: {args.admin_password}")
    print("  4. 在后台「AI模型配置」中添加 LLM 配置并激活")
    print("  5. 在后台「账号管理」中创建学生账号并分配学科订阅")


if __name__ == "__main__":
    main()
