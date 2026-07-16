import json
from typing import Dict, Any, List, Optional
from faos.services.security.models import GlobalPolicy

class PromptBuilder:
    """
    Constructs System and User Prompts by merging:
    - Task Intent
    - Execution Context (Evidence)
    - Security Policies (Constraints)
    - Knowledge & Capabilities
    """
    
    def __init__(self, policy: Optional[GlobalPolicy] = None):
        self.policy = policy or GlobalPolicy()
        
    def build_system_prompt(self, base_role: str, capabilities: List[str] = None, knowledge: str = None) -> str:
        """
        Builds the system instruction incorporating roles, capabilities, and constraints.
        """
        prompt = [
            f"# Role",
            base_role,
            ""
        ]
        
        if capabilities:
            prompt.extend([
                "# Capabilities",
                "You have access to the following capabilities/tools indirectly via the FAOS runtime:",
                "\n".join(f"- {cap}" for cap in capabilities),
                ""
            ])
            
        if knowledge:
            prompt.extend([
                "# Domain Knowledge",
                knowledge,
                ""
            ])
            
        prompt.extend([
            "# Constraints",
            f"1. Do not use more than {self.policy.max_tokens_per_task} tokens in your reasoning.",
            "2. Rely ONLY on the provided context evidence. Do not hallucinate data."
        ])
        
        if not self.policy.allow_network_access:
            prompt.append("3. Network access is completely disabled. You cannot fetch live data yourself.")
            
        return "\n".join(prompt)
        
    def build_user_prompt(self, intent: str, context_data: Dict[str, Any]) -> str:
        """
        Builds the user prompt combining the specific intent and the provided context/evidence.
        """
        prompt = [
            "# Task Intent",
            intent,
            "",
            "# Evidence / Context Data",
            "The following structured data was gathered by the runtime providers:"
        ]
        
        # Serialize context data, ignoring huge blobs if we wanted to (but we trust Gemini's 1M window for MVP)
        try:
            context_str = json.dumps(context_data, ensure_ascii=False, indent=2)
            prompt.append("```json\n" + context_str + "\n```")
        except Exception as e:
            prompt.append(f"[Error serializing context: {str(e)}]")
            prompt.append(str(context_data))
            
        return "\n".join(prompt)
