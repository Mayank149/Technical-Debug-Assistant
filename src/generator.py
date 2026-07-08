from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


class Generator:

    def __init__(self):

        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

        self.model = "llama-3.3-70b-versatile"

    def generate(self, prompt):

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical debugging assistant. "
                        "Answer ONLY using the provided context. "
                        "If the answer cannot be found in the context, "
                        "reply exactly: "
                        "'I don't know based on the available knowledge.' "
                        "Never hallucinate."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,
            max_tokens=512

        )

        return response.choices[0].message.content