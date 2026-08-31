import json
import os
import sys
import requests
from tools import TOOLS

OLLAMA_URL = f"http://{os.getenv('OLLAMA_HOST', 'localhost')}:11434/api/generate"
MODEL_NAME = "sre-copilot"

SYSTEM_PROMPT = """You are an SRE agent that diagnoses Kubernetes issues.
You have access to these tools:

- search_runbooks(query: string): search internal runbooks for relevant guidance
- get_pod_status(namespace: string): list pods and their status in a namespace

On each turn, respond with ONLY a JSON object, nothing else, in ONE of these two forms:

To use a tool:
{"thought": "...", "action": "tool_name", "action_input": {"query": "..."}}

To give your final answer:
{"thought": "...", "final_answer": "..."}

Think step by step. Only give a final_answer once you actually have enough information from tool results.
Never use final_answer to describe what you are about to do next — it must state an actual conclusion,
reached after using at least one tool and reading its real result.
"""

def call_llm(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
    )
    return response.json()["response"]


def run_agent(user_question: str, max_steps: int = 7) -> str:
    transcript = f"{SYSTEM_PROMPT}\n\nUser question: {user_question}\n"
    tools_used = 0

    for step in range(max_steps):
        raw = call_llm(transcript)
        print(f"--- step {step + 1} ---\n{raw}\n")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            transcript += "\n(Your last response was not valid JSON. Respond with only the JSON object.)\n"
            continue

        if "final_answer" in parsed:
            if tools_used == 0:
                transcript += (
                    "\n(You gave a final_answer without using any tool first. "
                    "You must call search_runbooks or get_pod_status at least once "
                    "and use its real result before answering. Try again.)\n"
                )
                continue
            return parsed["final_answer"]

        action = parsed.get("action")
        action_input = parsed.get("action_input", {})

        if action not in TOOLS:
            transcript += f"\nObservation: unknown tool '{action}'.\n"
            continue

        try:
            observation = TOOLS[action](**action_input)
            tools_used += 1
        except TypeError as e:
            observation = f"error calling tool '{action}': {e}. Check the argument names and try again."

        transcript += (
            f"\nThought: {parsed.get('thought', '')}\n"
            f"Action: {action}({action_input})\n"
            f"Observation: {observation}\n"
        )

    return "Agent could not reach a final answer within the step limit."

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Why might my pods be crashing?"
    print("\n=== FINAL ANSWER ===")
    print(run_agent(question))
