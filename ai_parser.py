from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

class TaskItem(BaseModel):
    task_title: str = Field(description="Clean, concise title of the task")
    priority: Optional[Literal["High", "Medium", "Low"]] = Field(default="Medium", description="Task priority")
    due_date_iso: Optional[str] = Field(default=None, description="ISO 8601 target due timestamp, e.g. 2026-09-23T19:00:00")

class ParsedIntent(BaseModel):
    intent: Literal["CREATE_TASK", "COMPLETE_TASK", "LIST_TASKS", "GENERAL"] = Field(description="Primary user intent")
    tasks: List[TaskItem] = Field(default_factory=list, description="List of tasks to create")
    task_title: Optional[str] = Field(default=None, description="Title of task to mark complete")
    response_text: Optional[str] = Field(default=None, description="Direct text response if conversational")

def get_client():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None
    return genai.Client(api_key=GEMINI_API_KEY)

MODEL_CANDIDATES = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash"]

def parse_user_message(user_message: str) -> ParsedIntent:
    client = get_client()
    if not client:
        return basic_fallback_parser(user_message)
        
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    system_instruction = f"""
    You are a Task & Reminder Assistant.
    Current Local Date & Time: {current_time_str}.
    
    Parse the user's message into JSON matching the schema.
    
    RULES:
    - If user mentions multiple tasks (e.g. "Write book and draw diagrams", "Buy milk, call doctor"), extract EACH action as a separate item in `tasks` array.
    - Clean task titles (strip "i need to", "remind me to").
    - Calculate exact ISO 8601 due timestamps (YYYY-MM-DDTHH:MM:SS) relative to current time for any relative time mentioned.
    """

    for model_name in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ParsedIntent,
                    temperature=0.1
                )
            )
            return ParsedIntent.model_validate_json(response.text)
        except Exception as e:
            print(f"[AI Parser Warning] Model {model_name} failed: {e}. Trying fallback...")

    return basic_fallback_parser(user_message)

def basic_fallback_parser(text: str) -> ParsedIntent:
    lower_text = text.lower()
    if any(word in lower_text for word in ["tasks", "list", "show my tasks"]):
        return ParsedIntent(intent="LIST_TASKS")
    elif "done" in lower_text or "complete" in lower_text:
        clean_title = text.replace("done", "").replace("complete", "").replace("marked", "").strip()
        return ParsedIntent(intent="COMPLETE_TASK", task_title=clean_title)
    else:
        raw_text = text
        for prefix in ["i need to ", "remind me to ", "i have to ", "please "]:
            if raw_text.lower().startswith(prefix):
                raw_text = raw_text[len(prefix):]
                
        import re
        parts = re.split(r'\s+and\s+|,|;', raw_text)
        parts = [p.strip().capitalize() for p in parts if p.strip()]
        
        task_items = [
            TaskItem(task_title=p, priority="Medium")
            for p in parts
        ] if parts else [TaskItem(task_title=text.capitalize(), priority="Medium")]
        
        return ParsedIntent(intent="CREATE_TASK", tasks=task_items)
