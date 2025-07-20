"""Load models to use them as a narrator and a common-sense oracle in the PAYADOR pipeline."""
import time
import google.genai as genai
from google.genai import types
from google.genai.errors import ServerError
import replicate
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_llm(model_name: str = "gemini-2.0-flash") -> object:

    google_models = ["gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
    replicate_models = ["meta/meta-llama-3-70b", "meta/meta-llama-3-70b-instruct"]

    model = None

    if model_name in google_models:
        model = GeminiModel(API_key="GEMINI_API_KEY", model_name=model_name)
    elif model_name in replicate_models:
        model = ReplicateModel(API_key="REPLICATE_API_TOKEN", model_name=model_name)

    return model


class ReplicateModel():
    def __init__ (self, API_key:str, model_name:str = "meta/meta-llama-3-70b-instruct") -> None:
        self.temperature = 0.7
        self.model_name = model_name

    def prompt_model(self,system_msg: str, user_msg:str) -> str:
        """Prompt the Replicate model."""

        system_instructions = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_msg}<|eot_id|><|start_header_id|>user<|end_header_id|>"

        input = {
            "top_p": 0.1,
            "min_tokens": 0,
            "temperature": self.temperature,
            "prompt": user_msg,
            "prompt_template": system_instructions + "\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        }

        output = replicate.run(self.model_name,input=input)
        
        return "".join(output)

class GeminiModel():
    def __init__ (self, API_key:str, model_name:str = "gemini-2.0-flash") -> None:
        """"Initialize the Gemini model using an API key."""
        # self.safety_settings = [
        #     types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
        #     types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
        #     types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        #     types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE")
        # ]
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def prompt_model(self, system_msg: str, user_msg: str, retry_attempts: int = 3, delay_seconds: int = 2) -> str:
        """Prompt the Gemini model con reintentos automáticos en caso de sobrecarga."""
        full_prompt = system_msg + "\n\n" + user_msg
        for attempt in range(retry_attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                )
                return response.text.strip()
            except ServerError as e:
                # Check if it's an overload error (503) by examining the error message
                if hasattr(e, 'error') and hasattr(e.error, 'code') and e.error.code == 503:
                    print(f"[WARN] Modelo sobrecargado. Intento {attempt+1}/{retry_attempts}")
                    time.sleep(delay_seconds)
                elif str(e).startswith('503 UNAVAILABLE'):
                    # Alternative way to check for 503 error based on string representation
                    print(f"[WARN] Modelo sobrecargado. Intento {attempt+1}/{retry_attempts}")
                    time.sleep(delay_seconds)
                else:
                    print(f"[ERROR] Otro error con el modelo: {e}")
                    break
            except Exception as general_error:
                print(f"[ERROR] Error inesperado: {general_error}")
                if attempt == retry_attempts - 1:  # If it's the last attempt
                    break
                time.sleep(delay_seconds)
                
        return "⚠️ El modelo está sobrecargado o no respondió. Por favor, intentá nuevamente."
    
    def prompt_model_structured(self, prompt: str, response_schema, max_retries: int = 3, delay_seconds: int = 2):
        """Prompt the Gemini model with structured output."""
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        response_mime_type="application/json",
                        top_p=0.9,
                        max_output_tokens=8192,
                        response_schema=response_schema,
                    ),
                )
                
                # Clean the response text before parsing
                response_text = response.text.strip()
                
                # Remove any markdown code block markers if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                if not self._is_json_complete(response_text):
                    print(f"Attempt {attempt + 1}: JSON appears truncated, retrying...")
                    continue

                # Parse the JSON response
                parsed_response = json.loads(response_text)
                return parsed_response
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error on attempt {attempt + 1}: {e}")
                if 'response' in locals():
                    print(f"Raw response: {response.text[:500]}...")  # Print first 500 chars for debugging
                
                if attempt == max_retries - 1:
                    print("Max retries reached. Returning empty result.")
                    # Return a minimal valid structure based on common schema patterns
                    return self._get_empty_response_for_schema(response_schema)
                else:
                    print(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(delay_seconds)
                    
            except ServerError as e:
                # Check if it's an overload error (503) by examining the error message
                if str(e).startswith('503 UNAVAILABLE'):
                    print(f"[WARN] Modelo sobrecargado. Intento {attempt+1}/{max_retries}")
                    time.sleep(delay_seconds)
                else:
                    print(f"[ERROR] Error del servidor en generación estructurada: {e}")
                    if attempt == max_retries - 1:
                        return self._get_empty_response_for_schema(response_schema)
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                print(f"Unexpected error in structured output generation: {e}")
                if attempt == max_retries - 1:
                    return self._get_empty_response_for_schema(response_schema)
                else:
                    print(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(delay_seconds)

    def _is_json_complete(self, json_text: str) -> bool:
        """Check if JSON appears to be complete (basic heuristic)."""
        if not json_text.strip():
            return False
    
        # Count braces and brackets
        open_braces = json_text.count('{')
        close_braces = json_text.count('}')
        open_brackets = json_text.count('[')
        close_brackets = json_text.count(']')
        
        # Basic check: should have matching braces/brackets
        return (open_braces == close_braces and 
                open_brackets == close_brackets and
                json_text.strip().endswith('}'))

    def _get_empty_response_for_schema(self, response_schema):
        """Generate an empty response that matches the expected schema structure."""
        # This is a fallback method - you might want to customize this based on your specific schemas
        try:
            # If the schema has a 'properties' field (typical for JSON schema)
            if hasattr(response_schema, 'properties') or (isinstance(response_schema, dict) and 'properties' in response_schema):
                return {}
            # For Pydantic models, try to create an empty instance
            elif hasattr(response_schema, 'model_validate'):
                return response_schema().model_dump()
            else:
                return {}
        except:
            return {}
