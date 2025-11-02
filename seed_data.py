"""
Seed database with sample hospitals and doctors
"""
import json
from database import SessionLocal, Hospital, Doctor, init_db

def seed_hospitals_and_doctors():
    """Add sample hospitals and doctors to the database"""
    db = SessionLocal()
    
    # Check if data already exists
    existing_hospitals = db.query(Hospital).count()
    if existing_hospitals > 0:
        print("Database already has hospital data. Skipping seed.")
        db.close()
        return
    
    print("Seeding database with sample hospitals and doctors...")
    
    # Sample hospitals
    hospitals_data = [
        {
            "name": "Sydney General Hospital",
            "address": "123 Health Street, Sydney CBD",
            "city": "Sydney",
            "distance_km": 2.5,
            "phone": "+61 2 9123 4567",
            "specialties": json.dumps(["General Medicine", "Emergency Care", "Cardiology", "Pediatrics"]),
            "rating": 4.5,
            "accepts_emergency": True
        },
        {
            "name": "Royal North Shore Hospital",
            "address": "Reserve Road, St Leonards",
            "city": "Sydney",
            "distance_km": 5.2,
            "phone": "+61 2 9926 7111",
            "specialties": json.dumps(["General Medicine", "Surgery", "Neurology", "Orthopedics"]),
            "rating": 4.7,
            "accepts_emergency": True
        },
        {
            "name": "Westmead Hospital",
            "address": "Darcy Road, Westmead",
            "city": "Sydney",
            "distance_km": 8.1,
            "phone": "+61 2 8890 5555",
            "specialties": json.dumps(["General Medicine", "Pediatrics", "Oncology", "Maternity"]),
            "rating": 4.6,
            "accepts_emergency": True
        },
        {
            "name": "Prince of Wales Hospital",
            "address": "High Street, Randwick",
            "city": "Sydney",
            "distance_km": 6.8,
            "phone": "+61 2 9382 2222",
            "specialties": json.dumps(["General Medicine", "Cardiology", "Neurology", "Dermatology"]),
            "rating": 4.4,
            "accepts_emergency": True
        },
        {
            "name": "Liverpool Hospital",
            "address": "Elizabeth Street, Liverpool",
            "city": "Sydney",
            "distance_km": 12.3,
            "phone": "+61 2 8738 3000",
            "specialties": json.dumps(["General Medicine", "Trauma Care", "Pediatrics", "Surgery"]),
            "rating": 4.3,
            "accepts_emergency": True
        }
    ]
    
    hospitals = []
    for h_data in hospitals_data:
        hospital = Hospital(**h_data)
        db.add(hospital)
        hospitals.append(hospital)
    
    db.commit()
    
    # Refresh to get IDs
    for h in hospitals:
        db.refresh(h)
    
    # Sample doctors for each hospital
    doctors_data = [
        # Sydney General Hospital
        {
            "hospital_id": hospitals[0].id,
            "name": "Dr. Sarah Johnson",
            "specialization": "General Medicine",
            "qualifications": "MBBS, FRACP",
            "experience_years": 15,
            "rating": 4.8,
            "consultation_fee": 120.0,
            "availability": json.dumps({
                "Monday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
                "Tuesday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "Wednesday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
                "Thursday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "Friday": ["09:00", "10:00", "11:00", "14:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=47"
        },
        {
            "hospital_id": hospitals[0].id,
            "name": "Dr. Michael Chen",
            "specialization": "Cardiology",
            "qualifications": "MBBS, PhD, FRACP",
            "experience_years": 20,
            "rating": 4.9,
            "consultation_fee": 180.0,
            "availability": json.dumps({
                "Monday": ["10:00", "11:00", "14:00", "15:00"],
                "Wednesday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                "Thursday": ["09:00", "10:00", "11:00", "14:00"],
                "Friday": ["10:00", "11:00", "14:00", "15:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=33"
        },
        {
            "hospital_id": hospitals[0].id,
            "name": "Dr. Emily Watson",
            "specialization": "Pediatrics",
            "qualifications": "MBBS, FRACP (Paeds)",
            "experience_years": 12,
            "rating": 4.7,
            "consultation_fee": 130.0,
            "availability": json.dumps({
                "Monday": ["09:00", "10:00", "11:00", "13:00", "14:00"],
                "Tuesday": ["09:00", "10:00", "11:00", "13:00", "14:00", "15:00"],
                "Thursday": ["09:00", "10:00", "11:00", "13:00", "14:00"],
                "Friday": ["09:00", "10:00", "11:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=45"
        },
        # Royal North Shore Hospital
        {
            "hospital_id": hospitals[1].id,
            "name": "Dr. David Kumar",
            "specialization": "General Medicine",
            "qualifications": "MBBS, FRACP",
            "experience_years": 18,
            "rating": 4.6,
            "consultation_fee": 125.0,
            "availability": json.dumps({
                "Monday": ["08:00", "09:00", "10:00", "14:00", "15:00", "16:00"],
                "Tuesday": ["08:00", "09:00", "10:00", "14:00", "15:00", "16:00"],
                "Wednesday": ["08:00", "09:00", "10:00", "14:00", "15:00"],
                "Friday": ["08:00", "09:00", "10:00", "14:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=52"
        },
        {
            "hospital_id": hospitals[1].id,
            "name": "Dr. Rachel Martinez",
            "specialization": "Neurology",
            "qualifications": "MBBS, PhD, FRACP (Neuro)",
            "experience_years": 22,
            "rating": 4.9,
            "consultation_fee": 200.0,
            "availability": json.dumps({
                "Tuesday": ["10:00", "11:00", "14:00", "15:00"],
                "Wednesday": ["10:00", "11:00", "14:00"],
                "Thursday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                "Friday": ["10:00", "11:00", "14:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=44"
        },
        {
            "hospital_id": hospitals[1].id,
            "name": "Dr. James Anderson",
            "specialization": "Orthopedics",
            "qualifications": "MBBS, FRACS (Ortho)",
            "experience_years": 16,
            "rating": 4.7,
            "consultation_fee": 170.0,
            "availability": json.dumps({
                "Monday": ["09:00", "10:00", "11:00", "15:00", "16:00"],
                "Tuesday": ["09:00", "10:00", "11:00", "15:00"],
                "Thursday": ["09:00", "10:00", "11:00", "15:00", "16:00"],
                "Friday": ["09:00", "10:00", "11:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=56"
        },
        # Westmead Hospital
        {
            "hospital_id": hospitals[2].id,
            "name": "Dr. Lisa Thompson",
            "specialization": "General Medicine",
            "qualifications": "MBBS, FRACP",
            "experience_years": 14,
            "rating": 4.5,
            "consultation_fee": 115.0,
            "availability": json.dumps({
                "Monday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "Tuesday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
                "Wednesday": ["09:00", "10:00", "11:00", "14:00"],
                "Thursday": ["09:00", "10:00", "11:00", "14:00", "15:00"],
                "Friday": ["09:00", "10:00", "11:00", "14:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=48"
        },
        {
            "hospital_id": hospitals[2].id,
            "name": "Dr. Ahmed Hassan",
            "specialization": "Oncology",
            "qualifications": "MBBS, PhD, FRACP (Med Onc)",
            "experience_years": 25,
            "rating": 4.9,
            "consultation_fee": 220.0,
            "availability": json.dumps({
                "Monday": ["10:00", "11:00", "14:00"],
                "Wednesday": ["10:00", "11:00", "14:00", "15:00"],
                "Thursday": ["10:00", "11:00", "14:00"],
                "Friday": ["10:00", "11:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=51"
        },
        # Prince of Wales Hospital
        {
            "hospital_id": hospitals[3].id,
            "name": "Dr. Jennifer Lee",
            "specialization": "Dermatology",
            "qualifications": "MBBS, FACD",
            "experience_years": 13,
            "rating": 4.8,
            "consultation_fee": 160.0,
            "availability": json.dumps({
                "Monday": ["09:00", "10:00", "11:00", "13:00", "14:00"],
                "Tuesday": ["09:00", "10:00", "11:00", "13:00", "14:00"],
                "Wednesday": ["09:00", "10:00", "11:00"],
                "Thursday": ["09:00", "10:00", "11:00", "13:00", "14:00"],
                "Friday": ["09:00", "10:00", "11:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=43"
        },
        {
            "hospital_id": hospitals[3].id,
            "name": "Dr. Robert Williams",
            "specialization": "Cardiology",
            "qualifications": "MBBS, FRACP (Cardio)",
            "experience_years": 19,
            "rating": 4.7,
            "consultation_fee": 175.0,
            "availability": json.dumps({
                "Monday": ["10:00", "11:00", "14:00", "15:00"],
                "Tuesday": ["10:00", "11:00", "14:00", "15:00", "16:00"],
                "Thursday": ["10:00", "11:00", "14:00", "15:00"],
                "Friday": ["10:00", "11:00", "14:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=59"
        },
        # Liverpool Hospital
        {
            "hospital_id": hospitals[4].id,
            "name": "Dr. Priya Sharma",
            "specialization": "General Medicine",
            "qualifications": "MBBS, FRACP",
            "experience_years": 11,
            "rating": 4.6,
            "consultation_fee": 110.0,
            "availability": json.dumps({
                "Monday": ["08:00", "09:00", "10:00", "14:00", "15:00", "16:00"],
                "Tuesday": ["08:00", "09:00", "10:00", "14:00", "15:00"],
                "Wednesday": ["08:00", "09:00", "10:00", "14:00", "15:00", "16:00"],
                "Thursday": ["08:00", "09:00", "10:00", "14:00", "15:00"],
                "Friday": ["08:00", "09:00", "10:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=49"
        },
        {
            "hospital_id": hospitals[4].id,
            "name": "Dr. Thomas Brown",
            "specialization": "Trauma Care",
            "qualifications": "MBBS, FRACS (Trauma)",
            "experience_years": 17,
            "rating": 4.8,
            "consultation_fee": 190.0,
            "availability": json.dumps({
                "Monday": ["09:00", "10:00", "15:00", "16:00"],
                "Tuesday": ["09:00", "10:00", "15:00", "16:00"],
                "Wednesday": ["09:00", "10:00", "15:00"],
                "Thursday": ["09:00", "10:00", "15:00", "16:00"],
                "Friday": ["09:00", "10:00"]
            }),
            "photo_url": "https://i.pravatar.cc/150?img=60"
        }
    ]
    
    for d_data in doctors_data:
        doctor = Doctor(**d_data)
        db.add(doctor)
    
    db.commit()
    
    print(f"✅ Successfully seeded {len(hospitals)} hospitals and {len(doctors_data)} doctors!")
    db.close()

if __name__ == "__main__":
    init_db()
    seed_hospitals_and_doctors()
