from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import Session
from database import get_db, Base, User
import uuid

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
def report_upload(reported_by: str, upload_id: str, reason: str, db: Session = Depends(get_db)):
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
def get_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.is_resolved == False).all()
    return reports

@router.post("/reports/resolve")
def resolve_report(report_id: str, action_taken: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.is_resolved = True
    report.action_taken = action_taken
    db.commit()
    return {"message": "Report resolved"}