import csv
import io
import re
import zipfile
from xml.etree import ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.category import Category
from app.models.question import Question, QuestionOption
from app.schemas.question import (
    CategoryOut, CategoryCreate,
    QuestionOut, QuestionCreate, OptionOut, QuestionPageOut
)

router = APIRouter(prefix="/api/questions", tags=["题库"])

# ========== 分类管理 ==========

@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    type: str = Query("question", description="分类类型：question/video/book"),
    show_all: bool = Query(False, description="是否显示所有状态，管理后台用"),
    db: Session = Depends(get_db)
):
    query = db.query(Category).filter(Category.type == type)
    if not show_all:
        query = query.filter(Category.status == 1)
    categories = query.order_by(Category.sort, Category.id).all()

    # 统计各分类题量；父分类汇总子分类，便于前端展示“内燃专业（1817题）”
    counts = dict(
        db.query(Question.category_id, func.count(Question.id))
        .filter(Question.status == 1)
        .group_by(Question.category_id)
        .all()
    )
    children = {}
    for c in categories:
        if c.parent_id:
            children.setdefault(c.parent_id, []).append(c.id)

    result = []
    for c in categories:
        item = CategoryOut.model_validate(c)
        item.question_count = counts.get(c.id, 0) + sum(
            counts.get(child_id, 0) for child_id in children.get(c.id, [])
        )
        result.append(item)
    return result

@router.post("/categories", response_model=CategoryOut, dependencies=[Depends(require_admin)])
def create_category(cat_in: CategoryCreate, db: Session = Depends(get_db)):
    cat = Category(**cat_in.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/categories/{cat_id}", response_model=CategoryOut, dependencies=[Depends(require_admin)])
def update_category(cat_id: int, cat_in: CategoryCreate, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    for key, value in cat_in.model_dump().items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categories/{cat_id}", dependencies=[Depends(require_admin)])
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    db.delete(cat)
    db.commit()
    return {"message": "删除成功"}

# ========== 题目管理 ==========

def _build_question_query(db, category_id, type_, keyword, show_all):
    """构建题目查询：父分类会自动包含其子分类下的题目"""
    query = db.query(Question)
    if category_id and category_id > 0:
        child_ids = [
            c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()
        ]
        query = query.filter(Question.category_id.in_([category_id] + child_ids))
    if not show_all:
        query = query.filter(Question.status == 1)
    if type_:
        query = query.filter(Question.type == type_)
    if keyword and keyword.strip():
        query = query.filter(Question.content.contains(keyword.strip()))
    return query


def _dump_questions(db, questions):
    result = []
    for q in questions:
        q_data = QuestionOut.model_validate(q).model_dump()
        options = db.query(QuestionOption).filter(
            QuestionOption.question_id == q.id
        ).order_by(QuestionOption.sort).all()
        q_data["options"] = [OptionOut.model_validate(o) for o in options]
        result.append(q_data)
    return result


# ========== 批量导入 ==========

_XLSX_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_TYPE_MAP = {
    "单选题": "single", "单选": "single", "single": "single",
    "多选题": "multiple", "多选": "multiple", "multiple": "multiple",
    "判断题": "judge", "判断": "judge", "judge": "judge",
}
_DIFFICULTY_MAP = {"简单": 1, "中等": 2, "困难": 3, "1": 1, "2": 2, "3": 3}


def _col_index(ref: str) -> int | None:
    match = re.match(r"([A-Z]+)", (ref or "").upper())
    if not match:
        return None
    value = 0
    for ch in match.group(1):
        value = value * 26 + (ord(ch) - 64)
    return value - 1


def _read_xlsx_rows(data: bytes) -> list[list[str]]:
    """用标准库解析 xlsx，不依赖 openpyxl，服务器上无需额外装包"""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{{{_XLSX_NS}}}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{_XLSX_NS}}}t")))

        sheet_names = [n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
        if not sheet_names:
            raise ValueError("未找到工作表")
        sheet_path = "xl/worksheets/sheet1.xml" if "xl/worksheets/sheet1.xml" in names else sorted(sheet_names)[0]
        root = ET.fromstring(zf.read(sheet_path))

        rows: list[list[str]] = []
        for row in root.iter(f"{{{_XLSX_NS}}}row"):
            cells: dict[int, str] = {}
            for cell in row.findall(f"{{{_XLSX_NS}}}c"):
                idx = _col_index(cell.get("r", ""))
                if idx is None:
                    continue
                if cell.get("t") == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter(f"{{{_XLSX_NS}}}t"))
                else:
                    v = cell.find(f"{{{_XLSX_NS}}}v")
                    raw = v.text if v is not None and v.text is not None else ""
                    if cell.get("t") == "s":
                        try:
                            value = shared[int(raw)]
                        except (ValueError, IndexError):
                            value = ""
                    else:
                        value = raw
                cells[idx] = str(value).strip()
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        return rows


