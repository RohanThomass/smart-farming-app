import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")
genai.configure(api_key=api_key)

def generate_farming_insight(sensor_data: str, question: str) -> str:
    """
    Generate smart farming insights using Google's Gemini API.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"Sensor Data:\n{sensor_data}\n\n"
            f"Farmer's Question:\n{question}\n\n"
            "You are an expert agronomist providing precise, practical advice "
            "on irrigation, soil health, crop rotation, and sustainable farming practices."
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"⚠️ Error generating Gemini insight: {str(e)}"
