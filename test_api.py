"""
Test script for Medical Llama system
Run this to verify everything is working
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test API health"""
    print("Testing API health...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print(f"✅ Health: {response.json()}")

def test_register_patient():
    """Test patient registration"""
    print("\nTesting patient registration...")
    patient_data = {
        "patient_id": "test_patient_001",
        "name": "Test Patient",
        "age": 35,
        "medical_history": ["asthma"],
        "allergies": ["shellfish"],
        "current_medications": ["albuterol"]
    }
    
    response = requests.post(f"{BASE_URL}/patients/register", json=patient_data)
    assert response.status_code == 200
    print(f"✅ Registered: {response.json()['name']}")
    return patient_data["patient_id"]

def test_get_patient(patient_id):
    """Test get patient"""
    print("\nTesting get patient...")
    response = requests.get(f"{BASE_URL}/patients/{patient_id}")
    assert response.status_code == 200
    print(f"✅ Retrieved: {response.json()['name']}")

def test_triage(patient_id):
    """Test triage"""
    print("\nTesting triage - mild case...")
    triage_data = {
        "patient_id": patient_id,
        "message": "I have a sore throat and mild cough for 2 days"
    }
    
    response = requests.post(f"{BASE_URL}/chat/triage", json=triage_data, timeout=30)
    assert response.status_code == 200
    result = response.json()
    
    print(f"✅ Severity: {result['severity']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Recommendation: {result['recommendation']}")
    print(f"   Escalation needed: {result['needs_escalation']}")
    
    return result

def test_triage_emergency(patient_id):
    """Test triage - emergency case"""
    print("\nTesting triage - emergency case...")
    triage_data = {
        "patient_id": patient_id,
        "message": "I have severe chest pain and difficulty breathing"
    }
    
    response = requests.post(f"{BASE_URL}/chat/triage", json=triage_data, timeout=30)
    assert response.status_code == 200
    result = response.json()
    
    print(f"✅ Severity: {result['severity']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Escalation needed: {result['needs_escalation']}")
    assert result['severity'] == 'emergency'
    assert result['needs_escalation'] == True
    
    return result

def test_conversation_history(patient_id):
    """Test conversation history"""
    print("\nTesting conversation history...")
    response = requests.get(f"{BASE_URL}/chat/history/{patient_id}")
    assert response.status_code == 200
    history = response.json()
    print(f"✅ Retrieved {len(history)} interactions")
    if history:
        print(f"   Latest: {history[0]['user'][:50]}...")

def test_info():
    """Test service info"""
    print("\nTesting service info...")
    response = requests.get(f"{BASE_URL}/info")
    assert response.status_code == 200
    info = response.json()
    print(f"✅ Service: {info['name']} v{info['version']}")
    print(f"   Model: {info['model']}")

if __name__ == "__main__":
    print("=" * 60)
    print("Medical Llama - Integration Test Suite")
    print("=" * 60)
    
    try:
        # Test connectivity
        print("\nConnecting to API on http://localhost:8000...")
        test_health()
        test_info()
        
        # Test patient management
        patient_id = test_register_patient()
        test_get_patient(patient_id)
        
        # Test triage
        print("\nNote: Triage requires BioMistral model to be running via Ollama.")
        print("First time inference will be slower (~5-10 seconds) as model loads to VRAM.")
        print("\nStarting triage tests...\n")
        
        test_triage(patient_id)
        test_triage_emergency(patient_id)
        
        # Test history
        test_conversation_history(patient_id)
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure:")
        print("   1. Ollama is running: ollama serve")
        print("   2. BioMistral is pulled: ollama pull biomistral:latest")
        print("   3. FastAPI server is running: python main.py")
        exit(1)
    
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
