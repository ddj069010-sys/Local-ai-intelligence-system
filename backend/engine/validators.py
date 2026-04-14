from .utils import call_ollama

async def validate_response(text: str) -> str:
    prompt = f"""
    Check this answer for:
    * factual errors
    * hallucinations
    * missing steps

    If correct → return as is
    If wrong → fix it

    Answer:
    {text}
    """
    return await call_ollama(prompt, model="phi3:mini")
