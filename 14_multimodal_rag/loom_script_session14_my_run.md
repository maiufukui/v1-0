# Loom Script — Session 14: Multi-Modal RAG (6 min)

*Screen-share the notebook, scrolling to the section/output being described. Do not read code line by
line — point at outputs and explain what they demonstrate.*

---

## [0:00–0:40] The core problem

"Today I am walking through Session 14, a lab about one mismatch: LangChain's embedding interface only
understands text. It is not possible to pass `OpenAIEmbeddings` a PNG, even though the chat model itself
can interpret images directly. This mismatch is exactly why cross-modal retrieval is difficult: the real
details in a chart live in its pixels, not necessarily in whatever caption was written about it. The
notebook builds three different approaches to bridge that gap for retrieval, then a separate step for
what happens once the correct image has been found and the model needs to read it."

*[Screen: Section 1, scroll to the three-strategy list]*

---

## [0:40–1:40] The VLM has two separate jobs

"The mental model underlying the notebook: the VLM is used twice, for two different purposes. At
ingestion, it examines each chart once and produces a structured description — this is parsing, and it is
what makes the image findable at all. Here is what it produced for the revenue chart:"

*[Screen: Section 4.2 output — parsed_images JSON: kind, title, takeaway, data_points Q1–Q4]*

"Then, at query time, once that chart has been retrieved, the actual image is reloaded and passed back to
the model — this is reading, and it is what makes the answer trustworthy rather than merely plausible."

---

## [1:40–3:00] Three retrieval strategies, and the modality gap is real

"Section 5 builds three approaches for making a text query find an image. Strategy A generates a caption
for every image at ingestion and embeds the caption as plain text — simple, and it remained at recall@3 =
1.00 across both gold-question tests. Strategy B places text and images in a single CLIP space so a query
can match pixels directly, without a caption in between — and this is where the modality gap appears in
practice, not only in theory: recall@3 measured 0.25 on the first gold set, and rose only to 0.30 after
two additional questions were added in Activity 2. Text queries consistently sit closer to text chunks
than to image pixels within that shared space, so the chart is quietly outranked even when an
images-only search would have found it. Strategy C keeps text and images in separate stores and merges
results by rank using Reciprocal Rank Fusion rather than raw score — and it matched Strategy A at 1.00 in
both tests, without the cost of captioning at ingestion. RRF matters specifically because text and image
searches come from different embedding models with different score scales — comparing 0.82 to 0.75 across
modalities is not meaningful, but comparing rank position within each list is."

*[Screen: Section 8.1 output — recall@3 table; then Activity #2 — expanded results]*

---

## [3:00–4:00] Generation: reading the actual pixels

"Even after retrieval identifies the correct chart, the caption is not reused — the source image is
reloaded and the real pixels are sent at answer time. A concrete example illustrates why this matters:
the question 'which quarter had the highest revenue and by how much' produced the answer Q4 at $27M,
ahead of Q2 by $9M — read directly from the bar chart rather than summarized from an earlier caption."

*[Screen: Section 7.2 output — the Q4 revenue $27M answer, and the March churn / 6.2% answer]*

"The churn example follows the same pattern — it correctly identified March at 6.2% and connected it to
the billing bug documented separately in text, combining an exact figure from an image with context from
text in a single grounded answer."

---

## [4:00–4:20] The same pattern, extended to video

"Section 9 applies this same two-job pattern — parse to make content searchable, then read the real
source to answer — to video: transcript segments plus sampled keyframes, aligned by timestamp. A question
about the APAC latency issue produced the exact figure along with the moment it occurred:"

*[Screen: Section 9.6 output — APAC 240ms answer with [00:26-00:37] citation]*

"240ms P95 in APAC, the worst of any region, resolved with a regional cache — cited to a twelve-second
window in the actual video rather than a vague reference."

---

## [4:20–4:40] The one extension actually completed: swapping the VLM

"For the advanced activity, only the provider swap was completed — embeddings remained on OpenAI's
`text-embedding-3-small`, but `VLM_MODEL` was switched from GPT-4o to Claude Sonnet 4.6, and the pipeline
was rerun in full. Recall@3 did not change: still 1.00, 0.25, and 1.00, and the same result held on the
expanded evaluation set. This outcome makes sense once each strategy's dependencies are considered
separately: Strategy B and Strategy C's image retrieval runs on local CLIP, which never touches the VLM,
so a provider swap cannot affect them. Strategy A does depend on the VLM, but only for caption quality —
and on a six-chart corpus, both models produced similarly strong captions, so the same top-three results
were returned either way."

---

## [4:40–5:00] Recap: the pipeline, summarized

"In summary: the VLM performs two jobs — parsing to find, reading to confirm — a measured tradeoff exists
across three retrieval strategies, where the modality gap reduced Strategy B's recall by roughly seventy
points, and generation always grounds its answer in the source pixels rather than a lossy caption. The
architecture remains the same whether the source is a chart or a video frame. That is the pipeline — the
following section covers what would come next."

---

## [5:00–6:00] Lessons learned, and lessons still to learn

"Three areas would still need to be learned to bring this to production. First, ingestion and indexing at
scale: this lab handled only six charts, but a real corpus would require parallel workers, retries, JSON
schema validation, persistent Qdrant collections, incremental upserts, and a mechanism to keep captions
and vectors synchronized as source documents change. Second, retrieval beyond dense search plus RRF: only
top-three cosine similarity was tested here, and production retrieval would require hybrid search
combining BM25 and dense methods, metadata filters, cross-encoder reranking, and tuning per modality —
particularly because a small, hand-written gold set is not sufficient to catch every failure mode. Third,
generation at scale: sending every retrieved image as raw pixels is workable on a small corpus, but it
does not scale — token usage, latency, and cost all increase quickly, and techniques such as capping the
number of images sent, downscaling them, prompt caching, post-hoc citation checks, guardrails, and
provider flexibility would all be needed.

"Three things were learned in this session. First, text-only embeddings require real workarounds for
images: LangChain's embedding API accepts only strings, so a PNG cannot be embedded directly, and this
notebook's three strategies represent three different answers to that constraint — caption-to-text
embedding, a unified CLIP space, or separate stores fused with RRF — each trading off simplicity, cost,
and retrieval quality differently. Second, CLIP enables cross-modal search but has real limits: a text
query can match an image vector within that same CLIP space, and an images-only search can retrieve
directly from pixels, but the modality gap means text documents frequently outrank charts in a unified
search, and CLIP itself cannot read precise details from a chart — it matches visual concepts, not axis
values. Third, retrieval and generation should be evaluated separately: finding the correct chunk is a
distinct problem from answering the question correctly, and a pipeline can retrieve perfectly and still
fail if it passes only a caption to the model at generation time rather than the real image."

---

## [6:00–6:10] Close

"This concludes Session 14 — a working multi-modal pipeline, along with a clear view of what would be
required to bring it to production."

---

**Total: ~1,070 words / ~6 min at a relaxed pace.**
