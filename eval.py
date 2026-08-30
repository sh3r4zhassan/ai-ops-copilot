import requests
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

from eval_dataset import EVAL_QUESTIONS
from tools import search_runbooks

AGENT_URL = "http://localhost:5000/diagnose"
API_KEY = "your-api-key-here"

judge_llm = ChatOllama(model="llama3.2:3b")
judge_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

records = []
for item in EVAL_QUESTIONS:
    question = item["question"]
    contexts = [search_runbooks(question)]

    response = requests.post(
        AGENT_URL,
        headers={"X-API-Key": API_KEY},
        json={"question": question},
    )
    answer = response.json().get("answer", "")

    records.append({
        "question": question,
        "contexts": contexts,
        "answer": answer,
        "ground_truth": item["ground_truth"],
    })
    print(f"Collected response for: {question}")

dataset = Dataset.from_list(records)

result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision],
    llm=judge_llm,
    embeddings=judge_embeddings,
)

print(result)
result.to_pandas().to_csv("eval_results.csv", index=False)
print("Saved detailed results to eval_results.csv")