def _read_csv_rows(data: bytes) -> list[list[str]]:
    text = None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("文件编码无法识别，请另存为 UTF-8 的 CSV")
    return [[str(cell).strip() for cell in row] for row in csv.reader(io.StringIO(text))]


def _norm_header(value: str) -> str:
    return re.sub(r"[\s\u3000]+", "", str(value or "")).lower()


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return str(row[idx]).strip()


def _parse_type(value: str) -> str:
    key = re.sub(r"\s+", "", str(value or ""))
    if key not in _TYPE_MAP:
        raise ValueError("题型只能是单选题/多选题/判断题")
    return _TYPE_MAP[key]


def _parse_labels(value: str, options: list[dict], qtype: str) -> list[str]:
    text = re.sub(r"[\s,，、;；/|]+", "", str(value or "")).upper()
    if qtype == "judge":
        if text in ("对", "正确", "√", "A", "TRUE", "是", "1"):
            return ["A"]
        if text in ("错", "错误", "×", "B", "FALSE", "否", "0"):
            return ["B"]
    labels = re.findall(r"[A-J]", text)
    if not labels:
        raise ValueError("正确答案请填选项字母，例如 A 或 ABD")
    valid = {o["label"] for o in options if o["content"]}
    for label in labels:
        if label not in valid:
            raise ValueError(f"正确答案 {label} 在选项中不存在")
    return list(dict.fromkeys(labels))


