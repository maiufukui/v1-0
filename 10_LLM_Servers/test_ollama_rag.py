from app.ollama_rag import answer_with_ollama_rag
from app.rag import answer_with_fireworks_rag
from app.openai_rag import answer_with_openai_rag
import time

result = answer_with_ollama_rag("What are the core vaccines recommended for cats?")
print("Response:", result["response"])
print("\nContext chunks used:", len(result["context"]))
for chunk in result["context"]:
    print("-", chunk[:100], "...")

start = time.time()
answer_with_ollama_rag("What are the core vaccines recommended for cats?")
print("Ollama:", time.time() - start, "seconds")

start = time.time()
answer_with_fireworks_rag("What are the core vaccines recommended for cats?")
print("Fireworks:", time.time() - start, "seconds")

start = time.time()
answer_with_openai_rag("What are the core vaccines recommended for cats?")
print("OpenAI:", time.time() - start, "seconds")