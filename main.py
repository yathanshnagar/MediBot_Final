"""
FastAPI backend for Medical Llama system
"""
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db, init_db, User, Patient, Interaction, MedicalEvent, Consultation, Hospital, Doctor, Appointment, Notification
from workflow import MedicalWorkflow
from config import SeverityLevel, CarePathway
import json

# Initialize
init_db()
app = FastAPI(
    title="Medical Llama API",
    description="Patient-facing medical triage and care recommendation chatbot",
    version="1.0.0"
)

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for local development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

workflow = MedicalWorkflow()

# Get current directory
BASE_DIR = Path(__file__).resolve().parent

# ============================================================================
# Request/Response Models
# ============================================================================

# Helper functions for password hashing
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def generate_token() -> str:
    """Generate a simple auth token"""
    return secrets.token_urlsafe(32)

# Auth Models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    age: int
    gender: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    age: int
    gender: str
    created_at: datetime

    model_config = {"from_attributes": True}

class LoginResponse(BaseModel):
    user: UserResponse
    token: str
    message: str

class MedicalHistoryItem(BaseModel):
    id: int
    timestamp: datetime
    chief_complaint: Optional[str]
    symptoms: Optional[str]
    duration: Optional[str]
    temperature: Optional[float]
    severity: str
    confidence: float
    diagnosis: List[str]
    medications: List[str]
    self_care: List[str]
    recommendations: Optional[str]
    full_conversation: Optional[str]
    care_pathway: Optional[str]

    model_config = {"from_attributes": True}

class PatientProfile(BaseModel):
    patient_id: str
    name: str
    age: int
    medical_history: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    notification_preferences: Optional[dict] = None

    model_config = {"from_attributes": True}

class MediaAttachment(BaseModel):
    type: str  # 'image', 'audio', 'file'
    data: str  # Base64 encoded data
    name: str  # Original filename
    size: Optional[int] = None  # File size in bytes

class ChatMessage(BaseModel):
    patient_id: str
    message: str
    include_history: bool = True
    media: Optional[List[MediaAttachment]] = None

class TriageResponse(BaseModel):
    severity: str
    confidence: float
    recommendation: str
    suggested_actions: List[str]
    disclaimer: str
    needs_escalation: bool
    care_pathway: Optional[dict] = None
    action_plan: Optional[dict] = None

class ConversationHistory(BaseModel):
    patient_id: str
    user: str
    assistant: str
    timestamp: datetime
    severity: Optional[str] = None

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/signup", response_model=UserResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        age=request.age,
        gender=request.gender
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user"""
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate token
    token = generate_token()
    
    return LoginResponse(
        user=UserResponse.model_validate(user),
        token=token,
        message="Login successful"
    )

@app.get("/users/{user_id}/medical-history", response_model=List[MedicalHistoryItem])
def get_medical_history(user_id: int, db: Session = Depends(get_db)):
    """Get user's medical history"""
    consultations = db.query(Consultation).filter(
        Consultation.user_id == user_id
    ).order_by(Consultation.timestamp.desc()).all()
    
    return [
        MedicalHistoryItem(
            id=c.id,
            timestamp=c.timestamp,
            chief_complaint=c.chief_complaint,
            symptoms=c.symptoms,
            duration=c.duration,
            temperature=c.temperature,
            severity=c.severity,
            confidence=c.confidence,
            diagnosis=json.loads(c.diagnosis) if c.diagnosis else [],
            medications=json.loads(c.medications) if c.medications else [],
            self_care=json.loads(c.self_care) if c.self_care else [],
            recommendations=c.recommendations,
            full_conversation=c.full_conversation,
            care_pathway=c.care_pathway
        )
        for c in consultations
    ]

class ConsultationRequest(BaseModel):
    user_id: int
    patient_id: str
    chief_complaint: str
    symptoms: str
    duration: Optional[str] = None
    temperature: Optional[float] = None
    severity: str
    confidence: float
    diagnosis: str  # JSON string
    medications: str  # JSON string
    self_care: str  # JSON string
    recommendations: str
    full_conversation: str
    care_pathway: Optional[str] = None

@app.post("/consultations/save")
def save_consultation(consultation: ConsultationRequest, db: Session = Depends(get_db)):
    """Save a consultation to medical history"""
    new_consultation = Consultation(
        user_id=consultation.user_id,
        patient_id=consultation.patient_id,
        chief_complaint=consultation.chief_complaint,
        symptoms=consultation.symptoms,
        duration=consultation.duration,
        temperature=consultation.temperature,
        severity=consultation.severity,
        confidence=consultation.confidence,
        diagnosis=consultation.diagnosis,
        medications=consultation.medications,
        self_care=consultation.self_care,
        recommendations=consultation.recommendations,
        full_conversation=consultation.full_conversation,
        care_pathway=consultation.care_pathway
    )
    
    db.add(new_consultation)
    db.commit()
    db.refresh(new_consultation)
    
    return {"message": "Consultation saved successfully", "id": new_consultation.id}

