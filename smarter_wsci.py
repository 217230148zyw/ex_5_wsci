from pathlib import Path
from ollama import chat
import json
import re


question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

## WRITE ##
service_status = {
    "wifi": "operational"
}

state = {
    "problem": question,
    "wi_fi status": "operational",
    "wi-fi_check": True
}

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

with open("state.json", "r") as file:
    state = json.load(file)

print(state)


## SELECT CONTEXT FILES BASED ON QUESTION
## Create the function that takes the student's question, takes some keywords and chooses the relevant files from the knowledge base. Return a list of the selected files.
## For example, if the question has the kyeword "print" or "printer", then the function should return the file "knowledge/printer_setup.txt" in a list.
def select_context(question):
    keywords = {
        "wifi_setup.txt": ["wifi", "wi-fi", "eduroam", "wireless", "laptop", "connect", "campus network"],
        "password_changes.txt": ["password", "passwd", "credential", "login", "changed my"],
        "service_status.txt": ["status", "outage", "down", "operational", "not working"],
        "email_setup.txt": ["email", "mail", "outlook", "mailbox"],
        "vpn.txt": ["vpn", "remote access", "off campus"],
        "printing.txt": ["print", "printer", "printing"],
        "classroom_projectors.txt": ["projector", "display", "classroom", "hdmi", "screen"],
    }

    question_lower = question.lower()
    selected = []
    for filename, words in keywords.items():
        if any(word in question_lower for word in words):
            selected.append(f"knowledge/{filename}")
    return selected


selected_files = select_context(question)

## READ SELECTED FILES and add their contents to the context variable.
context = ""
for file in selected_files:
    context += Path(file).read_text()
    context += "\n\n"

## 
## COMPRESS CONTEXT
## Add logic to compress the context from above by calling Qwen with "context" and the "question" as the parameter
## The response from Qwen should be the compressed context. Store it in a variable called "compressed_context" 
def compress_context(context, question):
    system_prompt = """
You are a context compression assistant.
You receive a block of university IT information and a student's question.
Extract ONLY the information that is relevant to answering the question.
Keep the actionable steps and the key facts. Do not add anything yourself.
"""
    user_prompt = f"""
Information:
{context}

Question: {question}

Relevant information only:
"""
    response = chat(
        model="qwen3:8b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.message.content


compressed_context = compress_context(context, question)


## Print the length of the compressed context
print(len(compressed_context))

## Now, call Qwen again with the compressed context and the student's question. Store the response in a variable called "response" and print the response from Qwen.
## Ensure the model produces a structured output 
final_system_prompt = """
You are an IT support assistant for a university.
You must respond ONLY with a single, valid JSON object. Do not include any
conversational filler, markdown formatting blocks (like ```json), or extra text.

JSON Schema:
{
  "diagnosis": "string - what is likely wrong",
  "device": "string - the affected device",
  "is_wifi_outage": boolean,
  "steps": ["string - actionable troubleshooting steps"]
}
"""

final_user_prompt = f"""
Compressed university information:
{compressed_context}

What we already know from the state:
{json.dumps(state, indent=2)}

Student support request:
{question}
"""

response = chat(
    model="qwen3:8b",
    messages=[
        {"role": "system", "content": final_system_prompt},
        {"role": "user", "content": final_user_prompt},
    ],
)

raw_output = response.message.content
print(raw_output)


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0))


result = extract_json(raw_output)


## WRITE the above output in an artifact called "state"
state["diagnosis"] = result["diagnosis"]
state["device"] = result["device"]
state["is_wifi_outage"] = result["is_wifi_outage"]
state["recommended_steps"] = result["steps"]

with open("state.json", "w") as file:
    json.dump(state, file, indent=2)
## Update the rest of the code so that it uses the "state" artifact as part of the context. 
## It is important to ensure that the model uses only the relevant parts from the "state" artifact and not the entire artifact.
## For this, you may have to think of a good structure for the "state" artifact and how to use it in the context.
diagnostic_context = {
    "problem": question,
    "device": "Windows laptop",
    "wifi_status": state.get("wi_fi status", "operational")
}

report_context = {
    "total_wifi_cases": 37,
    "resolved_cases": 29,
    "unresolved_cases": 8
}

classifier_prompt = """
Classify the following support request as either 'diagnostic' (the user has
a specific device problem to fix) or 'report' (the user wants aggregated
statistics / numbers). Reply with ONLY one word: diagnostic or report.
"""

classifier = chat(
    model="qwen3:8b",
    messages=[
        {"role": "system", "content": classifier_prompt},
        {"role": "user", "content": question},
    ],
)

task_type = classifier.message.content.strip().lower()
print(task_type)

if "report" in task_type:
    active_context = report_context
else:
    active_context = diagnostic_context

print(json.dumps(active_context, indent=2))


