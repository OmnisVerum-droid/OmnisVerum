import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import Session

from auth import get_current_user_id, require_admin_key
from database import Base, User, get_db

router = APIRouter()

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True)
    reported_by = Column(String)
    upload_id = Column(String)
    reason = Column(String)
    is_resolved = Column(Boolean, default=False)
    action_taken = Column(String, nullable=True)

@router.post("/report")
def report_upload(
    upload_id: str,
    reason: str,
    reported_by: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == reported_by).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(Report).filter(
        Report.reported_by == reported_by,
        Report.upload_id == upload_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already reported this upload")
    report = Report(
        id=str(uuid.uuid4()),
        reported_by=reported_by,
        upload_id=upload_id,
        reason=reason
    )
    db.add(report)
    db.commit()
    return {"message": "Report submitted successfully"}

@router.get("/reports")
def get_reports(admin_key: str, db: Session = Depends(get_db)):
    require_admin_key(admin_key)
    reports = db.query(Report).filter(Report.is_resolved == False).all()
    return reports

@router.post("/reports/resolve")
def resolve_report(report_id: str, action_taken: str, admin_key: str, db: Session = Depends(get_db)):
    require_admin_key(admin_key)
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.is_resolved = True
    report.action_taken = action_taken
    db.commit()
    return {"message": "Report resolved"}