"""
Langraph workflow orchestration for medical chatbot
"""
from typing import TypedDict, Optional, List, Any
from langgraph.graph import StateGraph, END, START
from llm_wrapper import MedicalLLMWrapper
from config import CONFIDENCE_THRESHOLD

class MedicalState(TypedDict):
    """State maintained throughout the workflow"""
    patient_id: str
    user_input: str
    conversation_history: List[dict]
    
    # Triage results
    triage_result: Optional[dict]
    severity: Optional[str]
    is_emergency: Optional[bool]
    
    # Care pathway
    care_pathway: Optional[dict]
    recommended_pathway: Optional[str]
    
    # Action execution
    action_plan: Optional[dict]
    
    # Metadata
    needs_escalation: bool
    confidence: float
    error: Optional[str]
    skip_to_finalize: Optional[bool]  # Flag to skip care pathway/action nodes

class MedicalWorkflow:
    """Langraph-based workflow for medical triage and care recommendations"""
    
    def __init__(self):
        self.llm = MedicalLLMWrapper()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build Langraph state machine"""
        graph = StateGraph(MedicalState)
        
        # Add nodes
        graph.add_node("triage", self._node_triage)
        graph.add_node("check_emergency", self._node_check_emergency)
        graph.add_node("recommend_pathway", self._node_recommend_pathway)
        graph.add_node("execute_action", self._node_execute_action)
        graph.add_node("escalate", self._node_escalate)
        graph.add_node("finalize", self._node_finalize)
        
        # Define edges (workflow routing)
        graph.add_edge(START, "triage")
        
        # After triage, check if emergency
        graph.add_conditional_edges(
            "triage",
            self._should_escalate_emergency,
            {
                "escalate": "escalate",
                "continue": "check_emergency",
            }
        )
        
        # Check confidence level
        graph.add_conditional_edges(
            "check_emergency",
            self._should_escalate_confidence,
            {
                "escalate": "escalate",
                "continue": "recommend_pathway",
                "skip": "finalize",  # Skip to finalize if gathering info
            }
        )
        
        # Recommend care pathway
        graph.add_edge("recommend_pathway", "execute_action")
        
        # Execute action and finalize
        graph.add_edge("execute_action", "finalize")
        
        # Escalation path
        graph.add_edge("escalate", "finalize")
        
        # End
        graph.add_edge("finalize", END)
        
        return graph.compile()
    
    def _node_triage(self, state: MedicalState) -> MedicalState:
        """Triage node: analyze patient input"""
        print(f"\n=== TRIAGE NODE CALLED ===")
        print(f"User input: {state['user_input']}")
        print(f"==========================\n")
        
        try:
            result = self.llm.perform_triage(
                state["user_input"],
                state.get("conversation_history", [])
            )
            
            print(f"\n=== TRIAGE RESULT ===")
            print(f"Result type: {type(result)}")
            print(f"Result: {result}")
            print(f"=====================\n")
            
            state["triage_result"] = result
            # If severity is None (still gathering info), use 'unknown' instead of 'referral'
            state["severity"] = result.get("severity") if result.get("severity") is not None else ("unknown" if result.get("needs_more_info") else "referral")
            state["confidence"] = result.get("confidence", 0.5)
            # Only escalate if there's an actual emergency severity, not just low confidence during info gathering
            state["is_emergency"] = result.get("severity") == "emergency"
            
        except Exception as e:
            import traceback
            print(f"\n=== TRIAGE NODE ERROR ===")
            print(traceback.format_exc())
            print(f"=========================\n")
            state["error"] = f"Triage failed: {str(e)}"
            state["severity"] = "referral"  # Default to safe option
        
        return state
    
    def _node_check_emergency(self, state: MedicalState) -> MedicalState:
        """Check if emergency classification applies"""
        severity = state.get("severity", "referral")
        state["is_emergency"] = severity == "emergency"
        
        # If we're in information gathering mode (severity is 'unknown'), 
        # set a flag to skip care pathway and action nodes
        if severity == "unknown":
            state["skip_to_finalize"] = True
        
        return state
    
    def _node_recommend_pathway(self, state: MedicalState) -> MedicalState:
        """Recommend care pathway based on triage"""
        try:
            pathway = self.llm.recommend_care_pathway(
                state.get("triage_result", {}),
                patient_context={"patient_id": state.get("patient_id")}
            )
            
            state["care_pathway"] = pathway
            state["recommended_pathway"] = pathway.get("recommended_pathway", "no_action")
            
        except Exception as e:
            state["error"] = f"Care pathway failed: {str(e)}"
            state["recommended_pathway"] = "no_action"
        
        return state
    
    def _node_execute_action(self, state: MedicalState) -> MedicalState:
        """Execute action plan"""
        try:
            action = self.llm.execute_action(
                state.get("care_pathway", {}),
                patient_context={"patient_id": state.get("patient_id")}
            )
            
            state["action_plan"] = action
            
        except Exception as e:
            state["error"] = f"Action execution failed: {str(e)}"
            state["action_plan"] = {"error": str(e)}
        
        return state
    
    def _node_escalate(self, state: MedicalState) -> MedicalState:
        """Escalation node: mark for clinician review"""
        state["needs_escalation"] = True
        state["action_plan"] = {
            "action": "escalate_to_clinician",
            "reason": "High confidence threshold not met or emergency detected",
            "steps": ["Contacting healthcare provider", "Escalating case for immediate review"],
        }
        return state
    
    def _node_finalize(self, state: MedicalState) -> MedicalState:
        """Finalize response"""
        # Add safety disclaimers
        state["action_plan"] = state.get("action_plan", {})
        if isinstance(state["action_plan"], dict):
            state["action_plan"]["medical_disclaimer"] = (
                "This is not a substitute for professional medical advice. "
                "Always consult a qualified healthcare provider for diagnosis and treatment."
            )
        
        return state
    
    def _should_escalate_emergency(self, state: MedicalState) -> str:
        """Decide if emergency escalation is needed"""
        if state.get("is_emergency"):
            return "escalate"
        return "continue"
    
    def _should_escalate_confidence(self, state: MedicalState) -> str:
        """Decide if escalation needed based on confidence"""
        # Skip pathway/action nodes if we're still gathering information
        if state.get("severity") == "unknown" or state.get("skip_to_finalize"):
            return "skip"
        
        confidence = state.get("confidence", 1.0)
        if confidence < CONFIDENCE_THRESHOLD:
            return "escalate"
        return "continue"
    
    def run(self, patient_id: str, user_input: str, conversation_history: List[dict] = None) -> MedicalState:
        """Run the workflow"""
        initial_state: MedicalState = {
            "patient_id": patient_id,
            "user_input": user_input,
            "conversation_history": conversation_history or [],
            "triage_result": None,
            "severity": None,
            "is_emergency": False,
            "care_pathway": None,
            "recommended_pathway": None,
            "action_plan": None,
            "needs_escalation": False,
            "confidence": 1.0,
            "error": None,
            "skip_to_finalize": False,
        }
        
        result = self.graph.invoke(initial_state)
        return result
