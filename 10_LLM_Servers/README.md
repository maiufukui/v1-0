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