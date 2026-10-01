from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
from pipelines.interview_pipeline import (
    extract_and_profile_resume,
    start_interview_session,
    submit_candidate_answer,
    generate_evaluation_report,
)

router = APIRouter(prefix="/api/interview", tags=["interview"])


class StartInterviewRequest(BaseModel):
    profile: Dict[str, Any]
    interview_type: str = "Technical Interview"
    target_role: str = "AI Engineer"
    difficulty: str = "Mid-Level"
    total_questions: int = 5


class SubmitAnswerRequest(BaseModel):
    session: Dict[str, Any]
    answer: str


class EvaluateRequest(BaseModel):
    session: Dict[str, Any]


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        profile = await asyncio.to_thread(extract_and_profile_resume, contents, file.filename)
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/start")
async def start_interview(req: StartInterviewRequest):
    try:
        session = await asyncio.to_thread(
            start_interview_session,
            req.profile,
            req.interview_type,
            req.target_role,
            req.difficulty,
            req.total_questions,
        )
        return {"success": True, "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer")
async def submit_answer(req: SubmitAnswerRequest):
    try:
        if not req.answer or not req.answer.strip():
            raise HTTPException(status_code=400, detail="Answer cannot be empty.")
        updated_session = await asyncio.to_thread(
            submit_candidate_answer,
            req.session,
            req.answer,
        )
        return {"success": True, "session": updated_session}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate(req: EvaluateRequest):
    try:
        report = await asyncio.to_thread(generate_evaluation_report, req.session)
        return {"success": True, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))