import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import User, Upload, Report, Server, ServerMember, get_db
from auth import get_current_user_id, require_admin_key

router = APIRouter()


class ReportBody(BaseModel):
    reported_user_id: str = None
    reported_upload_id: str = None
    server_id: str
    reason: str
    description: str = ""


@router.post("/report")
def create_report(
    body: ReportBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a report against a user or upload."""
    if not body.reason or not body.reason.strip():
        raise HTTPException(status_code=400, detail="Reason is required")
    
    if not body.reported_user_id and not body.reported_upload_id:
        raise HTTPException(status_code=400, detail="Must report either a user or an upload")
    
    # Check if server exists
    server = db.query(Server).filter(Server.id == body.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if user is a server member
    member = db.query(ServerMember).filter(
        ServerMember.server_id == body.server_id,
        ServerMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="You must be a server member to create reports")
    
    # Validate target exists
    if body.reported_user_id:
        target_user = db.query(User).filter(User.id == body.reported_user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Reported user not found")
    
    if body.reported_upload_id:
        target_upload = db.query(Upload).filter(Upload.id == body.reported_upload_id).first()
        if not target_upload:
            raise HTTPException(status_code=404, detail="Reported upload not found")
    
    report = Report(
        id=str(uuid.uuid4()),
        reporter_id=user_id,
        reported_user_id=body.reported_user_id,
        reported_upload_id=body.reported_upload_id,
        server_id=body.server_id,
        reason=body.reason.strip()[:100],
        description=body.description.strip()[:500],
    )
    
    db.add(report)
    db.commit()
    
    return {"report_id": report.id, "message": "Report submitted successfully"}


@router.get("/reports/{server_id}")
def get_server_reports(
    server_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get all reports for a server (for admins)."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if user is server owner
    if server.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only server owner can view reports")
    
    reports = db.query(Report).filter(Report.server_id == server_id).all()
    
    result = []
    for report in reports:
        reporter = db.query(User).filter(User.id == report.reporter_id).first()
        reported_user = None
        if report.reported_user_id:
            reported_user = db.query(User).filter(User.id == report.reported_user_id).first()
        reported_upload = None
        if report.reported_upload_id:
            reported_upload = db.query(Upload).filter(Upload.id == report.reported_upload_id).first()
        
        result.append({
            "id": report.id,
            "reporter": {
                "id": reporter.id,
                "username": reporter.username
            } if reporter else None,
            "reported_user": {
                "id": reported_user.id,
                "username": reported_user.username
            } if reported_user else None,
            "reported_upload": {
                "id": reported_upload.id,
                "content": reported_upload.content[:100] + "..."
            } if reported_upload else None,
            "reason": report.reason,
            "description": report.description,
            "is_resolved": report.is_resolved,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M"),
            "resolved_at": report.resolved_at.strftime("%Y-%m-%d %H:%M") if report.resolved_at else None,
        })
    
    return {"server_id": server_id, "reports": result}


@router.post("/reports/{report_id}/resolve")
def resolve_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Resolve a report (for server owners)."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if user is server owner
    server = db.query(Server).filter(Server.id == report.server_id).first()
    if not server or server.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only server owner can resolve reports")
    
    if report.is_resolved:
        raise HTTPException(status_code=400, detail="Report already resolved")
    
    report.is_resolved = True
    report.resolved_by = user_id
    report.resolved_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Report resolved successfully"}
