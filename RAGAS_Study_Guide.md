# RAGAS Study Guide
**Paper:** *Ragas: Automated Evaluation of Retrieval Augmented Generation* — Es, James, Espinosa-Anke, Schockaert (Exploding Gradients / Cardiff University)

---

## ⚡ One-Page Summary

**What is RAGAS?** A framework for *reference-free, automated evaluation* of RAG (Retrieval Augmented Generation) pipelines — no human annotations or ground-truth answers required.

**Why RAG?** LLMs have two hard limits: they can't answer about post-training events, and they struggle with rare knowledge. RAG fixes this by retrieving relevant passages and feeding them into the LLM alongside the question.

**Why is evaluating RAG hard?** Perplexity doesn't predict downstream performance; closed models (GPT-4, ChatGPT) don't expose token probabilities; standard QA datasets use short extractive answers that aren't representative; human annotation is slow and expensive.

**RAGAS's solution:** Use an LLM to evaluate three complementary quality dimensions:

| Metric | Question it answers | Formula |
|--------|-------------------|---------|
| **Faithfulness** | Is the answer grounded in the context? | F = \|verified statements\| / \|total statements\| |
| **Answer Relevance** | Does the answer actually address the question? | AR = avg cosine sim(original q, reverse-generated qᵢ) |
| **Context Relevance** | Is the retrieved context focused / noise-free? | CR = extracted sentences / total sentences in context |

**How each metric works:**
- *Faithfulness*: Decompose answer → atomic statements → LLM verifies each against context (Yes/No)
- *Answer Relevance*: LLM generates n questions from the answer → embed all → measure cosine similarity with the original question
- *Context Relevance*: LLM extracts only the sentences from context truly needed to answer the question

