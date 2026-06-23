from openai import OpenAI
from app.models.user_data import UserData
from app.rag.retrieve import retrieve
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def generate_insight(data, db, user_id: int=None):
    user_id_val=(
        str(user_id)
        if user_id is not None
        else data.user_id
    )
    print("user_id- done")
    history = (
        db.query(UserData)
        .filter(UserData.user_id == user_id_val)
        .order_by(UserData.id.desc())
        .limit(10)
        .all()
    )

    history_text = "\n".join([
        f"Cycle Phase: {h.cycle_phase}, "
        f"Mood: {h.mood}, "
        f"Energy: {h.energy}, "
        f"Sleep: {h.sleep}"
        for h in history
    ])
    print("history_text-done")
    retrieval_query = f"""
    User Context
    Cycle Phase:{data.cycle_phase}
    Mood: {data.mood}
    Energy: {data.energy}
    Sleep:{data.sleep}
    Explain the biological rasons behind the user's current state.
    """
    retrieved_chunks = retrieve(
        query=retrieval_query,
        top_k=5
    )
    print("retreival-done")
    evidence_text = ""
    for idx, chunk in enumerate(
        retrieved_chunks, 
        start=1
    ):
        evidence_text +=f"""
        [{idx}]
        Source:{chunk['source']}
        Page:{chunk['page']}
        Evidence:{chunk['text']}
        """
    confidence = "Low"
    if retrieved_chunks:
        avg_score = (
            sum(
                chunk["score"]
                for chunk in retrieved_chunks
            )
            / len(retrieved_chunks)
        )
        if avg_score > 0.85:
            confidence = "High"
        elif avg_score > 0.75:
            confidence = "Medium"
    print("evidence- done")

    prompt = f"""
    You are an evidence-based women's health assistant.

    Use ONLY the research evidence provided.

    Do not invent information.

    If evidence is weak,
    say so clearly.


    CURRENT DATA

    Cycle Phase:
    {data.cycle_phase}

    Mood:
    {data.mood}

    Energy:
    {data.energy}

    Sleep:
    {data.sleep}


    RECENT HISTORY

    {history_text}


    RESEARCH EVIDENCE

    {evidence_text}


    TASK

    1. Explain what is happening biologically.
    2. Explain why the user may feel this way.
    3. Give 2-3 practical suggestions.
    4. Cite evidence using [1], [2], etc.
    5. Use only the provided evidence.

    IMPORTANT:

    Return your response in valid markdown.

    Use EXACTLY this structure:

    # Health Insight

    ## Summary
    A short 2-3 sentence overview.

    ## Biological Explanation
    Explain the physiology using evidence.
    Write in bullet points

    ## Why You May Feel This Way
    Explain how the user's cycle phase, mood, energy, and sleep relate to the evidence.
    Write in bullet points

    ## Recommendations
    - Recommendation 1
    - Recommendation 2
    - Recommendation 3

    ## Confidence
    {confidence}

    ## Sources
    [1] Source Name
    [2] Source Name
    Wite as [1]., [2]. ... each in a new line

    refer to the user as you.
    Do not use numbered sections.
    Use markdown headings and bullet points.
    """
    print("prompt-done")
    response = client.chat.completions.create(
        model = "mistralai/mistral-small-3.2-24b-instruct",
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    return {
        "insight": response.choices[0].message.content, 
        "confidence": confidence,
        "sources":[{
            "source": chunk["source"],
            "page": chunk["page"]
            }
            for chunk in retrieved_chunks
        ]
    }

    
# from openai import OpenAI
# from app.models.user_data import UserData
# import os
# from dotenv import load_dotenv
# load_dotenv()
# client = OpenAI(
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     base_url="https://openrouter.ai/api/v1"
# )

# def generate_insight(data, db, user_id: int=None):
#     user_id_val = str(user_id) if user_id is not None else data.user_id
#     # 1. Get only last N records (IMPORTANT)
#     history = (
#         db.query(UserData)
#         .filter(UserData.user_id == user_id_val)
#         .order_by(UserData.id.desc())   # latest first
#         .limit(10)                        # LIMIT HISTORY SIZE
#         .all()
#     )

#     # 2. Convert to text safely
#     history_text = "\n".join([
#         f"Cycle Phase: {h.cycle_phase}, Mood: {h.mood}, Energy: {h.energy}, Sleep: {h.sleep}"
#         for h in history
#     ])

#     # 3. Keep prompt small and clean
#     prompt = f"""
#     You are a health assistant focused on female physiology.

#     Current Data:
#     - Cycle Phase: {data.cycle_phase}
#     - Mood: {data.mood}
#     - Energy: {data.energy}
#     - Sleep: {data.sleep}

#     Recent History (last 5 entries):
#     {history_text}

#     Explain:
#     1. What is happening biologically
#     2. Why user feels this way
#     3. Give 2-3 pr
#     actical suggestions
#     Do not write anything apart from these
#     """

#     response = client.chat.completions.create(
#         model="mistralai/mistral-small-3.2-24b-instruct",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     return response.choices[0].message.content

