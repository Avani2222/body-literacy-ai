from openai import OpenAI
from app.models.user_data import UserData
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def generate_insight(data, db, user_id: int=None):
    user_id_val = str(user_id) if user_id is not None else data.user_id
    # 1. Get only last N records (IMPORTANT)
    history = (
        db.query(UserData)
        .filter(UserData.user_id == user_id_val)
        .order_by(UserData.id.desc())   # latest first
        .limit(10)                        # LIMIT HISTORY SIZE
        .all()
    )

    # 2. Convert to text safely
    history_text = "\n".join([
        f"Cycle Phase: {h.cycle_phase}, Mood: {h.mood}, Energy: {h.energy}, Sleep: {h.sleep}"
        for h in history
    ])

    # 3. Keep prompt small and clean
    prompt = f"""
    You are a health assistant focused on female physiology.

    Current Data:
    - Cycle Phase: {data.cycle_phase}
    - Mood: {data.mood}
    - Energy: {data.energy}
    - Sleep: {data.sleep}

    Recent History (last 5 entries):
    {history_text}

    Explain:
    1. What is happening biologically
    2. Why user feels this way
    3. Give 2-3 pr
    actical suggestions
    Do not write anything apart from these
    """

    response = client.chat.completions.create(
        model="mistralai/mistral-small-3.2-24b-instruct",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

