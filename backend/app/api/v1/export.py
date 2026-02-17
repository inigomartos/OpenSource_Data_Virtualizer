"""Export endpoints: PDF, Excel."""

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.export import ExportRequest
from app.services.export_service import ExportService

router = APIRouter()
export_service = ExportService()


def _validate_export_data(data: dict) -> tuple[list[str], list[list]]:
    """Validate and extract columns and rows from export data dict."""
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="data must be a dict with 'columns' and 'rows' keys",
        )

    columns = data.get("columns")
    rows = data.get("rows")

    if not isinstance(columns, list) or not all(isinstance(c, str) for c in columns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="data.columns must be a list of strings",
        )

    if not isinstance(rows, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="data.rows must be a list of lists",
        )

    return columns, rows


@router.post("/pdf")
async def export_pdf(
    request: ExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a PDF report from query results."""
    columns, rows = _validate_export_data(request.data)

    pdf_bytes = await export_service.export_pdf(
        title=request.title,
        insight=request.insight or "",
        columns=columns,
        rows=rows,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"datamind_export_{timestamp}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/excel")
async def export_excel(
    request: ExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download an Excel workbook from query results."""
    columns, rows = _validate_export_data(request.data)

    excel_bytes = await export_service.export_excel(
        title=request.title,
        insight=request.insight or "",
        columns=columns,
        rows=rows,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"datamind_export_{timestamp}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
