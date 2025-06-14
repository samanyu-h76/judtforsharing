import google.generativeai as genai

_model = None

# Initialize Gemini API

def init_gemini(api_key: str = "AIzaSyA-eFWdCSUeNggTlWGzbFEA1uGtioZMQEA", model_name: str = "gemini-1.5-flash"):
    global _model
    genai.configure(api_key=api_key, transport="rest")
    _model = genai.GenerativeModel(model_name)
    return _model

# Get the active model

def get_model():
    if _model is None:
        raise ValueError("Gemini model not initialized. Call init_gemini() first.")
    return _model

# Generate content from prompt

def generate_campaign(prompt: str) -> str:
    model = get_model()
    response = model.generate_content(prompt)
    return response.text.strip()
