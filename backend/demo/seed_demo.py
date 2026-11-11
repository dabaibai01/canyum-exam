"""创建一套用于展示功能的演示题库。

用法：
    cd backend
    python demo/seed_demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine
from app.models.category import Category
from app.models.question import Question, QuestionOption

Base.metadata.create_all(bind=engine)

CATEGORIES = [
    ("演示-安全常识", 1),
    ("演示-业务基础", 2),
    ("演示-服务规范", 3),
]

QUESTIONS = [
    {
        "category": "演示-安全常识",
        "type": "single",
        "content": "进入作业现场前，首先应确认的是？",
        "options": [("A", "安全防护用品是否齐全", True), ("B", "手机电量是否充足", False),
                    ("C", "午饭是否已经吃好", False), ("D", "当天天气是否晴朗", False)],
        "analysis": "进入现场前应先确认劳动防护用品齐全、有效。",
    },
    {
        "category": "演示-安全常识",
        "type": "single",
        "content": "发现设备运行异常时，正确的做法是？",
        "options": [("A", "继续使用，等下班再处理", False), ("B", "立即停机并报告", True),
                    ("C", "自行拆卸检查", False), ("D", "暂时忽略异常", False)],
        "analysis": "设备异常应立即停机并按流程报告，禁止带病运行。",
    },
    {
        "category": "演示-安全常识",
        "type": "multiple",
        "content": "以下哪些属于劳动防护用品？",
        "options": [("A", "安全帽", True), ("B", "防护手套", True),
                    ("C", "普通水杯", False), ("D", "防护眼镜", True)],
        "analysis": "安全帽、防护手套、防护眼镜属于劳动防护用品。",
    },
    {
        "category": "演示-安全常识",
        "type": "judge",
        "content": "作业现场可以随意吸烟。",
        "options": [("对", "对", False), ("错", "错", True)],
        "analysis": "作业现场通常属于禁烟区域，应遵守现场消防与安全管理规定。",
    },
    {
        "category": "演示-业务基础",
        "type": "single",
        "content": "整理工作台时，优先应做的是？",
        "options": [("A", "分类定位，保持通道畅通", True), ("B", "把所有物品堆在一起", False),
                    ("C", "丢弃全部工具", False), ("D", "等待他人整理", False)],
        "analysis": "工作台应分类定位、保持通道畅通，便于取用和交接。",
    },
    {
        "category": "演示-业务基础",
        "type": "single",
        "content": "交接班时，最重要的信息是？",
        "options": [("A", "本班未完成事项和风险点", True), ("B", "个人休息安排", False),
                    ("C", "与工作无关的聊天内容", False), ("D", "当天食堂菜单", False)],
        "analysis": "交接班应重点说明未完成事项、设备状态和风险点。",
    },
    {
        "category": "演示-业务基础",
        "type": "multiple",
        "content": "日常巡检通常需要关注哪些内容？",
        "options": [("A", "设备运行状态", True), ("B", "现场安全通道", True),
                    ("C", "记录是否完整", True), ("D", "个人社交消息", False)],
        "analysis": "巡检关注设备、安全通道和记录完整性。",
    },
    {
        "category": "演示-业务基础",
        "type": "judge",
        "content": "交接班记录可以不写未完成事项。",
        "options": [("对", "对", False), ("错", "错", True)],
        "analysis": "未完成事项属于交接重点，必须记录并说明。",
    },
    {
        "category": "演示-服务规范",
        "type": "single",
        "content": "面对服务对象的咨询，首先应该？",
        "options": [("A", "耐心倾听并确认需求", True), ("B", "直接打断", False),
                    ("C", "让对方自行查找", False), ("D", "不作回应", False)],
        "analysis": "先倾听、再确认需求，才能准确回应。",
    },
    {
        "category": "演示-服务规范",
        "type": "single",
        "content": "遇到无法立即解决的问题时，合适的方式是？",
        "options": [("A", "说明情况并给出后续处理渠道", True), ("B", "编造一个答案", False),
                    ("C", "直接挂断", False), ("D", "把问题推给其他人", False)],
        "analysis": "无法立即解决时应说明情况，并给出可执行的后续渠道。",
    },
    {
        "category": "演示-服务规范",
        "type": "multiple",
        "content": "良好的服务沟通应包括哪些做法？",
        "options": [("A", "使用礼貌用语", True), ("B", "复述确认关键信息", True),
                    ("C", "及时反馈处理进度", True), ("D", "随意承诺无法完成的事项", False)],
        "analysis": "礼貌、确认、反馈是基本服务沟通要求；不应随意承诺。",
    },
    {
        "category": "演示-服务规范",
        "type": "judge",
        "content": "服务过程中可以随意泄露服务对象的个人信息。",
        "options": [("对", "对", False), ("错", "错", True)],
        "analysis": "个人信息应依法依规保护，不得随意泄露。",
    },
]


def main():
    db = SessionLocal()
    try:
        category_map = {}
        for name, sort in CATEGORIES:
            item = db.query(Category).filter(Category.name == name, Category.type == "question").first()
            if not item:
                item = Category(name=name, parent_id=0, type="question", sort=sort, status=1)
                db.add(item)
                db.flush()
                print("创建分类", name)
            category_map[name] = item.id

        created = 0
        for data in QUESTIONS:
            exists = db.query(Question).filter(
                Question.category_id == category_map[data["category"]],
                Question.content == data["content"],
            ).first()
            if exists:
                continue
            q = Question(
                category_id=category_map[data["category"]],
                type=data["type"],
                content=data["content"],
                analysis=data.get("analysis", ""),
                difficulty=1,
                score=1.0,
                status=1,
            )
            db.add(q)
            db.flush()
            for idx, (label, content, correct) in enumerate(data["options"]):
                db.add(QuestionOption(
                    question_id=q.id,
                    label=label,
                    content=content,
                    is_correct=1 if correct else 0,
                    sort=idx,
                ))
            created += 1

        db.commit()
        print(f"演示题库完成：新增 {created} 道题（已存在的题目自动跳过）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
