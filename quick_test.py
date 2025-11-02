"""
Quick test of Medical Llama API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Medical Llama - Quick Test")
print("=" * 60)

# Test 1: Health check
print("\n1. Testing API health...")
response = requests.get(f"{BASE_URL}/health")
print(f"✅ Status: {response.json()}")

# Test 2: Register a test patient
print("\n2. Registering test patient...")
patient_data = {
    "patient_id": "test_001",
    "name": "John Doe",
    "age": 35,
    "medical_history": ["hypertension"],
    "allergies": ["penicillin"],
    "current_medications": ["lisinopril"]
}

try:
    response = requests.post(f"{BASE_URL}/patients/register", json=patient_data)
    if response.status_code == 200:
        print(f"✅ Registered: {response.json()['name']}")
    else:
        print(f"⚠️  Patient may already exist (status {response.status_code})")
except Exception as e:
    print(f"⚠️  {e}")

# Test 3: Run triage - mild case
print("\n3. Testing triage - MILD case (sore throat)...")
print("   This will take 5-10 seconds (LLM inference)...")
triage_data = {
    "patient_id": "test_001",
    "message": "I have a sore throat and mild cough for 2 days, no fever"
}

response = requests.post(f"{BASE_URL}/chat/triage", json=triage_data, timeout=60)
result = response.json()

print(f"\n📊 Triage Result:")
print(f"   Severity: {result['severity']}")
print(f"   Confidence: {result['confidence']:.2f}")
print(f"   Recommendation: {result['recommendation'][:100]}...")
print(f"   Needs escalation: {result['needs_escalation']}")

# Test 4: Run triage - emergency case
print("\n4. Testing triage - EMERGENCY case (chest pain)...")
print("   This will take 5-10 seconds (LLM inference)...")
triage_data = {
    "patient_id": "test_001",
    "message": "I have severe chest pain and difficulty breathing"
}

response = requests.post(f"{BASE_URL}/chat/triage", json=triage_data, timeout=60)
result = response.json()

print(f"\n🚨 Emergency Detection:")
print(f"   Severity: {result['severity']}")
print(f"   Confidence: {result['confidence']:.2f}")
print(f"   Recommendation: {result['recommendation'][:100]}...")
print(f"   Needs escalation: {result['needs_escalation']}")

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
print(f"\n📚 API Documentation: http://localhost:8000/docs")
print(f"📊 View all endpoints at: http://localhost:8000/docs")
