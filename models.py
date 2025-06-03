"""Load models to use them as a narrator and a common-sense oracle in the PAYADOR pipeline."""
import google.genai as genai
from google.genai import types
import replicate
import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_llm(model_name: str = "gemini-2.0-flash") -> object:

    google_models = ["gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"]
    replicate_models = ["meta/meta-llama-3-70b", "meta/meta-llama-3-70b-instruct"]

    model = None

    if model_name in google_models:
        model = GeminiModel(API_key="GOOGLE_API_KEY", model_name=model_name)
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
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    def prompt_model(self, system_msg: str, user_msg:str) -> str:
        """Prompt the Gemini model."""
        full_prompt = system_msg + "\n\n" + user_msg
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
        )
        return response.text

    def prompt_model_structured(self, prompt:str, response_schema):
        """Prompt the Gemini model with structured output."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                    top_p=0.9,
                    max_output_tokens=1024,
                    response_schema=response_schema,
                ),
            )
            # Parse the JSON response
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in structured output generation: {e}")
            # Return an empty result conforming to the schema structure
            return {}
