"""
Database models for patient profiles and conversation history
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    """User account"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    age = Column(Integer)
    gender = Column(String(20))
    phone = Column(String(20))
    medical_history = Column(Text)  # JSON string of medical conditions
    allergies = Column(Text)  # JSON string
    current_medications = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

class Patient(Base):
    """Patient profile"""
    __tablename__ = "patients"
    
    patient_id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # Link to user account
    name = Column(String(100))
    age = Column(Integer)
    medical_history = Column(Text)  # JSON string of medical conditions
    allergies = Column(Text)  # JSON string
    current_medications = Column(Text)  # JSON string
    preferred_language = Column(String(20), default="en")
    notification_preferences = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Consultation(Base):
    """Medical consultation record"""
    __tablename__ = "consultations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    patient_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    chief_complaint = Column(String(500))  # Main symptom/reason
    symptoms = Column(Text)  # Detailed symptoms
    duration = Column(String(100))  # How long symptoms lasted
    temperature = Column(Float)  # Body temperature if provided
    severity = Column(String(50))  # self_care, referral, urgent, emergency
    confidence = Column(Float)  # 0.0 - 1.0
    diagnosis = Column(Text)  # JSON array of possible conditions
    medications = Column(Text)  # JSON array of prescribed medications
    self_care = Column(Text)  # JSON array of self-care actions
    recommendations = Column(Text)  # Doctor's recommendations
    full_conversation = Column(Text)  # Complete chat history
    care_pathway = Column(String(100))
    resolved = Column(Boolean, default=False)

class Interaction(Base):
    """Conversation/interaction history"""
    __tablename__ = "interactions"
    
    interaction_id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_message = Column(Text)
    assistant_response = Column(Text)
    severity = Column(String(50))  # self_care, referral, urgent, emergency
    confidence = Column(Float)  # 0.0 - 1.0
    care_pathway = Column(String(100))
    action_taken = Column(String(200))
    escalated = Column(Boolean, default=False)
    escalation_reason = Column(Text)

class MedicalEvent(Base):
    """Track medical events/escalations"""
    __tablename__ = "medical_events"
    
    event_id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50))  # emergency, escalation, referral, etc.
    description = Column(Text)
    severity = Column(String(50))
    action_taken = Column(Text)
    resolved = Column(Boolean, default=False)

class Hospital(Base):
    """Hospital/Clinic information"""
    __tablename__ = "hospitals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    city = Column(String(100))
    distance_km = Column(Float)  # Distance from user
    phone = Column(String(20))
    specialties = Column(Text)  # JSON array of specialties
    rating = Column(Float)  # 1.0 - 5.0
    accepts_emergency = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Doctor(Base):
    """Doctor information"""
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    specialization = Column(String(100))
    qualifications = Column(String(500))
    experience_years = Column(Integer)
    rating = Column(Float)  # 1.0 - 5.0
    consultation_fee = Column(Float)
    availability = Column(Text)  # JSON object of available time slots
    photo_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class Appointment(Base):
    """Appointment bookings"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=True, index=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'), nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=False, index=True)
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    reason = Column(String(500))  # Chief complaint
    symptoms = Column(Text)
    status = Column(String(50), default='scheduled')  # scheduled, confirmed, completed, cancelled
    notes = Column(Text)
    reminder_sent_booking = Column(Boolean, default=False)
    reminder_sent_1hour = Column(Boolean, default=False)
    reminder_sent_1day = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=True, index=True)
    type = Column(String(50))  # booking_confirmation, appointment_reminder, general
    title = Column(String(200))
    message = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
