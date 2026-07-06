import os

from ragas import EvaluationDataset, evaluate
from ragas.metrics import Faithfulness, LLMContextRecall, FactualCorrectness

from eval_dataset import TEST_QUESTIONS
from app.rag import answer_with_fireworks_rag
from app.openai_rag import answer_with_openai_rag

from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper


def build_samples(answer_fn):
    from ragas.dataset_schema import SingleTurnSample
    samples = []
    for item in TEST_QUESTIONS:
        result = answer_fn(item["question"])
        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                retrieved_contexts=result["context"],
                response=result["response"],
                reference=item["reference"],
            )
        )
    return EvaluationDataset(samples=samples)

evaluator_llm = LangchainLLMWrapper(
    ChatOpenAI(model="gpt-4.1-mini", openai_api_key=os.environ["OPENAI_API_KEY"])
)
metrics = [
    Faithfulness(llm=evaluator_llm),
    LLMContextRecall(llm=evaluator_llm),
    FactualCorrectness(llm=evaluator_llm),
]

print("Running Fireworks pipeline over all test questions...")
fireworks_dataset = build_samples(answer_with_fireworks_rag)

print("Running OpenAI pipeline over all test questions...")
openai_dataset = build_samples(answer_with_openai_rag)

print("Scoring Fireworks pipeline with RAGAS...")
fireworks_scores = evaluate(fireworks_dataset, metrics=metrics)

print("Scoring OpenAI pipeline with RAGAS...")
openai_scores = evaluate(openai_dataset, metrics=metrics)

print("\n=== Fireworks (gpt-oss-20b) ===")
print(fireworks_scores)
print("\n=== OpenAI (gpt-4.1-mini) ===")
print(openai_scores)