@router.post("/import", dependencies=[Depends(require_admin)])
async def import_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """批量导入题库：支持 .xlsx / .csv，逐行校验并返回失败原因"""
    filename = (file.filename or "").lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="只支持 .xlsx 或 .csv 文件；.xls 请先另存为 .xlsx")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 20MB")

    try:
        rows = _read_xlsx_rows(data) if filename.endswith(".xlsx") else _read_csv_rows(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"文件解析失败：{exc}")
    if not rows:
        raise HTTPException(status_code=400, detail="文件里没有数据")

    header = [_norm_header(x) for x in rows[0]]
    header_map: dict[str, int] = {}
    option_cols: dict[str, int] = {}
    aliases = {
        "category": {"分类", "分类名称", "专业"},
        "category_id": {"分类id", "categoryid", "category_id"},
        "type": {"题型", "type"},
        "content": {"题干", "题目", "content", "question"},
        "answer": {"正确答案", "答案", "answer"},
        "analysis": {"解析", "analysis"},
        "score": {"分值", "score"},
        "difficulty": {"难度", "difficulty"},
        "image": {"图片", "图片地址", "image"},
    }
    for idx, name in enumerate(header):
        for key, names in aliases.items():
            if name in names and key not in header_map:
                header_map[key] = idx
        match = (
            re.match(r"(?:选项)?([a-j])(?:内容|选项)?$", name)
            or re.match(r"option([a-j])(?:content)?$", name)
        )
        if match:
            letter = match.group(1).upper()
            option_cols.setdefault(letter, idx)
        num_match = re.match(r"选项([1-9]|10)$", name)
        if num_match:
            letter = "ABCDEFGHIJ"[int(num_match.group(1)) - 1]
            option_cols.setdefault(letter, idx)

    if "content" not in header_map:
        raise HTTPException(status_code=400, detail="表头未找到“题干”列，请先下载模板")
    if "type" not in header_map:
        raise HTTPException(status_code=400, detail="表头未找到“题型”列，请先下载模板")
    if "answer" not in header_map:
        raise HTTPException(status_code=400, detail="表头未找到“正确答案”列，请先下载模板")
    if "category" not in header_map and "category_id" not in header_map:
        raise HTTPException(status_code=400, detail="表头未找到“分类”或“分类ID”列，请先下载模板")

    categories = db.query(Category).filter(Category.type == "question").all()
    cat_by_id = {c.id: c for c in categories}
    cat_by_name: dict[str, Category] = {}
    for c in categories:
        cat_by_name.setdefault(c.name.strip(), c)
    existing = {
        (int(q.category_id), q.type, (q.content or "").strip())
        for q in db.query(Question.category_id, Question.type, Question.content).all()
    }

    valid: list[dict] = []
    errors: list[dict] = []
    duplicates = 0
    seen: set[tuple] = set()

    for row_no, row in enumerate(rows[1:], start=2):
        if not any(str(cell).strip() for cell in row):
            continue
        try:
            cat_text = _cell(row, header_map.get("category"))
            cat_id_text = _cell(row, header_map.get("category_id"))
            category = None
            if cat_id_text:
                if not cat_id_text.isdigit() or int(cat_id_text) not in cat_by_id:
                    raise ValueError(f"分类ID {cat_id_text} 不存在")
                category = cat_by_id[int(cat_id_text)]
            elif cat_text:
                category = cat_by_name.get(cat_text)
                if not category:
                    raise ValueError(f"分类“{cat_text}”不存在，请先在分类管理里创建")
            else:
                raise ValueError("分类不能为空")

            qtype = _parse_type(_cell(row, header_map.get("type")))
            content = _cell(row, header_map.get("content"))
            if not content:
                raise ValueError("题干不能为空")

            options = []
            for letter in "ABCDEFGHIJ":
                text = _cell(row, option_cols.get(letter))
                if text:
                    options.append({"label": letter, "content": text})
            if qtype == "judge" and not options:
                options = [
                    {"label": "A", "content": "对"},
                    {"label": "B", "content": "错"},
                ]
            if len([o for o in options if o["content"]]) < 2:
                raise ValueError("至少需要两个有内容的选项（判断题可以不填，系统自动生成对/错）")

            labels = _parse_labels(_cell(row, header_map.get("answer")), options, qtype)
            if qtype != "multiple" and len(labels) > 1:
                raise ValueError("单选题/判断题只能有一个正确答案")
            if qtype == "multiple" and not labels:
                raise ValueError("多选题至少需要一个正确答案")

            for opt in options:
                opt["is_correct"] = 1 if opt["label"] in labels else 0
                opt["sort"] = "ABCDEFGHIJ".index(opt["label"]) + 1

            score_text = _cell(row, header_map.get("score"))
            score = float(score_text) if score_text else 1.0
            if score <= 0 or score > 10:
                raise ValueError("分值必须在 0.5～10 之间")

            diff_text = _cell(row, header_map.get("difficulty"))
            difficulty = _DIFFICULTY_MAP.get(diff_text, 1) if diff_text else 1

            key = (int(category.id), qtype, content)
            if key in existing or key in seen:
                duplicates += 1
                continue
            seen.add(key)

            valid.append({
                "category_id": int(category.id),
                "type": qtype,
                "content": content,
                "image": _cell(row, header_map.get("image")) or None,
                "analysis": _cell(row, header_map.get("analysis")) or None,
                "difficulty": difficulty,
                "score": score,
                "options": options,
            })
        except ValueError as exc:
            errors.append({"row": row_no, "message": str(exc)})
        except Exception as exc:
            errors.append({"row": row_no, "message": f"数据格式错误：{exc}"})

    if len(valid) > 5000:
        raise HTTPException(status_code=400, detail="单次最多导入 5000 道题，请拆分文件")

    try:
        for item in valid:
            q = Question(
                category_id=item["category_id"],
                type=item["type"],
                content=item["content"],
                image=item["image"],
                analysis=item["analysis"],
                difficulty=item["difficulty"],
                score=item["score"],
                status=1,
            )
            db.add(q)
            db.flush()
            for opt in item["options"]:
                db.add(QuestionOption(
                    question_id=q.id,
                    label=opt["label"],
                    content=opt["content"],
                    is_correct=opt["is_correct"],
                    sort=opt["sort"],
                ))
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="写入数据库失败，已回滚，请检查数据后重试")

    return {
        "total": len(valid) + len(errors) + duplicates,
        "success": len(valid),
        "failed": len(errors),
        "duplicates": duplicates,
        "errors": errors[:50],
    }


