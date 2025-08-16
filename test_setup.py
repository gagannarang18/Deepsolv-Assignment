import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def test_groq_client():
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
            max_tokens=10
        )
        print("✅ Groq API call successful:", response.choices[0].message.content)
    except Exception as e:
        print("❌ Groq API call failed:", str(e))

if __name__ == "__main__":
    test_groq_client()
