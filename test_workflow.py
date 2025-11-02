"""Quick test of the workflow"""
import sys
sys.path.append('medical_llama')

from workflow import MedicalWorkflow

print("Initializing workflow...")
workflow = MedicalWorkflow()

print("Running test triage...")
result = workflow.run(
    patient_id="test_123",
    user_input="I have a sore throat",
    conversation_history=[]
)

print("\n=== RESULT ===")
print(f"Type: {type(result)}")
print(f"Result: {result}")
print("==============")
