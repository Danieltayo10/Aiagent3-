import os
import typing as t
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OpenAI_API_KEY")
c = OpenAI(base_url="https://openrouter.ai/api/v1",api_key=key)



Groq_API_KEY = key

class LLMClient:
    """
    Simple wrapper for OpenAI API calls.
    """

    def __init__(self, api_key: t.Optional[str] = None):
        self.api_key = Groq_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env")
        
    def chat(
        self,
        system: str = "You are a helpful AI assistant.",
        messages: t.List[dict] = None,
        model: str ="mistralai/mixtral-8x7b-instruct",
        temperature: float = 0.2,
    ) -> t.Dict:
        """
        messages: List of dicts, e.g. [{"role":"user","content":"Hello"}]
        Returns: {"content": "..."}
        """
       
        if messages is None:
            messages = [{"role": "user", "content": ""}]
        response = c.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}] + messages,
            temperature=temperature,
        )
        content = response.choices[0].message.content
        return {"content": content}
    

client = LLMClient()