@router.get("/list", response_model=list[QuestionOut], dependencies=[Depends(require_admin)])
def list_questions(
    category_id: int | None = Query(None, description="分类ID，不传则查所有"),
    type: str | None = Query(None, description="题型"),
    keyword: str | None = Query(None, description="题干关键词"),
    show_all: bool = Query(False, description="是否显示所有状态，管理后台用"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = _build_question_query(db, category_id, type, keyword, show_all)
    questions = query.order_by(Question.id).offset((page - 1) * page_size).limit(page_size).all()
    return _dump_questions(db, questions)


@router.get("/page", response_model=QuestionPageOut, dependencies=[Depends(require_admin)])
def page_questions(
    category_id: int | None = Query(None, description="分类ID，不传则查所有"),
    type: str | None = Query(None, description="题型"),
    keyword: str | None = Query(None, description="题干关键词"),
    show_all: bool = Query(True, description="是否显示所有状态，管理后台用"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = _build_question_query(db, category_id, type, keyword, show_all)
    total = query.count()
    questions = query.order_by(Question.id).offset((page - 1) * page_size).limit(page_size).all()
    return QuestionPageOut(total=total, items=_dump_questions(db, questions))

@router.get("/{question_id}", response_model=QuestionOut, dependencies=[Depends(require_admin)])
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    q_data = QuestionOut.model_validate(q).model_dump()
    options = db.query(QuestionOption).filter(
        QuestionOption.question_id == q.id
    ).order_by(QuestionOption.sort).all()
    q_data["options"] = [OptionOut.model_validate(o) for o in options]
    return q_data

@router.post("/", response_model=QuestionOut, dependencies=[Depends(require_admin)])
def create_question(q_in: QuestionCreate, db: Session = Depends(get_db)):
    q_data = q_in.model_dump(exclude={"options"})
    q = Question(**q_data)
    db.add(q)
    db.flush()
    
    for opt in q_in.options:
        opt_obj = QuestionOption(question_id=q.id, **opt.model_dump())
        db.add(opt_obj)
    
    db.commit()
    db.refresh(q)
    return q

@router.put("/{question_id}", response_model=QuestionOut, dependencies=[Depends(require_admin)])
def update_question(question_id: int, q_in: QuestionCreate, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    
    q_data = q_in.model_dump(exclude={"options"})
    for key, value in q_data.items():
        setattr(q, key, value)
    
    # 更新选项
    db.query(QuestionOption).filter(QuestionOption.question_id == question_id).delete()
    for opt in q_in.options:
        opt_obj = QuestionOption(question_id=question_id, **opt.model_dump())
        db.add(opt_obj)
    
    db.commit()
    db.refresh(q)
    return q

@router.delete("/{question_id}", dependencies=[Depends(require_admin)])
def delete_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    db.query(QuestionOption).filter(QuestionOption.question_id == question_id).delete()
    db.delete(q)
    db.commit()
    return {"message": "删除成功"}

@router.get("/random/{category_id}", response_model=list[QuestionOut])
def get_random_questions(
    category_id: int,
    count: int = Query(10, ge=1, le=100),
    mode: str = Query("random", description="random=随机练习，order=顺序练习"),
    offset: int = Query(0, ge=0, description="顺序练习时跳过已做的题数"),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(Question).filter(Question.status == 1)

    # category_id 为 0 表示全部题目；为正数时连同其子分类一起取题
    if category_id and category_id > 0:
        child_ids = [
            c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()
        ]
        query = query.filter(Question.category_id.in_([category_id] + child_ids))

    if mode == "order":
        questions = query.order_by(Question.id).offset(offset).limit(count).all()
        if len(questions) == 0 and offset > 0:
            # 已做到末尾，重新从头开始
            questions = query.order_by(Question.id).limit(count).all()
    else:
        questions = query.order_by(func.random()).limit(count).all()
    
    result = []
    for q in questions:
        q_data = QuestionOut.model_validate(q).model_dump()
        options = db.query(QuestionOption).filter(
            QuestionOption.question_id == q.id
        ).order_by(QuestionOption.sort).all()
        # 练习答题时不把正确答案下发给前端，判分统一走 /api/practice/submit
        q_data["options"] = [
            {"id": o.id, "label": o.label, "content": o.content, "is_correct": 0, "sort": o.sort}
            for o in options
        ]
        result.append(q_data)

    return result