# ============================================================================
# Appointment & Booking Endpoints
# ============================================================================

class HospitalResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    distance_km: float
    phone: str
    specialties: List[str]
    rating: float
    accepts_emergency: bool

    model_config = {"from_attributes": True}

class DoctorResponse(BaseModel):
    id: int
    hospital_id: int
    name: str
    specialization: str
    qualifications: str
    experience_years: int
    rating: float
    consultation_fee: float
    availability: dict
    photo_url: Optional[str]

    model_config = {"from_attributes": True}

class AppointmentRequest(BaseModel):
    user_id: int
    consultation_id: Optional[int] = None
    doctor_id: int
    hospital_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    reason: str
    symptoms: Optional[str] = None
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    user_id: int
    doctor_id: int
    hospital_id: int
    appointment_date: datetime
    duration_minutes: int
    reason: str
    symptoms: Optional[str]
    status: str
    created_at: datetime
    doctor_name: str
    doctor_specialization: str
    hospital_name: str
    hospital_address: str

    model_config = {"from_attributes": True}

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}

@app.get("/hospitals", response_model=List[HospitalResponse])
def get_hospitals(db: Session = Depends(get_db)):
    """Get list of nearby hospitals"""
    hospitals = db.query(Hospital).order_by(Hospital.distance_km).all()
    
    return [
        HospitalResponse(
            id=h.id,
            name=h.name,
            address=h.address,
            city=h.city,
            distance_km=h.distance_km,
            phone=h.phone,
            specialties=json.loads(h.specialties) if h.specialties else [],
            rating=h.rating,
            accepts_emergency=h.accepts_emergency
        )
        for h in hospitals
    ]

@app.get("/hospitals/{hospital_id}/doctors", response_model=List[DoctorResponse])
def get_hospital_doctors(hospital_id: int, specialization: Optional[str] = None, db: Session = Depends(get_db)):
    """Get doctors at a specific hospital"""
    query = db.query(Doctor).filter(Doctor.hospital_id == hospital_id)
    
    if specialization:
        query = query.filter(Doctor.specialization == specialization)
    
    doctors = query.order_by(Doctor.rating.desc()).all()
    
    return [
        DoctorResponse(
            id=d.id,
            hospital_id=d.hospital_id,
            name=d.name,
            specialization=d.specialization,
            qualifications=d.qualifications,
            experience_years=d.experience_years,
            rating=d.rating,
            consultation_fee=d.consultation_fee,
            availability=json.loads(d.availability) if d.availability else {},
            photo_url=d.photo_url
        )
        for d in doctors
    ]

