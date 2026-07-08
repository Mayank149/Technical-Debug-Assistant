class PromptBuilder:

    def build(self, context, question):

        prompt = """
You are an expert technical debugging assistant.

Answer ONLY using the provided context.

Rules:
- Use only the supplied context.
- Do not invent information.
- If the answer cannot be found in the context, reply exactly:
"I don't know based on the available knowledge."
- Combine information from multiple sources when appropriate.
- Do not mention retrieval scores.

=========================
CONTEXT
=========================

"""

        for document in context:

            prompt += f"Source: {document['source']}\n\n"

            for item in document["chunks"]:

                chunk = item["chunk"]

                text = chunk.text.strip()

                lines = text.split("\n")

                # Remove duplicated markdown heading
                if lines and lines[0].startswith("##"):
                    text = "\n".join(lines[1:]).strip()

                prompt += f"### {chunk.metadata.heading}\n"
                prompt += text + "\n\n"

            prompt += "=" * 60 + "\n\n"

        prompt += f"""
=========================
QUESTION
=========================

{question}

=========================
ANSWER
=========================
"""

        return prompt