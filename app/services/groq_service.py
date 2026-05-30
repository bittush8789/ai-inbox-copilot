import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key or self.api_key.startswith("your_groq_api_key"):
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    def is_configured(self) -> bool:
        return self.client is not None

    def get_completion(self, prompt: str, json_mode: bool = True) -> str:
        if not self.is_configured():
            raise ValueError(
                "Groq API Key is not configured. Please set the GROQ_API_KEY environment variable in the .env file."
            )
        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that always outputs valid JSON." if json_mode else "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "timeout": 30.0,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            chat_completion = self.client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with Groq LLM API: {str(e)}")
        
groq_service = GroqService()