**WikiEval dataset:** 50 post-2022 Wikipedia pages (beyond ChatGPT's training cutoff) with human-annotated pairwise comparisons across all three dimensions.

**Results vs. baselines (accuracy vs. human judges):**

| Method | Faithfulness | Answer Relevance | Context Relevance |
|--------|:-:|:-:|:-:|
| **RAGAS** | **0.95** | **0.78** | **0.70** |
| GPTScore | 0.72 | 0.52 | 0.63 |
| GPTRanking | 0.54 | 0.40 | 0.52 |

**Key takeaways:**
- The three metrics are complementary — a system can fail each independently
- Decomposing answers into atomic statements before verification improves faithfulness precision
- Reverse question generation is an elegant reference-free proxy for answer relevance
- Context relevance is the hardest to evaluate; ChatGPT struggles with long contexts ("lost in the middle")
- RAGAS integrates with LlamaIndex and LangChain; all prompts run on `gpt-3.5-turbo-16k`

---

## 1. Problem & Motivation

**RAG (Retrieval Augmented Generation)** systems address two core limitations of LLMs:
1. LLMs can't answer about events after their training cutoff
2. LLMs struggle to memorize rare/long-tail knowledge

RAG works by: *retrieving relevant passages from a corpus → feeding them to the LLM alongside the question → generating an answer grounded in that context.*

**Why automated evaluation is hard:**
- Standard perplexity-based evaluation doesn't predict downstream performance well
- Many closed-source models (ChatGPT, GPT-4) don't expose token probabilities
- QA benchmarks use short extractive answers — not representative of real RAG use
- Human annotation is expensive and slow
- No single metric captures all quality dimensions

**RAGAS's core claim:** You can evaluate RAG systems in a *reference-free* way (no ground truth answers needed) by using an LLM as an evaluator.

---

## 2. The Three Quality Dimensions (Core Metrics)

These are the most exam-critical concepts. Know each definition, what it penalizes, and how it's computed.

### 2.1 Faithfulness
> *Is the answer grounded in the retrieved context?*

**Why it matters:** Prevents hallucinations. Especially critical in domains like law where facts change and accuracy is essential.

**How it's computed (3 steps):**
1. **Extract statements** — prompt the LLM to decompose the answer into atomic statements S = {s₁, s₂, ..., sₙ}
2. **Verify each statement** — for each sᵢ, prompt the LLM to determine if it can be inferred from context c(q) using a binary verdict (Yes/No)
3. **Score:** `F = |V| / |S|` where |V| = number of supported statements, |S| = total statements

**Key insight:** Decomposing into shorter statements before verification makes the task more precise than verifying whole sentences.

---

### 2.2 Answer Relevance
> *Does the answer directly and completely address the question?*

**What it penalizes:**
- Incomplete answers
- Redundant information
- Answers that drift off-topic

**Note:** Does NOT penalize factual errors — that's Faithfulness's job.

**How it's computed:**
1. Prompt the LLM to generate *n* questions qᵢ that the given answer a(q) would answer
2. Embed all generated questions using `text-embedding-ada-002`
3. Compute cosine similarity sim(q, qᵢ) between original question q and each generated qᵢ
4. **Score:** `AR = (1/n) Σ sim(q, qᵢ)`

**Key insight:** If the answer is truly relevant to the question, reverse-engineered questions should closely match the original.

---

### 2.3 Context Relevance
> *Is the retrieved context focused and free of irrelevant information?*

**Why it matters:**
- Feeding irrelevant context wastes LLM tokens (cost)
- Long irrelevant context degrades LLM performance (the "lost in the middle" problem — Liu et al., 2023)

**How it's computed:**
1. Prompt LLM to extract the subset of sentences from c(q) that are crucial for answering q
2. If no relevant sentences found, LLM returns "Insufficient Information"
3. **Score:** `CR = (# extracted sentences) / (total sentences in context)`

**Key insight:** Lower CR means too much noise in the retrieved context. This is the *hardest metric to evaluate* — ChatGPT often struggles with it for long contexts.

---

## 3. RAGAS vs. Baseline Methods

| Method | Approach | Faith. Accuracy | Ans.Rel. Accuracy | Ctx.Rel. Accuracy |
|--------|----------|:-:|:-:|:-:|
| **RAGAS** | Decompose + verify / reverse QA / sentence extraction | **0.95** | **0.78** | **0.70** |
| GPTScore | Ask ChatGPT to rate 0–10 on each dimension | 0.72 | 0.52 | 0.63 |
| GPTRanking | Ask ChatGPT to pick the better answer/context | 0.54 | 0.40 | 0.52 |

**Takeaways:**
- RAGAS substantially outperforms both baselines across all three metrics
- Faithfulness is the easiest to evaluate automatically (0.95)
- Context Relevance is the hardest (0.70) — LLMs struggle to select crucial sentences from long contexts
- Answer Relevance (0.78) is lower partly because differences between high/low relevance answers are often subtle

---

## 4. WikiEval Dataset

RAGAS introduced this dataset to validate the metrics (no public dataset existed).

**Construction:**
- 50 Wikipedia pages covering events **after Jan 2022** (beyond ChatGPT's training cutoff, ensuring no memorized answers)
- Pages selected with recent edits, prioritized
- ChatGPT used to generate one question per page's introductory section
- ChatGPT used to answer each question with context provided

**For each dimension, two contrasting answers/contexts were constructed:**

| Dimension | High Quality | Low Quality |
|-----------|-------------|-------------|
| Faithfulness | Standard RAG answer | Answer generated *without* context |
| Answer Relevance | Direct complete answer | Intentionally incomplete/evasive answer |
| Context Relevance | Only relevant sentences | Relevant sentences + back-link content padded in |

**Human annotation:**
- 2 annotators, fluent English, clear instructions
- Agreement: ~95% on Faithfulness & Context Relevance, ~90% on Answer Relevance
- Disagreements resolved by discussion

---

## 5. Related Work & Prior Approaches (Know for Comparisons)

### Detecting Hallucinations
| Approach | Method | Limitation |
|----------|--------|------------|
| Few-shot prompting | Zhang et al., 2023 | Existing models still struggle |
| BARTScore | Conditional probability of generated text | Needs access to model probabilities |
| SelfCheckGPT | Sample multiple answers; factual answers are stable | Slow; requires many samples |
| Azaria & Mitchell | Classify hidden layer weights | Needs model internals — unsuitable for API-only models |
| Knowledge base linking | Min et al., 2023 (FActScore) | Not always possible |

### Reference-Based Text Evaluation
- **BERTScore** — contextual embeddings to compare generated vs. reference
- **MoverScore** — Earth Mover Distance over BERT embeddings
- **BARTScore** — precision (P(generated|reference)) and recall (P(reference|generated))

**All require ground-truth reference answers** → RAGAS's advantage is being *reference-free*.

### LLM-as-Judge Approaches
- **GPTScore (Fu et al., 2023)** — use token probabilities, describe aspect in prompt
- **Direct scoring (Wang et al., 2023a)** — ask ChatGPT for 0-100 or 5-star score; sensitive to prompt design
- **LLM ranking (Wang et al., 2023b)** — order of presented answers biases results

---

## 6. Technical Implementation Details

- All prompts evaluated using **gpt-3.5-turbo-16k** via OpenAI API
- Embeddings: **text-embedding-ada-002** (for answer relevance cosine similarity)
- Integrates with **LlamaIndex** and **LangChain** — the dominant RAG frameworks
- Open source: `https://github.com/explodinggradients/ragas`

---

## 7. Key Insights & Exam-Likely Arguments

1. **Reference-free evaluation is possible and valuable.** RAGAS shows you don't need human-annotated ground truth to get meaningful quality signals.

2. **The three metrics are complementary, not redundant.** A system can fail on any one dimension independently:
   - High faithfulness but low answer relevance → answers questions not asked
   - High answer relevance but low faithfulness → answers correctly but hallucinates
   - High both but low context relevance → retrieval system is inefficient

3. **Decomposition improves evaluation.** Breaking an answer into atomic statements before verifying faithfulness is more precise than checking whole sentences.

4. **Reverse generation as a relevance proxy.** Generating questions from answers (for answer relevance) is a creative and effective way to avoid needing reference answers.

5. **Context length is a real bottleneck.** The "lost in the middle" problem (Liu et al., 2023) makes context relevance important beyond just cost savings.

6. **LLM-as-evaluator limitations.** ChatGPT struggles with context relevance for long contexts — there's still headroom for improvement, especially in the CR metric.

7. **WikiEval design principle:** Using post-2022 Wikipedia content ensures the LLM can't rely on memorized knowledge — the context is genuinely necessary to answer.

---

## 8. Limitations (Likely Exam Material)

- Context relevance accuracy (0.70) still has room to improve
- All metrics rely on GPT-3.5 as the evaluator — quality is bounded by that model's capabilities
- Answer relevance only captures relevance, not factual correctness
- The WikiEval dataset is relatively small (50 pages / 50 questions)
- Evaluation cost scales with LLM API calls (multiple prompts per question)

---

## Quick Recall: Formula Sheet

| Metric | Formula |
|--------|---------|
| Faithfulness | F = \|V\| / \|S\| |
| Answer Relevance | AR = (1/n) Σ sim(q, qᵢ) |
| Context Relevance | CR = extracted sentences / total sentences |
