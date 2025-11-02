"""
LLM wrapper for Ollama-based Medical LLM
"""
import json
import re
from typing import Optional
from langchain_ollama import OllamaLLM
from config import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    TRIAGE_SYSTEM_PROMPT,
    CARE_PATHWAY_SYSTEM_PROMPT,
    ACTION_EXECUTION_SYSTEM_PROMPT,
    EMERGENCY_KEYWORDS,
)

class MedicalLLMWrapper:
    """Wrapper around Ollama-based Medical LLM"""
    
    def __init__(self):
        # Try to initialize with num_gpu=0 to force CPU mode if CUDA fails
        try:
            self.llm = OllamaLLM(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                num_predict=2048,  # Increase max tokens to prevent truncation
            )
            # Test if it works
            self.llm.invoke("test")
        except Exception as e:
            print(f"WARNING: Ollama initialization failed: {e}")
            print("Retrying with CPU mode...")
            self.llm = OllamaLLM(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                num_gpu=0,  # Force CPU mode
                num_predict=2048,  # Increase max tokens
            )
    
    def _check_emergency_keywords(self, text: str) -> bool:
        """Check if text contains emergency keywords"""
        text_lower = text.lower()
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in text_lower:
                return True
        return False
    
    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from LLM response"""
        # Try to find JSON in response
        try:
            # First try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown or text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        
        # Fallback: return error response
        return {"error": "Failed to parse response", "raw_response": response}
    
    def perform_triage(self, patient_input: str, conversation_history: Optional[list] = None) -> dict:
        """
        Perform medical triage on patient input with conversational follow-up
        Returns: {severity, reasoning, recommendation, suggested_actions, confidence, escalated, needs_more_info}
        """
        # Check for emergency keywords first
        if self._check_emergency_keywords(patient_input):
            return {
                "severity": "emergency",
                "reasoning": "Emergency keywords detected in patient description",
                "recommendation": "🚨 IMMEDIATE MEDICAL ATTENTION REQUIRED. Call 999 or go to nearest emergency room. Do not wait.",
                "suggested_actions": ["Call emergency services (999)", "Go to nearest emergency department", "Do not drive yourself"],
                "disclaimer": "This is an emergency. Do not delay seeking immediate medical care.",
                "confidence": 1.0,
                "escalated": True,
                "needs_more_info": False,
            }
        
        # Build conversational context
        context = ""
        if conversation_history:
            context = "\n\nPrevious conversation context:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                context += f"Patient: {msg.get('user', '')}\nYou: {msg.get('assistant', '')}\n"
        
        # Conversational triage prompt
        prompt = f"""You are a compassionate medical triage assistant having a conversation with a patient.

INSTRUCTIONS:
1. If you don't have enough information to assess severity, ask 1-2 SPECIFIC follow-up questions
2. Once you have sufficient information, provide a complete assessment with:
   - Severity classification (self_care, referral, urgent, or emergency)
   - Detailed reasoning
   - Specific recommendations
   - Possible conditions (list 2-3 most likely)
   - Self-care advice and/or medications if appropriate
   - Clear next steps

CONVERSATION STYLE:
- Be warm, empathetic, and professional
- Ask questions naturally (like a doctor would)
- Don't overwhelm with too many questions at once
- If patient provides enough info, give full assessment

{context}

Patient's latest message: {patient_input}

