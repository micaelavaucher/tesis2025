"""Load models to use them as a narrator and a common-sense oracle in the PAYADOR pipeline."""
import google.genai as genai
from google.genai import types

class GeminiModel():
    def __init__(self, api_key_file: str) -> None:
        """"Initialize the Gemini model using an API key."""
        self.api_key = get_api_key(api_key_file)
        self.client = genai.Client(api_key=self.api_key)
        
        self.safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE")
        ]
        
        self.model_name = "gemini-2.0-flash"

    def prompt_model(self, prompt: str) -> str:
        """Prompt the Gemini model."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=self.safety_settings
            ))
        return response.text
    
    def prompt_model_structured(self, prompt: str, response_schema):
        """Prompt the Gemini model with structured output."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    safety_settings=self.safety_settings,
                    response_mime_type="application/json",
                    response_schema=response_schema),
            )
            return response.text
        except Exception as e:
            print(f"Error generating structured content: {e}")
            return "{}"  # Empty JSON

def get_api_key(path: str) -> str:
    """Load an API key from path."""
    key = ""
    with open(path) as f:
        key = f.readline()
    return key