@app.post("/appointments/book")
def book_appointment(appointment: AppointmentRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Book a new appointment"""
    # Create appointment
    new_appointment = Appointment(
        user_id=appointment.user_id,
        consultation_id=appointment.consultation_id,
        doctor_id=appointment.doctor_id,
        hospital_id=appointment.hospital_id,
        appointment_date=appointment.appointment_date,
        duration_minutes=appointment.duration_minutes,
        reason=appointment.reason,
        symptoms=appointment.symptoms,
        notes=appointment.notes,
        status='scheduled'
    )
    
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    
    # Get doctor and hospital details
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    hospital = db.query(Hospital).filter(Hospital.id == appointment.hospital_id).first()
    
    # Create booking confirmation notification
    notification = Notification(
        user_id=appointment.user_id,
        appointment_id=new_appointment.id,
        type='booking_confirmation',
        title='Appointment Booked Successfully! 🎉',
        message=f'Your appointment with Dr. {doctor.name} at {hospital.name} has been scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.'
    )
    
    db.add(notification)
    new_appointment.reminder_sent_booking = True
    db.commit()
    
    return {
        "message": "Appointment booked successfully",
        "appointment_id": new_appointment.id,
        "appointment_date": new_appointment.appointment_date,
        "doctor": doctor.name,
        "hospital": hospital.name
    }

@app.get("/appointments/user/{user_id}", response_model=List[AppointmentResponse])
def get_user_appointments(user_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get user's appointments"""
    query = db.query(Appointment).filter(Appointment.user_id == user_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    appointments = query.order_by(Appointment.appointment_date).all()
    
    result = []
    for appt in appointments:
        doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        hospital = db.query(Hospital).filter(Hospital.id == appt.hospital_id).first()
        
        result.append(AppointmentResponse(
            id=appt.id,
            user_id=appt.user_id,
            doctor_id=appt.doctor_id,
            hospital_id=appt.hospital_id,
            appointment_date=appt.appointment_date,
            duration_minutes=appt.duration_minutes,
            reason=appt.reason,
            symptoms=appt.symptoms,
            status=appt.status,
            created_at=appt.created_at,
            doctor_name=doctor.name if doctor else "Unknown",
            doctor_specialization=doctor.specialization if doctor else "Unknown",
            hospital_name=hospital.name if hospital else "Unknown",
            hospital_address=hospital.address if hospital else "Unknown"
        ))
    
    return result

@app.get("/notifications/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: int, unread_only: bool = False, db: Session = Depends(get_db)):
    """Get user's notifications"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.read == False)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            title=n.title,
            message=n.message,
            read=n.read,
            created_at=n.created_at
        )
        for n in notifications
    ]

@app.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

@app.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Cancel an appointment"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment.status = 'cancelled'
    appointment.updated_at = datetime.utcnow()
    db.commit()
    
    # Create cancellation notification
    notification = Notification(
        user_id=appointment.user_id,
        appointment_id=appointment.id,
        type='general',
        title='Appointment Cancelled',
        message=f'Your appointment scheduled for {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")} has been cancelled.'
    )
    
    db.add(notification)
    db.commit()
    
    return {"message": "Appointment cancelled successfully"}

# Background task to check for upcoming appointments and send reminders
def check_appointment_reminders(db: Session):
    """Check for appointments needing reminders"""
    now = datetime.utcnow()
    one_hour_from_now = now + timedelta(hours=1)
    one_day_from_now = now + timedelta(days=1)
    
    # Get appointments that need 1-hour reminders
    appointments_1hour = db.query(Appointment).filter(
        Appointment.status == 'scheduled',
        Appointment.appointment_date <= one_hour_from_now,
        Appointment.appointment_date > now,
        Appointment.reminder_sent_1hour == False
    ).all()
    
    for appt in appointments_1hour:
        doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        hospital = db.query(Hospital).filter(Hospital.id == appt.hospital_id).first()
        
        notification = Notification(
            user_id=appt.user_id,
            appointment_id=appt.id,
            type='appointment_reminder',
            title='⏰ Appointment Reminder - 1 Hour',
            message=f'Your appointment with Dr. {doctor.name} at {hospital.name} is in 1 hour! Don\'t forget to bring any relevant medical documents.'
        )
        
        db.add(notification)
        appt.reminder_sent_1hour = True
    
    # Get appointments that need 1-day reminders
    appointments_1day = db.query(Appointment).filter(
        Appointment.status == 'scheduled',
        Appointment.appointment_date <= one_day_from_now,
        Appointment.appointment_date > one_hour_from_now,
        Appointment.reminder_sent_1day == False
    ).all()
    
    for appt in appointments_1day:
        doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        hospital = db.query(Hospital).filter(Hospital.id == appt.hospital_id).first()
        
        notification = Notification(
            user_id=appt.user_id,
            appointment_id=appt.id,
            type='appointment_reminder',
            title='📅 Appointment Reminder - Tomorrow',
            message=f'Your appointment with Dr. {doctor.name} at {hospital.name} is scheduled for tomorrow at {appt.appointment_date.strftime("%I:%M %p")}.'
        )
        
        db.add(notification)
        appt.reminder_sent_1day = True
    
    db.commit()

@app.get("/check-reminders")
def trigger_reminder_check(db: Session = Depends(get_db)):
    """Manually trigger reminder check (can be called by a cron job)"""
    check_appointment_reminders(db)
    return {"message": "Reminder check completed"}

# ============================================================================
# Patient Management Endpoints
# ============================================================================

@app.post("/patients/register", response_model=PatientProfile)
def register_patient(profile: PatientProfile, db: Session = Depends(get_db)):
    """Register a new patient"""
    # Check if patient already exists
    existing = db.query(Patient).filter(Patient.patient_id == profile.patient_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient already registered")
    
    patient = Patient(
        patient_id=profile.patient_id,
        name=profile.name,
        age=profile.age,
        medical_history=json.dumps(profile.medical_history or []),
        allergies=json.dumps(profile.allergies or []),
        current_medications=json.dumps(profile.current_medications or []),
        notification_preferences=json.dumps(profile.notification_preferences or {}),
    )
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # Return with parsed JSON
    return PatientProfile(
        patient_id=patient.patient_id,
        name=patient.name,
        age=patient.age,
        medical_history=profile.medical_history or [],
        allergies=profile.allergies or [],
        current_medications=profile.current_medications or [],
        notification_preferences=profile.notification_preferences or {}
    )

@app.get("/patients/{patient_id}", response_model=PatientProfile)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get patient profile"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Parse JSON fields
    return PatientProfile(
        patient_id=patient.patient_id,
        name=patient.name,
        age=patient.age,
        medical_history=json.loads(patient.medical_history) if patient.medical_history else [],
        allergies=json.loads(patient.allergies) if patient.allergies else [],
        current_medications=json.loads(patient.current_medications) if patient.current_medications else [],
        notification_preferences=json.loads(patient.notification_preferences) if patient.notification_preferences else {}
    )

@app.put("/patients/{patient_id}", response_model=PatientProfile)
def update_patient(patient_id: str, profile: PatientProfile, db: Session = Depends(get_db)):
    """Update patient profile"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient.name = profile.name
    patient.age = profile.age
    patient.medical_history = json.dumps(profile.medical_history or [])
    patient.allergies = json.dumps(profile.allergies or [])
    patient.current_medications = json.dumps(profile.current_medications or [])
    patient.notification_preferences = json.dumps(profile.notification_preferences or {})
    patient.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(patient)
    
    # Return with parsed JSON
    return PatientProfile(
        patient_id=patient.patient_id,
        name=patient.name,
        age=patient.age,
        medical_history=profile.medical_history or [],
        allergies=profile.allergies or [],
        current_medications=profile.current_medications or [],
        notification_preferences=profile.notification_preferences or {}
    )

# ============================================================================
# Conversation/Triage Endpoints
# ============================================================================

@app.post("/chat/triage", response_model=TriageResponse)
def triage_patient(
    chat: ChatMessage,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Run medical triage on patient input with optional media attachments
    """
    try:
        # Get patient profile
        patient = db.query(Patient).filter(Patient.patient_id == chat.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Process media attachments if present
        media_info = ""
        if chat.media and len(chat.media) > 0:
            media_types = []
            for media in chat.media:
                media_types.append(f"{media.type} ({media.name})")
            
            media_info = f"\n\n[Patient attached {len(chat.media)} file(s): {', '.join(media_types)}]"
            print(f"\n=== MEDIA ATTACHMENTS ===")
            print(f"Count: {len(chat.media)}")
            for idx, media in enumerate(chat.media):
                print(f"  [{idx+1}] Type: {media.type}, Name: {media.name}, Size: {media.size} bytes")
            print(f"========================\n")
        
        # Append media info to message for LLM context
        enhanced_message = chat.message + media_info
        
        # Get conversation history if requested
        conversation_history = []
        if chat.include_history:
            interactions = db.query(Interaction).filter(
                Interaction.patient_id == chat.patient_id
            ).order_by(Interaction.timestamp.desc()).limit(5).all()
            
            conversation_history = [
                {
                    "user": i.user_message,
                    "assistant": i.assistant_response
                }
                for i in reversed(interactions)
            ]
        
        # Run workflow with enhanced message
        result = workflow.run(
            patient_id=chat.patient_id,
            user_input=enhanced_message,
            conversation_history=conversation_history
        )
        
        # Debug: Check if result is None
        if result is None:
            print(f"\n=== WARNING: Workflow returned None ===")
            raise HTTPException(status_code=500, detail="Workflow returned no result")
        
        print(f"\n=== WORKFLOW RESULT ===")
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        print(f"Triage result: {result.get('triage_result', 'Missing') if isinstance(result, dict) else 'N/A'}")
        print(f"======================\n")
        
        # Store interaction in database (background task)
        def store_interaction():
            try:
                # Create message with media metadata
                stored_message = chat.message
                if chat.media and len(chat.media) > 0:
                    media_summary = f" [+{len(chat.media)} attachment(s)]"
                    stored_message += media_summary
                
                interaction = Interaction(
                    interaction_id=str(uuid.uuid4()),
                    patient_id=chat.patient_id,
                    user_message=stored_message,
                    assistant_response=str(result.get("action_plan", {})),
                    severity=result.get("severity"),
                    confidence=result.get("confidence", 0.5),
                    care_pathway=result.get("recommended_pathway"),
                    escalated=result.get("needs_escalation", False),
                    escalation_reason=result.get("error"),
                )
                db.add(interaction)
                
                # If escalated, also create medical event
                if result.get("needs_escalation"):
                    event = MedicalEvent(
                        event_id=str(uuid.uuid4()),
                        patient_id=chat.patient_id,
                        event_type="escalation" if not result.get("is_emergency") else "emergency",
                        description=stored_message,
                        severity=result.get("severity"),
                        action_taken=str(result.get("action_plan", {})),
                    )
                    db.add(event)
                
                db.commit()
            except Exception as e:
                print(f"Error storing interaction: {e}")
                db.rollback()
        
        if background_tasks:
            background_tasks.add_task(store_interaction)
        else:
            store_interaction()
        
        # Format response - handle conversational flow
        triage_result = result.get("triage_result", {})
        
        # For conversational responses (needs_more_info), use appropriate defaults
        if triage_result.get("needs_more_info", False):
            return TriageResponse(
                severity="unknown",  # Not yet determined
                confidence=1.0,  # High confidence in asking the question
                recommendation=triage_result.get("recommendation", "Please provide more details"),
                suggested_actions=triage_result.get("suggested_actions") or [],  # Handle None
                disclaimer=triage_result.get("disclaimer", "This is not medical advice. Always consult a healthcare provider."),
                needs_escalation=False,  # Don't escalate during information gathering
                care_pathway=None,
                action_plan=None,
            )
        
        # For complete triage responses
        return TriageResponse(
            severity=result.get("severity", triage_result.get("severity", "referral")),
            confidence=result.get("confidence", triage_result.get("confidence", 0.5)),
            recommendation=triage_result.get("recommendation", "Please consult a healthcare provider"),
            suggested_actions=triage_result.get("suggested_actions") or [],  # Handle None
            disclaimer=triage_result.get("disclaimer", "This is not medical advice. Always consult a healthcare provider."),
            needs_escalation=result.get("needs_escalation", False),
            care_pathway=result.get("care_pathway"),
            action_plan=result.get("action_plan"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"\n=== TRIAGE ERROR ===")
        print(error_details)
        print(f"===================\n")
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")

@app.get("/chat/history/{patient_id}", response_model=List[ConversationHistory])
def get_conversation_history(patient_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get conversation history for a patient"""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    interactions = db.query(Interaction).filter(
        Interaction.patient_id == patient_id
    ).order_by(Interaction.timestamp.desc()).limit(limit).all()
    
    return [
        ConversationHistory(
            patient_id=i.patient_id,
            user=i.user_message,
            assistant=i.assistant_response,
            timestamp=i.timestamp,
            severity=i.severity,
        )
        for i in reversed(interactions)
    ]

# ============================================================================
# Health and Info Endpoints
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "medical-llama"}

@app.get("/info")
def service_info():
    """Service information"""
    return {
        "name": "Medical Llama",
        "version": "1.0.0",
        "model": "BioMistral 7B",
        "description": "Patient-facing medical triage and care recommendation chatbot",
    }

# ============================================================================
# HTML Page Routes
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the login/signup page"""
    file_path = BASE_DIR / "auth.html"
    if file_path.exists():
        return FileResponse(file_path)
    return HTMLResponse("<h1>Medical Llama</h1><p>auth.html not found</p>")

@app.get("/dashboard", response_class=HTMLResponse)
def read_dashboard():
    """Serve the dashboard page"""
    file_path = BASE_DIR / "dashboard.html"
    if file_path.exists():
        return FileResponse(file_path)
    return HTMLResponse("<h1>Dashboard not found</h1>")

@app.get("/chat", response_class=HTMLResponse)
def read_chat():
    """Serve the chat UI page"""
    file_path = BASE_DIR / "chat_ui.html"
    if file_path.exists():
        return FileResponse(file_path)
    return HTMLResponse("<h1>Chat UI not found</h1>")

@app.get("/history", response_class=HTMLResponse)
def read_history():
    """Serve the medical history page"""
    file_path = BASE_DIR / "medical_history.html"
    if file_path.exists():
        return FileResponse(file_path)
    return HTMLResponse("<h1>Medical History not found</h1>")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🏥 Medical Llama - AI Health Assistant")
    print("="*60)
    print("\n🚀 Server starting...")
    print(f"\n📍 Access the application at:")
    print(f"   http://localhost:8000")
    print(f"\n📄 Available pages:")
    print(f"   • Login/Signup:     http://localhost:8000/")
    print(f"   • Dashboard:        http://localhost:8000/dashboard")
    print(f"   • Chat:             http://localhost:8000/chat")
    print(f"   • Medical History:  http://localhost:8000/history")
    print(f"\n🔧 API Documentation:")
    print(f"   http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
