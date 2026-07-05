"""供应商资格评审 API - Phase 1"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import json

from app.core.database import get_db
from app.models.supply_chain import (
    QualificationProject, QualificationSubmission, Supplier,
    QualificationStatus
)
from app.schemas.supply_chain import (
    RegistrationCreate, RegistrationResponse
)
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/qualification", tags=["供应商资格评审"])


# ==================== Schemas ====================

class QualificationProjectCreate(BaseModel):
    project_name: str
    target_categories: str
    target_supplier_ids: List[int]
    deadline: Optional[datetime] = None
    notes: Optional[str] = None


class QualificationProjectResponse(BaseModel):
    id: int
    project_name: str
    target_categories: str
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    invited_suppliers: Optional[List[dict]] = None


class QuestionnaireSubmission(BaseModel):
    supplier_id: int
    answers: dict  # 问卷答案 JSON


# ==================== US-104: 创建资格评审项目 ====================

@router.post("/projects", response_model=QualificationProjectResponse)
async def create_qualification_project(
    body: QualificationProjectCreate,
    created_by: int = Query(1),
    db: AsyncSession = Depends(get_db)
):
    """
    创建资格评审项目

    - 从合格供应商库选择目标供应商
    - 自动通知被邀请供应商
    - 支持批量邀请多个供应商
    """
    # 验证所有供应商都存在
    for sid in body.target_supplier_ids:
        supplier_check = await db.execute(
            select(Supplier).where(Supplier.id == sid)
        )
        if not supplier_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"供应商ID {sid} 不存在")

    project = QualificationProject(
        project_name=body.project_name,
        target_categories=body.target_categories,
        deadline=body.deadline,
        status=QualificationStatus.PENDING_RESPONSE,
        created_by=created_by,
        notes=body.notes
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    # 为每个目标供应商创建提交记录
    submissions = []
    for sid in body.target_supplier_ids:
        submission = QualificationSubmission(
            project_id=project.id,
            supplier_id=sid,
            status=QualificationStatus.PENDING_RESPONSE
        )
        db.add(submission)
        submissions.append(submission)

    await db.flush()

    # 返回带供应商信息的项目
    supplier_infos = []
    for sid, sub in zip(body.target_supplier_ids, submissions):
        sup_result = await db.execute(select(Supplier).where(Supplier.id == sid))
        sup = sup_result.scalar_one()
        supplier_infos.append({
            "supplier_id": sid,
            "supplier_name": sup.name,
            "submission_id": sub.id,
            "status": sub.status.value
        })

    return {
        "id": project.id,
        "project_name": project.project_name,
        "target_categories": project.target_categories,
        "deadline": project.deadline,
        "status": project.status.value,
        "created_at": project.created_at,
        "completed_at": project.completed_at,
        "notes": project.notes,
        "invited_suppliers": supplier_infos
    }


@router.get("/projects")
async def list_qualification_projects(
    status: str = Query(None),
    supplier_id: int = Query(None, description="供应商端：仅查看被邀请参与的评审项目 (US-104-2)"),
    db: AsyncSession = Depends(get_db)
):
    """获取资格评审项目列表；采购方看全部，供应商传 supplier_id 过滤"""
    query = select(QualificationProject).order_by(QualificationProject.created_at.desc())
    if status:
        query = query.where(QualificationProject.status == status)
    result = await db.execute(query)
    projects = result.scalars().all()

    response = []
    for p in projects:
        sub_count_result = await db.execute(
            select(QualificationSubmission)
            .where(QualificationSubmission.project_id == p.id)
        )
        submissions = sub_count_result.scalars().all()

        my_submission = None
        if supplier_id is not None:
            my_submission = next(
                (s for s in submissions if s.supplier_id == supplier_id),
                None,
            )
            if not my_submission:
                continue

        accepted = sum(1 for s in submissions if s.status != QualificationStatus.PENDING_RESPONSE)
        item = {
            "id": p.id,
            "project_name": p.project_name,
            "target_categories": p.target_categories,
            "deadline": p.deadline,
            "status": p.status.value,
            "notes": p.notes,
            "created_at": p.created_at,
            "completed_at": p.completed_at,
            "invited_count": len(submissions),
            "accepted_count": accepted,
        }
        if my_submission:
            item["my_status"] = my_submission.status.value
            item["submission_id"] = my_submission.id
        response.append(item)
    return response


@router.get("/projects/{project_id}", response_model=QualificationProjectResponse)
async def get_qualification_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取资格评审项目详情"""
    result = await db.execute(
        select(QualificationProject).where(QualificationProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="评审项目不存在")

    # 获取提交列表
    sub_result = await db.execute(
        select(QualificationSubmission)
        .options(selectinload(QualificationSubmission.supplier))
        .where(QualificationSubmission.project_id == project_id)
    )
    submissions = sub_result.scalars().all()

    supplier_infos = []
    for s in submissions:
        supplier_infos.append({
            "submission_id": s.id,
            "supplier_id": s.supplier_id,
            "supplier_name": s.supplier.name if s.supplier else None,
            "status": s.status.value,
            "final_score": s.final_score,
            "tech_score": s.tech_score,
            "quality_score": s.quality_score,
            "finance_score": s.finance_score
        })

    return {
        "id": project.id,
        "project_name": project.project_name,
        "target_categories": project.target_categories,
        "deadline": project.deadline,
        "status": project.status.value,
        "created_at": project.created_at,
        "completed_at": project.completed_at,
        "notes": project.notes,
        "invited_suppliers": supplier_infos
    }


# ==================== US-105: 供应商提交问卷 ====================

@router.get("/projects/{project_id}/questionnaire")
async def get_questionnaire(
    project_id: int,
    supplier_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """供应商获取资格问卷表单"""
    project_result = await db.execute(
        select(QualificationProject).where(QualificationProject.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="评审项目不存在")

    # 检查供应商是否被邀请
    sub_result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=403, detail="您未被邀请参与此评审项目")

    # 返回问卷模板
    existing_answers = {}
    if submission.questionnaire_answers:
        existing_answers = json.loads(submission.questionnaire_answers)

    questionnaire = {
        "project_id": project.id,
        "project_name": project.project_name,
        "project_notes": project.notes,
        "submission_id": submission.id,
        "deadline": project.deadline,
        "status": submission.status.value,
        "existing_answers": existing_answers,
        "sections": [
            {
                "id": "basic_info",
                "title": "基本信息",
                "fields": [
                    {"id": "company_scale", "label": "企业规模", "type": "select",
                     "options": ["微型(<50人)", "小型(50-200人)", "中型(200-500人)", "大型(>500人)"], "required": True},
                    {"id": "registered_capital", "label": "注册资本(万元)", "type": "number", "required": True},
                    {"id": "annual_revenue", "label": "年营业额(万元)", "type": "number", "required": True},
                    {"id": "main_markets", "label": "主要市场区域", "type": "text", "required": False},
                ]
            },
            {
                "id": "production",
                "title": "生产能力",
                "fields": [
                    {"id": "production_capacity", "label": "年产能(吨)", "type": "number", "required": True},
                    {"id": "production_lines", "label": "生产线数量", "type": "number", "required": True},
                    {"id": "warehouse_capacity", "label": "仓储能力(吨)", "type": "number", "required": True},
                    {"id": "lead_time_days", "label": "常规交期(天)", "type": "number", "required": True},
                ]
            },
            {
                "id": "quality",
                "title": "质量体系",
                "fields": [
                    {"id": "has_iso9001", "label": "是否有ISO9001认证", "type": "select",
                     "options": ["是", "否", "申请中"], "required": True},
                    {"id": "has_iso22000", "label": "是否有ISO22000认证", "type": "select",
                     "options": ["是", "否", "申请中"], "required": True},
                    {"id": "has_haccp", "label": "是否有HACCP认证", "type": "select",
                     "options": ["是", "否", "申请中"], "required": False},
                    {"id": "quality_score_self", "label": "自评质量得分(1-10)", "type": "number", "required": True},
                    {"id": "quality_cert_files", "label": "质量证书上传", "type": "file", "required": False,
                     "note": "支持上传PDF或图片，单文件≤10MB"},
                ]
            },
            {
                "id": "finance",
                "title": "财务状况",
                "fields": [
                    {"id": "latest_revenue", "label": "最近一年营业额(万元)", "type": "number", "required": True},
                    {"id": "latest_profit", "label": "最近一年净利润(万元)", "type": "number", "required": True},
                    {"id": "current_assets", "label": "流动资产(万元)", "type": "number", "required": True},
                    {"id": "current_liabilities", "label": "流动负债(万元)", "type": "number", "required": True},
                    {"id": "has_tax_cert", "label": "是否可提供完税证明", "type": "select",
                     "options": ["是", "否"], "required": True},
                ]
            },
            {
                "id": "cases",
                "title": "合作案例",
                "fields": [
                    {"id": "major_clients", "label": "主要客户(至少3个)", "type": "textarea", "required": True,
                     "note": "请说明客户名称、合作时长、年供货量"},
                    {"id": "has_baijiu_exp", "label": "是否有白酒行业合作经验", "type": "select",
                     "options": ["是(详细说明)", "否"], "required": True},
                    {"id": "cooperation_files", "label": "合作证明材料上传", "type": "file", "required": False},
                ]
            }
        ]
    }
    return questionnaire


@router.post("/projects/{project_id}/submission")
async def submit_questionnaire(
    project_id: int,
    body: QuestionnaireSubmission,
    db: AsyncSession = Depends(get_db)
):
    """供应商提交问卷答案"""
    supplier_id = body.supplier_id
    sub_result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = sub_result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=403, detail="您未被邀请参与此评审项目")

    # 验证状态
    if submission.status not in [QualificationStatus.PENDING_RESPONSE,
                                  QualificationStatus.SUPPLEMENT_MATERIALS,
                                  QualificationStatus.IN_PROGRESS]:
        raise HTTPException(status_code=400, detail="当前状态不允许提交")

    # 保存问卷答案
    submission.questionnaire_answers = json.dumps(body.answers, ensure_ascii=False)
    submission.status = QualificationStatus.IN_PROGRESS
    submission.updated_at = datetime.utcnow()

    # 更新项目状态为评审中（如果所有供应商都已提交）
    project_result = await db.execute(
        select(QualificationProject).where(QualificationProject.id == project_id)
    )
    project = project_result.scalar_one()
    all_submitted = True
    sub_list_result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
    )
    for s in sub_list_result.scalars().all():
        if s.status in [QualificationStatus.PENDING_RESPONSE]:
            all_submitted = False
            break
    if all_submitted:
        project.status = QualificationStatus.IN_PROGRESS

    await db.flush()
    return {
        "success": True,
        "message": "问卷提交成功，等待采购方评审",
        "submission_id": submission.id,
        "status": submission.status.value,
    }


