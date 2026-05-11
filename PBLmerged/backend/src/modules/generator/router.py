from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "../../../generator-service"))

try:
    from generator import generate_pages, regenerate_page
    from model import extract_text_from_upload
    from schemas import PageContent
    GENERATOR_AVAILABLE = True
except ImportError as e:
    GENERATOR_AVAILABLE = False
    IMPORT_ERROR = str(e)

router = APIRouter(prefix="/api/generator", tags=["generator"])


class GenerateRequest(BaseModel):
    description: str
    total_pages: int
    reference_mode: bool = False
    reference_text: str = ""


class RegenerateRequest(BaseModel):
    description: str
    total_pages: int
    page_index: int
    reference_mode: bool = False
    reference_text: str = ""


@router.post("/generate")
def generate(req: GenerateRequest):
    if not GENERATOR_AVAILABLE:
        raise HTTPException(503, f"Generator service unavailable: {IMPORT_ERROR}")
    pages = generate_pages(
        description=req.description,
        total_pages=req.total_pages,
        reference_mode=req.reference_mode,
        reference_text=req.reference_text,
    )
    return {"pages": [p.to_dict() for p in pages]}


@router.post("/regenerate")
def regenerate(req: RegenerateRequest):
    if not GENERATOR_AVAILABLE:
        raise HTTPException(503, f"Generator service unavailable: {IMPORT_ERROR}")
    page = regenerate_page(
        description=req.description,
        total_pages=req.total_pages,
        page_index=req.page_index,
        reference_mode=req.reference_mode,
        reference_text=req.reference_text,
    )
    return page.to_dict()


@router.post("/upload-source")
async def upload_source(file: UploadFile = File(...)):
    if not GENERATOR_AVAILABLE:
        raise HTTPException(503, f"Generator service unavailable: {IMPORT_ERROR}")
    if not file.filename:
        raise HTTPException(400, "No file uploaded")

    data = await file.read()
    extracted_text = extract_text_from_upload(file_name=file.filename, data=data)

    return {
        "file_name": file.filename,
        "reference_text": extracted_text,
        "preview": extracted_text[:1000],
        "message": "参考文件上传成功。",
    }