RESPOND IN JSON FORMAT:
{{
  "needs_more_info": true/false,
  "recommendation": "Your conversational response (ask questions if needs_more_info=true, provide full assessment if false)",
  "severity": "self_care|referral|urgent|emergency" (only if needs_more_info=false),
  "reasoning": "clinical reasoning" (only if needs_more_info=false),
  "possible_conditions": ["condition1", "condition2"] (only if needs_more_info=false),
  "suggested_actions": ["action1", "action2"],
  "medications": ["med1", "med2"] (only for self_care cases),
  "disclaimer": "appropriate medical disclaimer",
  "confidence": 0.0-1.0
}}"""
        
        response = self.llm.invoke(prompt)
        
        # Debug logging
        print(f"\n=== LLM RAW RESPONSE (perform_triage) ===")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(str(response))}")
        print(f"First 800 chars: {str(response)[:800]}")
        print(f"==========================================\n")
        
        result = self._parse_json_response(response)
        
        # If parsing failed, create a fallback response
        if "error" in result or not isinstance(result, dict) or "recommendation" not in result:
            print(f"WARNING: Failed to parse LLM response properly. Creating fallback.")
            result = {
                "needs_more_info": True,
                "recommendation": "Could you please tell me more about your symptoms? How long have you been experiencing this, and are there any other symptoms?",
                "suggested_actions": ["Describe symptoms in detail", "Mention duration and severity"],
                "disclaimer": "This is not medical advice. Please consult a healthcare professional if symptoms persist.",
                "confidence": 0.8
            }
        
        # Add escalation flag
        if "confidence" in result and "severity" in result:
            result["escalated"] = result.get("confidence", 1.0) < 0.6 or result.get("severity") in ["urgent", "emergency"]
        else:
            result["escalated"] = False
        
        return result
    
    def recommend_care_pathway(self, triage_result: dict, patient_context: Optional[dict] = None) -> dict:
        """
        Recommend care pathway based on triage severity
        """
        severity = triage_result.get("severity", "referral")
        reasoning = triage_result.get("reasoning", "")
        
        prompt = f"""{CARE_PATHWAY_SYSTEM_PROMPT}

Triage Result:
- Severity: {severity}
- Reasoning: {reasoning}
- Patient Symptoms: {triage_result.get('recommendation', '')}

{f"Patient Context: {patient_context}" if patient_context else ""}

Based on this triage, recommend the appropriate care pathway:"""
        
        response = self.llm.invoke(prompt)
        
        # Debug logging
        print(f"\n=== LLM RAW RESPONSE (perform_triage) ===")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(str(response))}")
        print(f"First 500 chars: {str(response)[:500]}")
        print(f"========================\n")
        
        result = self._parse_json_response(response)
        
        # If parsing failed, create a fallback response
        if "error" in result or not isinstance(result, dict) or "recommendation" not in result:
            print(f"WARNING: Failed to parse LLM response properly. Creating fallback.")
            result = {
                "needs_more_info": False,
                "recommendation": "I'm having trouble processing your request. Please describe your symptoms in more detail.",
                "severity": "referral",
                "reasoning": "Unable to parse response",
                "possible_conditions": [],
                "suggested_actions": ["Consult with a healthcare provider"],
                "medications": [],
                "disclaimer": "This is not medical advice. Please consult a healthcare professional.",
                "confidence": 0.3
            }
        return result
    
    def execute_action(self, pathway: dict, patient_context: Optional[dict] = None) -> dict:
        """
        Generate action steps based on recommended care pathway
        """
        recommended_action = pathway.get("recommended_pathway", "no_action")
        
        prompt = f"""{ACTION_EXECUTION_SYSTEM_PROMPT}

Recommended Pathway: {recommended_action}
Reasoning: {pathway.get('reasoning', '')}
Specific Actions: {pathway.get('specific_actions', [])}

{f"Patient Context: {patient_context}" if patient_context else ""}

Provide concrete action steps for the patient to follow:"""
        
        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response)
        return result
    
    def validate_response(self, response: str) -> dict:
        """
        Validate LLM response for hallucinations and safety issues
        """
        # Check for explicit medical diagnosis statements (risky)
        diagnosis_patterns = [
            r"you have\s+(\w+)",
            r"you (are|have been)\s+diagnosed",
            r"it'?s (?:definitely|clearly)\s+(\w+)",
        ]
        
        diagnosis_found = False
        for pattern in diagnosis_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                diagnosis_found = True
                break
        
        return {
            "is_safe": not diagnosis_found,
            "diagnosis_detected": diagnosis_found,
            "needs_disclaimer": diagnosis_found or "medication" in response.lower(),
        }