@router.get("/projects/{project_id}/submissions")
async def list_project_submissions(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """采购方查看项目下所有供应商的提交"""
    result = await db.execute(
        select(QualificationSubmission)
        .options(selectinload(QualificationSubmission.supplier))
        .where(QualificationSubmission.project_id == project_id)
    )
    submissions = result.scalars().all()
    return [
        {
            "submission_id": s.id,
            "supplier_id": s.supplier_id,
            "supplier_name": s.supplier.name if s.supplier else None,
            "status": s.status.value,
            "submitted_at": s.updated_at,
            "has_answers": bool(s.questionnaire_answers)
        }
        for s in submissions
    ]


# ==================== US-106: 采购方评审文件 ====================

@router.get("/projects/{project_id}/submissions/{supplier_id}")
async def get_submission_detail(
    project_id: int,
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """采购方查看单个供应商的详细提交"""
    result = await db.execute(
        select(QualificationSubmission)
        .options(selectinload(QualificationSubmission.supplier))
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    answers = {}
    if submission.questionnaire_answers:
        answers = json.loads(submission.questionnaire_answers)

    return {
        "submission_id": submission.id,
        "supplier_id": submission.supplier_id,
        "supplier_name": submission.supplier.name if submission.supplier else None,
        "status": submission.status.value,
        "tech_score": submission.tech_score,
        "quality_score": submission.quality_score,
        "finance_score": submission.finance_score,
        "final_score": submission.final_score,
        "review_opinions": submission.review_opinions,
        "clarification_requests": json.loads(submission.clarification_requests) if submission.clarification_requests else [],
        "answers": answers,
        "updated_at": submission.updated_at
    }


class ReviewSubmitRequest(BaseModel):
    reviewer_id: int = 1
    tech_score: Optional[float] = None
    quality_score: Optional[float] = None
    finance_score: Optional[float] = None
    opinions: Optional[str] = None
    clarification_message: Optional[str] = None


@router.post("/projects/{project_id}/submissions/{supplier_id}/review")
async def submit_review(
    project_id: int,
    supplier_id: int,
    body: ReviewSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    """采购方提交评审意见"""
    reviewer_id = body.reviewer_id
    result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    # 更新评分
    if body.tech_score is not None:
        submission.tech_score = min(100, max(0, body.tech_score))
    if body.quality_score is not None:
        submission.quality_score = min(100, max(0, body.quality_score))
    if body.finance_score is not None:
        submission.finance_score = min(100, max(0, body.finance_score))

    # 计算综合得分
    scores = []
    weights = []
    if submission.tech_score is not None:
        scores.append(submission.tech_score); weights.append(0.4)
    if submission.quality_score is not None:
        scores.append(submission.quality_score); weights.append(0.3)
    if submission.finance_score is not None:
        scores.append(submission.finance_score); weights.append(0.3)

    if scores:
        total_weight = sum(weights)
        submission.final_score = sum(s * w for s, w in zip(scores, weights)) / total_weight

    # 评审意见
    existing_opinions = []
    if submission.review_opinions:
        existing_opinions = json.loads(submission.review_opinions)
    existing_opinions.append({
        "reviewer_id": reviewer_id,
        "timestamp": datetime.utcnow().isoformat(),
        "tech_score": body.tech_score,
        "quality_score": body.quality_score,
        "finance_score": body.finance_score,
        "opinions": body.opinions
    })
    submission.review_opinions = json.dumps(existing_opinions, ensure_ascii=False)
    submission.reviewed_by = reviewer_id
    submission.reviewed_at = datetime.utcnow()

    # 澄清请求
    if body.clarification_message:
        clarifications = []
        if submission.clarification_requests:
            clarifications = json.loads(submission.clarification_requests)
        clarifications.append({
            "from": "buyer",
            "message": body.clarification_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        submission.clarification_requests = json.dumps(clarifications, ensure_ascii=False)
        submission.status = QualificationStatus.SUPPLEMENT_MATERIALS

    await db.flush()
    return {"success": True, "message": "评审意见已提交", "final_score": submission.final_score}


# ==================== US-107: 最终审批 ====================

@router.post("/projects/{project_id}/approve")
async def approve_qualification(
    project_id: int,
    supplier_id: int,
    approver_id: int = Query(1),
    opinion: str = Query(""),
    db: AsyncSession = Depends(get_db)
):
    """采购方最终审批通过供应商资格"""
    result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    submission.status = QualificationStatus.APPROVED
    submission.reviewed_by = approver_id
    submission.reviewed_at = datetime.utcnow()

    # 将供应商状态更新为 qualified
    from app.models.supply_chain import SupplierStatus
    supplier_result = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = supplier_result.scalar_one()
    supplier.status = SupplierStatus.ACTIVE

    # 检查项目是否全部完成
    all_done = True
    sub_result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
    )
    for s in sub_result.scalars().all():
        if s.status not in [QualificationStatus.APPROVED, QualificationStatus.REJECTED]:
            all_done = False
            break

    project_result = await db.execute(
        select(QualificationProject).where(QualificationProject.id == project_id)
    )
    project = project_result.scalar_one()
    if all_done:
        project.status = QualificationStatus.APPROVED
        project.completed_at = datetime.utcnow()

    await db.flush()
    return {"success": True, "message": f"供应商【{supplier.name}】资格审批通过，已纳入合格供应商库"}


@router.post("/projects/{project_id}/reject")
async def reject_qualification(
    project_id: int,
    supplier_id: int,
    approver_id: int = Query(1),
    reason: str = Query(""),
    db: AsyncSession = Depends(get_db)
):
    """采购方审批不通过"""
    result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    submission.status = QualificationStatus.REJECTED
    submission.reviewed_by = approver_id
    submission.reviewed_at = datetime.utcnow()

    # 添加驳回意见
    existing_opinions = []
    if submission.review_opinions:
        existing_opinions = json.loads(submission.review_opinions)
    existing_opinions.append({
        "type": "final_rejection",
        "reviewer_id": approver_id,
        "timestamp": datetime.utcnow().isoformat(),
        "reason": reason
    })
    submission.review_opinions = json.dumps(existing_opinions, ensure_ascii=False)

    await db.flush()
    return {"success": True, "message": "资格申请已驳回"}


@router.get("/projects/{project_id}/status")
async def get_project_status(
    project_id: int,
    supplier_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """供应商查询自己的资格申请状态"""
    result = await db.execute(
        select(QualificationSubmission)
        .where(QualificationSubmission.project_id == project_id)
        .where(QualificationSubmission.supplier_id == supplier_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="未找到提交记录")

    clarifications = []
    if submission.clarification_requests:
        clarifications = json.loads(submission.clarification_requests)

    return {
        "submission_id": submission.id,
        "status": submission.status.value,
        "final_score": submission.final_score,
        "tech_score": submission.tech_score,
        "quality_score": submission.quality_score,
        "finance_score": submission.finance_score,
        "clarifications": clarifications,
        "has_final_result": submission.status in [
            QualificationStatus.APPROVED, QualificationStatus.REJECTED
        ]
    }
