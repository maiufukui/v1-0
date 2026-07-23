# Session 15 Loom Script — Reasoning Model Fine-Tuning with GRPO
**Target length: ~5 min**
**Audience: AIE9 cohort**
**Focus: streamlined top-to-bottom walkthrough of the demo notebook — easy to scroll through live**

---

### [0:00–1:10] Cold open, the core idea, and the default setting

**Show:** stay on the top of the notebook — title cell, intro paragraph (with the loop and the 16-bit note), and the "Learning Outcomes" list (cell 0).

Hey everyone — walking through Session 15, Reasoning Model Fine-Tuning with GRPO. This session we're not orchestrating a model, we're changing its weights: teaching Llama 3.2 3B to reason through GSM8K math problems using GRPO, the RL algorithm behind DeepSeek-R1.

The key takeaway from this is that we never actually show the model how to reason — GSM8K is just questions and final answers — so it only gets rewarded when the format and the final answer are right, and it has to figure out the reasoning on its own. For each question, the model comes up with a group of attempts, and each one gets scored against that group's own average instead of needing a separate critic network, which is a big part of why this fits on a single GPU with a 3B model. And we're training a 16-bit LoRA adapter here instead of QLoRA, because GRPO spends most of its time generating completions, and 16-bit is just faster for that.

### [1:10–1:50] Loading the model and attaching LoRA

**Show:** scroll down to Task 2's `from_pretrained(...)` cell (`max_seq_length`, `load_in_4bit`), then Task 3's `get_peft_model(...)` cell and its `print(model)` output.

First we actually load the base model with Unsloth, then attach LoRA to it. LoRA freezes the original weights and just trains two small matrices, A and B.

However, the default settings actually kept failing on me when I ran this in Colab. So I switched `load_in_4bit` to `True` and cut `max_seq_length` down to 1024 — turns out memory was my real constraint, not speed.

### [1:50–2:25] Prepping GSM8K and the reward functions

**Show:** Task 4's dataset cell + `dataset[0]` output, then the Task 5 reward table and reward function cells.

The dataset is just questions and correct answers, with a system prompt forcing every response into `<reasoning>...</reasoning><answer>...</answer>` so it can be checked automatically.

The key takeaway here is that the real craft is in the reward functions. Correctness is worth the most, but there are smaller rewards too, like tag formatting, and those give the model something to improve at before answering correctly.

### [2:25–3:00] Training

**Show:** Task 6's `GRPOConfig` cell (`num_generations = 4` — the other setting I dropped from 8 to run this in Colab), then Task 7's training cell and live output.

This chart is an example of the training reward curve. Reward is noisy around 0 for roughly the first 40-50 steps, then climbs steadily through the 50-100 range, and plateaus higher, around 1.2 to 1.5, for the rest of the run out to 175 steps. The faint light-blue line is the raw per-step values, and the darker line is a smoothed rolling average.

### [3:00–3:40] Before and after, save and load

**Show:** Task 8's generation output (base model, `lora_request = None`), then Task 9's save/load cells and trained-model output.

Task 8 generates from the frozen base model with no system prompt and `lora_request = None`, so it's just the untrained model answering "Calculate pi" on its own, no tags, no structure. Task 9 then loads the trained adapter back in and regenerates for that same kind of prompt, this time with the reasoning system prompt in place, so you can actually see the structured, tagged output GRPO trained it to produce, side by side with the untrained version. Saving that adapter is small, just a few hundred megabytes, and loading it back later is just as easy.

### [3:40–4:00] Close

**Show:** "Breakout Room #2 Summary" cell at the bottom.

So to wrap up: rewards shape the model's behavior instead of demonstrations, the group average takes the place of the critic, and LoRA is what keeps the whole training run cheap. And pay attention to your own constraints, whatever they are — mine needed QLoRA, a shorter context, and a smaller group just to actually finish. That's Session 15, thanks for watching.

---

**Total: ~400 words / under 4 min, leaves room for screen scrolling**
