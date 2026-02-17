"""File upload endpoints: CSV, Excel."""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/csv")
async def upload_csv(user=Depends(get_current_user)):
    return {"message": "CSV upload placeholder"}


@router.post("/excel")
async def upload_excel(user=Depends(get_current_user)):
    return {"message": "Excel upload placeholder"}
