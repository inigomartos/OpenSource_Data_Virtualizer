"""Export endpoints: PDF, Excel."""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/pdf")
async def export_pdf(user=Depends(get_current_user)):
    return {"message": "PDF export placeholder"}


@router.post("/excel")
async def export_excel(user=Depends(get_current_user)):
    return {"message": "Excel export placeholder"}
