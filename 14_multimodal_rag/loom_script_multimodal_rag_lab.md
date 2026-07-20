# Loom Script — Multi-Modal RAG Lab (5 min, concept-first)

*Tone: conversational, screen-share of the notebook scrolling along as you talk. Don't dwell on code — point at section headers and outputs, not syntax.*

---

## [0:00–0:30] Cold open — the one-sentence problem

"This lab is about one problem: your knowledge base isn't just text anymore — it's PDFs, charts,
screenshots, video. But the tools we've used all cohort — LangChain's embedding interface, our vector
DB — were built for strings. Everything in this notebook is a workaround for that mismatch."

*[Screen: scroll past the title cell, land on Section 1's table]*

---

## [0:30–1:15] The VLM has two separate jobs — this is the whole mental model

"Before anything else, one distinction the rest of the lab hangs on: the vision-language model gets used
**twice**, for two completely different reasons.

First, at **ingestion** — it looks at a chart once and writes a description, so the image becomes
searchable. That's parsing.

Second, at **query time** — it looks at the *retrieved* image again and actually reads the numbers off
it to answer your question. That's understanding.

If you remember nothing else: parsing is for *finding* things, reading is for *trusting* the answer.
Almost every weird result in this lab traces back to conflating those two jobs."

*[Screen: Section 1 table, then jump to Section 4 header]*

---

## [1:15–3:00] Retrieval: there is no single right answer, only tradeoffs

"Section 5 is the heart of the lab — three different ways to make a text query find an image, and the
point isn't 'which one wins,' it's that each one trades away something different.

Caption-based retrieval turns images into text up front, so it's cheap to query and plays nice with
everything we already know — but it's only as good as whatever the caption happened to mention.

Unified embeddings — CLIP — put text and images in the same vector space, so a query can match pixels
directly with no caption in between. Sounds ideal, except in practice text and image vectors don't
actually mix — they cluster apart. So in a combined search, text quietly buries the images even when the
image is the right answer. That's the 'modality gap,' and it's the single most important gotcha in this
notebook.

The third approach just accepts that and keeps text and images in separate indexes, merging results by
rank instead of by score. More moving parts, but it's the one that doesn't let one modality silently
dominate the other.

None of these is 'correct.' The lab wants you to internalize that retrieval design here is a genuine
trade — cost, simplicity, and accuracy pull in different directions depending on your corpus."

*[Screen: run through Strategy A/B/C outputs side by side, point at the tradeoffs table]*

---

## [3:00–4:00] Generation: why we still hand over the actual pixels

"Here's the second big idea, and it directly follows from the two-jobs point earlier. Even after
retrieval finds the right chart, we don't just reuse the caption we already wrote for it — we reload the
actual image and hand real pixels to the model at answer time.

Why? Because a caption is a lossy, one-time summary written before anyone asked a question. It's fine
for search — 'this looks like the revenue chart' — but the exact number you need might never have made
it into that summary. So retrieval's job is just to get you close; generation's job is to look again,
grounded in the source, and read the precise value off it. Skip that step and you're quietly trusting a
summary instead of the ground truth."

*[Screen: Section 7, point at build_answer_message sending an image, then the generated answer with a real number]*

---

## [4:00–4:45] Zoom out: this generalizes past charts

"Last thing — Section 9 stretches this same pattern to video, and it's worth seeing why that's not a new
idea, just a bigger one. A video is still just two aligned streams, visual and text (the transcript), and
you handle it with the exact same two moves: parse it down into searchable chunks, then hand the model
the real frames when it needs to actually look. The scale changes — you can't index every frame — but
the architecture doesn't."

*[Screen: quick scroll through Section 9]*

---

## [4:45–5:00] Close

"So: two jobs for the VLM, a real tradeoff between three retrieval designs, and generation that always
grounds back in the source instead of trusting a summary. That's the whole lab. Go run the breakout
questions to pressure-test it yourselves."

---

**Total: ~800 words / ~5 min at a relaxed talking pace.**
