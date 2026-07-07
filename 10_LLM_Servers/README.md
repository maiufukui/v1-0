## # Session 10: LLM Servers


| 📰 Session Sheet                                        | ⏺️ Recording                                                                                                                                           | 🖼️ Slides                                                                                                                                                                         | 👨‍💻 Repo    | 📝 Homework                                                                                                                                 | 📁 Feedback                                         |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| [LLM Servers](../00_Docs/Session_Sheets/16_LLM_Servers) | [Recording!](https://us02web.zoom.us/rec/share/HDunij9p7eCXeP_OgsRDRjTdWUqiEhDBGWrFJEn1bwWR1wz1jKX6EHXSOM45d0sC.rHiyo_znZ-R8Jh6S) passcode: `D80X^YjL` | [Session 10 Slides](https://www.canva.com/design/DAG-EBu7B5A/POcowC5rDLENSPcSVpbf8g/edit?utm_content=DAG-EBu7B5A&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton) | You are here! | [Session 10 Assignment: LLM Servers](https://forms.gle/Riqvwf6KrZcCRKV86) [Demo Day Submission (3/12)](https://forms.gle/7xyuBUn69GX4v6K98) | [Feedback 3/5](https://forms.gle/W28QFWJXpSS4ZAR6A) |


**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU'RE FINISHED YOUR ASSIGNMENT !!!⚠️**

# Build 🏗️

In today's assignment, we'll be creating Fireworks AI endpoints, and then building a RAG application.

- 🤝 Breakout Room #1
  - Set-up Open Source Endpoint (Instructions [here](./ENDPOINT_SETUP.md)) ((This process may take 15-20min.))
  - Test Endpoint and Embeddings with the `endpoint_slammer.ipynb` notebook.
- 🤝 Breakout Room #2
  - Use the Open Source Endpoints to build a RAG LangGraph application



# Ship 🚢

The completed notebook and your RAG app/notebook!

### Deliverables

- A short Loom of either:
  - the notebook and the RAG application you built for the Main Homework Assignment; or
  - the notebook you created for the Advanced Build



# Share 🚀

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped a RAG application powered by open-source endpoints! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI and question-answering. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#LangChain #QuestionAnswering #RetrievalAugmented #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```



# Submitting You Homework



## Main Homework Assignment

Follow these steps to prepare and submit your homework assignment:

1. Follow the instructions in `ENDPOINT_SETUP.md`
2. Replace both `model` values in `endpoint_slammer.ipynb` with the `gpt-oss` endpoint you created in Step 1
3. Run the code cells in `endpoint_slammer.ipynb`
4. Respond to the questions in the section below
5. Build a sample RAG
6. Record a Loom video reviewing what you have learned from this session

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU HAVE FINISHED YOUR ASSIGNMENT !!!⚠️**

## Questions



### ❓ Question #1:

What is the difference between serverless and dedicated endpoints?

#### ✅ Answer:

Serverless endpoints: 

- Fireworks runs the model on shared infrastructure. You call a model ID e.g., accounts/fireworks/models/gpt-oss-20b - no deployment to create
- Pricing: Pay per token (input + output). No charge when idle 
- Setup: minimal, API key + model ID in code /.env 
- Trade offs: easy and cheap for low/medium usage, shared capacity, rate limits, less control over latency/throughput

Dedicated endpoints:

- You deploy a model onto your own GPU(s) in Fireworks 
- Pricing: Pay per GPU time (per second/hour) while replicas are running - even if you are not sending requests
- Set up: more involved, pick model, GPU type, scaling. 
- Trade offs: predictable performance, higher throughput, lower latency at scale, customer/fine tuned models - but need to manage cost and infra



### ❓ Question #2:

Why is it important to consider token throughput and latency when choosing an LLM for user-facing applications?

#### ✅ Answer:

Latency is how long users wait for a response e.g., UX, engagement

Token throughput is how many tokes the model can generate (or process) per second - often measured as tokens/sec or requests/min under load. e.g., streaming speed, concurrency (similar to 24 parallel requests in slammer notebook0, cost at scale (serverless vs dedicated), long outputs need sustained throughput 

When picking an LLM for production user-facing use, need to balance

- model size - bigger models often smarter but slower/lower throughput 
- endpoint type - serverless may hit rate limits; dedicated gives predictable throughput 
- use case - quick Q&A vs long document generation have different requirements
- scale - one user vs. thousands changes whether throughput dominates



## Activity 1: RAGAS Evaluation with Cost Analysis

Use RAGAS to evaluate your open-source Fireworks AI powered RAG app against an OpenAI `gpt-4.1-mini` powered equivalent. Compare retrieval quality, answer faithfulness, and end-to-end accuracy across both providers.

Additionally, instrument both pipelines with **LangSmith** to capture token usage and cost per query. Use LangSmith's tracing and cost dashboards to compare the total cost of running each provider at scale. Include your evaluation results, cost breakdown, and analysis in your Loom video.

**Fireworks vs. OpenAI RAG assessment:** 

**Faithfulness:** 0.793 vs 0.891 >> OpenAI more grounded

**Context recall:** 1.000 vs 0.967 >> Fireworks better 

**Factual correctness:** 0.737 vs 0.717 >> near tie, Fireworks slightly ahead

**Cost per query:** Fireworks $0.00035 vs OpenAI $0.00157 >> OpenAI is ~4.5x more expensive, despite similar total token counts (the gap is rate, not volume).

Fireworks' current serverless pricing for gpt-oss-20b ($0.07/1M input tokens, $0.035/1M cached input, $0.30/1M output tokens)

**No clean winner:** Fireworks is dramatically cheaper and wins on context recall and factual correctness, but OpenAI is meaningfully more faithful and less likely to say things not actually backed by the retrieved context. If cost matters more and questions need to better match the reference, Fireworks looks like the better deal. If minimizing hallucination/ungrounded claims is the priority, OpenAI's faithfulness edge may be worth the 4.5x premium. 

However, the judge model here is gpt-4.1-mini, the same as the OpenAI pipeline itself and could be a source of bias 

## Advanced Activity: Local Models

Swap out the Fireworks AI endpoints for **locally-running open-source models** using [Ollama](https://ollama.com/) or another local inference server of your choice. Run both your embedding model and your chat model locally, and rebuild the RAG pipeline on top of them.

- Compare quality and latency between the local setup and your Fireworks AI hosted endpoint.
- Reflect: what are the trade-offs of local models vs. managed endpoints in a production setting?

Include your findings and a demo in your Loom video.

Objective: Leverage the Fireworks-hosted embedding and chat models for fully local equivalents running on Ollama, rebuild the RAG pipeline, and compare quality and latency against the Fireworks hosted endpoints. 

**Setup:** Ollama was installed, and pulled 2 models: llama3.2 (2B chat model) and nomic embed text (embedding only model). langchain-ollama was added to pyproject.toml and installed via uv sync so that ChatOllama/OllamaEmbeddings properly pointed at Ollamas local API. 

**Build:** Created app/ollama_rag.py structurally similar to [rag.py](http://rag.py) and openai_rag.py with the same state schema, same retrieve to generate graph, same content/query/prompt. All unchanged to ensure comparison is isolated to the underlying model. The only difference is embedding and chat model constructs. 

**Quality:** 

=== Fireworks (gpt-oss-20b) ===

{'faithfulness': 0.8627, 'context_recall': 0.9667, 'factual_correctness(mode=f1)': 0.6910}

=== OpenAI (gpt-4.1-mini) ===

{'faithfulness': 0.8900, 'context_recall': 0.9167, 'factual_correctness(mode=f1)': 0.6980}

=== Ollama (llama3.2 / nomic-embed-text) ===

{'faithfulness': 0.8633, 'context_recall': 0.9167, 'factual_correctness(mode=f1)': 0.5300}

Faithfulness and context recall for Ollama are in line to OpenAI and Fireworks. nomic-embed-text is pulling relevant chunks (0.9167). The biggest gap is factual correctness at 0.530, meaningfully below OpenAI (0.69) and Fireworks (0.69).

At 3B parameter, it is not surprising the performance is lower than a 20B+ hosted model, even when it's reading the same retrieved context. 

**Latency:** 

ollama:  2.48 sec/2.94 sec

Fireworks: 4.60 sec/6.90 sec

OpenAI: - / 4.82 sec

Ran 3 times, with adding OpenAI in the last run as I was curious. 

Running 3 times shows that Olla is the fastest, and Fireworks slowest. This may be due to the fact that llama3.2 is the smallest model, so model size might be the leading cause though infrastructure location (local vs hosted) could also impact the results. 

However, this lab did not capture or test the benefit of hosted infrastructure which is sustained throughput under concurrent load (tested in this lab with the 24 concurrent requests). Fireworks is built for product systems to manage spikes and concurrent runs. Fireworks is able to manage these operations that local wont be able to do as (1) multiple GPUs, load balnaced; (2) continuous batching where single GPU process token generation can handle several requests simultanenously; and (3) horizontal scaling where hosted platforms can spin up to absorb traffic 

**Reflection**: local vs managed endpoint tradeoffs 

Local models cost nothing per query, keeps everything on device, and are not subect to shared rate limits. However, given the meaningful drop in factual correctness (0.5 vs 0.69) with the smaller local model and no evidence it can sustain concurrent production traffic the same way a managed endpoint can and does not provide support for key operational concerns (i.e. uptime, scaling, monitoring, model upgrades available in managed endpoints)

However, given the cost, access, and ease of use, local models are probably a good fit for prototying, privacy sensitive work that is not dependent on production capabilities 





