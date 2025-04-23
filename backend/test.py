import os
from openai import OpenAI
from dotenv import load_dotenv

# Load your environment variables
load_dotenv()
api_key = os.getenv("OPENAI_SECRET_KEY")

# Create client
client = OpenAI(api_key=api_key)


def test_gpt4o():
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Summarize this email: Hi Ebad, just a quick reminder that your project submission is due tomorrow. Let me know if you need any help."}
            ],
            temperature=0.5,
            max_tokens=150
        )
        summary = response.choices[0].message.content
        print("✅ GPT-4o Response:\n", summary)
    except Exception as e:
        print("❌ Error while calling GPT-4o:\n", e)


if __name__ == "__main__":
    test_gpt4o()
