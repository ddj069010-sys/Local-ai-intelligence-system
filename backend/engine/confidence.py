from .utils import call_ollama_json

async def confidence_check(answer: str) -> float:
    prompt = f"""
    Rate confidence (0–1):

    Answer:
    {answer}

    Return JSON: {{"confidence": 0.0}}
    """
    res = await call_ollama_json(answer, model="phi3:mini", system=prompt)
    return res.get("confidence", 0.5)
