## This file is a bad way of managing context. 

from pathlib import Path
from ollama import chat


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""


context = ""

for file in Path("knowledge").glob("*.txt"):
    context += file.read_text()
    context += "\n\n"

## Make a call to Qwen with student's question and the context from the knowledge base.
system_prompt = """
You are an IT support assistant for a university.
Answer the student's support request using ONLY the university
information provided below. Be concise and practical.
"""

user_prompt = f"""
Student support request:
{question}

University information:
{context}
"""

response = chat(
    model="qwen3:8b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
)



## Just for fun, print the total length of the context
print(
    "Context characters:",
    len(context)
)

## Print the response from Qwen
print("\nAI response:")
print(response.message.content)