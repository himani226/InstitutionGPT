import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are InstitutionGPT, a university assistant."},
        {"role": "user", "content": "Say hello in one sentence and confirm you're working."},
    ],
)
print(resp.choices[0].message.content)