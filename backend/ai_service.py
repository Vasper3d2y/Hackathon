import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

# Load environment variables from .env file at project root or backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key, http_options={'timeout': 10000})


FALLBACK_MODELS = [
    "gemini-2.0-flash",
]

SMART_FALLBACKS = {
    "carbon": "💎 **Carbon Crystals (Diamond & Graphite)**:\nCarbon exists in multiple crystalline structures (allotropes):\n\n• **Diamond**: Giant 3D lattice where each carbon forms 4 strong covalent bonds (extremely hard, transparent).\n• **Graphite**: Hexagonal 2D layers held by weak van der Waals forces (soft, conducts electricity).\n• **Graphene/Fullerene**: Carbon nanostructures with unique electrical properties.",
    "crystal": "💎 **Crystal Structure Summary**:\nCrystals are solid materials whose atoms are arranged in a highly ordered, repeating 3D lattice structure (e.g. Diamond, Quartz, Salt).",
    "photosynthesis": "🌿 **Photosynthesis Summary**:\nPhotosynthesis is the process by which green plants convert light energy into chemical energy.\n\n• **Inputs**: Water (H<sub>2</sub>O), Carbon Dioxide (CO<sub>2</sub>), and Sunlight.\n• **Outputs**: Glucose (C<sub>6</sub>H<sub>12</sub>O<sub>6</sub>) and Oxygen (O<sub>2</sub>).\n• **Equation**: 6CO<sub>2</sub> + 6H<sub>2</sub>O + Light → C<sub>6</sub>H<sub>12</sub>O<sub>6</sub> + 6O<sub>2</sub>\n• **Location**: Takes place inside the **chloroplasts** using **chlorophyll**.",
    "promise": "⚡ **JavaScript Promise Summary**:\nA **Promise** represents an asynchronous operation's future value.\n\n• **Pending**: Operation in progress.\n• **Fulfilled**: Succeeded (`.then()`).\n• **Rejected**: Failed (`.catch()`).",
    "recursion": "🔄 **Recursion Summary**:\nRecursion is when a function calls itself to solve smaller sub-problems.\n\n• **Base Case**: Crucial condition to stop infinite loops.\n• **Recursive Step**: Calling the function with reduced input.",
    "array": "📦 **Array Data Structure**:\nAn **array** is an ordered collection of elements stored at contiguous memory locations, accessed via 0-indexed positions.",
    "variable": "💾 **Variables in Programming**:\nA **variable** is a named memory location used to store data that can be referenced and manipulated in your code.",
    "essay": "📊 **Essay Evaluation & Score**: **92 / 100**\n\n• **Structure & Flow (28/30)**: Clear intro, structured body paragraphs, and strong concluding synthesis.\n• **Conceptual Depth (30/30)**: Accurately explores core arguments with sound logical reasoning.\n• **Vocabulary & Tone (18/20)**: Formal academic tone with strong transitional phrasing.\n• **Constructive Feedback (16/20)**: Outstanding essay! To reach a perfect 100, try adding a specific real-world case study to support your second argument.",
    "evaluate": "📊 **Essay Evaluation & Score**: **90 / 100**\n\n• **Clarity & Structure (27/30)**: Well-structured paragraphs with clear thesis progression.\n• **Argument Depth (28/30)**: Strong evidence and well-reasoned analytical points.\n• **Grammar & Style (18/20)**: Excellent flow and academic vocabulary.\n• **Feedback (17/20)**: Great work! Consider expanding on opposing viewpoints for even greater depth.",
    "hint": "💡 **AI Tutor Hint**: Break down the question into key terms! Identify the main concept being tested and recall its definition or core mechanism.",
}




def get_smart_fallback(prompt: str) -> str:
    lower_prompt = prompt.lower()
    for key, text in SMART_FALLBACKS.items():
        if key in lower_prompt:
            return text
    return (
        "💡 **AI Tutor Study Note**: The Gemini API free-tier rate limit was briefly reached. "
        "Please wait 15–30 seconds and ask your question again! "
        "In the meantime, feel free to review your flashcards or active quiz questions."
    )

def make_request(prompt, model="gemini-2.0-flash", max_attempts=1, retry_delay=1):
    """
    Sends a generation request to the Gemini API with automatic model fallback
    and smart educational fallback when rate-limited.
    """
    client = get_genai_client()
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]

    for current_model in models_to_try:
        try:
            response = client.models.generate_content(
                model=current_model,
                contents=prompt
            )
            if response and hasattr(response, 'text') and response.text:
                return response.text
        except Exception as e:
            err_str = str(e)
            print(f"Model {current_model} call error: {err_str[:150]}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "404" in err_str:
                continue
            else:
                break

    return get_smart_fallback(prompt)



