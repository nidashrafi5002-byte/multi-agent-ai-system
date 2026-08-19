import os
from dotenv import load_dotenv
from datetime import datetime
from tools.groq_utils import create_chat_completion

load_dotenv()

def run_general_pipeline(user_query: str) -> str:

    print("\n" + "="*60)
    print("   GENERAL Q&A PIPELINE STARTED")
    print("="*60)

    print("\n💬 Answering your question...")

    prompt = f"""
    You are a helpful, knowledgeable AI assistant.
    Answer the user's question in a clear, detailed,
    and easy to understand way.

    If the question is about a technical topic,
    provide examples to make it clearer.

    If the question is about a concept, explain it
    simply with real world analogies.

    IMPORTANT: Always detect the language of the user's
    message and respond in that SAME language.
    If user writes in Hindi, respond in Hindi.
    If user writes in Japanese, respond in Japanese.
    If user writes in Tamil, respond in Tamil.
    Never switch languages unless user asks.

    User Question: {user_query}

    Provide a well structured answer with:
    1. Direct answer first
    2. Detailed explanation
    3. Example if needed
    4. Key takeaway at the end
    """

    response = create_chat_completion(
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content.strip()

    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    final_response = f"""
{'='*60}
        GENERAL Q&A
{'='*60}
Question : {user_query}
Date     : {now}
{'='*60}

{answer}

{'='*60}
    """

    return final_response