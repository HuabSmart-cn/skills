# Unsloth - Llms-Txt

**Pages:** 136

---

## !pip install huggingface_hub hf_transfer

**URL:** llms-txt#!pip-install-huggingface_hub-hf_transfer

import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id = "unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF",
    local_dir = "unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF",
    allow_patterns = ["*IQ2_XXS*"],
)
bash
./llama.cpp/llama-cli \
    --model unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF/Llama-4-Scout-17B-16E-Instruct-UD-IQ2_XXS.gguf \
    --threads 32 \
    --ctx-size 16384 \
    --n-gpu-layers 99 \
    -ot ".ffn_.*_exps.=CPU" \
    --seed 3407 \
    --prio 3 \
    --temp 0.6 \
    --min-p 0.01 \
    --top-p 0.9 \
    -no-cnv \
    --prompt "<|header_start|>user<|header_end|>\n\nCreate a Flappy Bird game.<|eot|><|header_start|>assistant<|header_end|>\n\n"
```

{% hint style="success" %}
Read more on running Llama 4 here: <https://docs.unsloth.ai/basics/tutorial-how-to-run-and-fine-tune-llama-4>
{% endhint %}

**Examples:**

Example 1 (unknown):
```unknown
And let's do inference!

{% code overflow="wrap" %}
```

---

## First uninstall xformers installed by previous libraries

**URL:** llms-txt#first-uninstall-xformers-installed-by-previous-libraries

pip uninstall xformers -y

---

## (1) Saving to GGUF / merging to 16bit for vLLM

**URL:** llms-txt#(1)-saving-to-gguf-/-merging-to-16bit-for-vllm

---

## Qwen3-Coder: How to Run Locally

**URL:** llms-txt#qwen3-coder:-how-to-run-locally

**Contents:**
- 🖥️ **Running Qwen3-Coder**
  - :gear: Recommended Settings
  - Run Qwen3-Coder-30B-A3B-Instruct:

Run Qwen3-Coder-30B-A3B-Instruct and 480B-A35B locally with Unsloth Dynamic quants.

Qwen3-Coder is Qwen’s new series of coding agent models, available in 30B (**Qwen3-Coder-Flash**) and 480B parameters. **Qwen3-480B-A35B-Instruct** achieves SOTA coding performance rivalling Claude Sonnet-4, GPT-4.1, and [Kimi K2](https://docs.unsloth.ai/models/tutorials-how-to-fine-tune-and-run-llms/kimi-k2-how-to-run-locally), with 61.8% on Aider Polygot and support for 256K (extendable to 1M) token context.

We also uploaded Qwen3-Coder with native <mark style="background-color:purple;">**1M context length**</mark> extended by YaRN and full-precision 8bit and 16bit versions. [Unsloth](https://github.com/unslothai/unsloth) also now supports fine-tuning and [RL](https://docs.unsloth.ai/get-started/reinforcement-learning-rl-guide) of Qwen3-Coder.

{% hint style="success" %}
[**UPDATE:** We fixed tool-calling for Qwen3-Coder! ](#tool-calling-fixes)You can now use tool-calling seamlessly in llama.cpp, Ollama, LMStudio, Open WebUI, Jan etc. This issue was universal and affected all uploads (not just Unsloth), and we've communicated with the Qwen team about our fixes! [Read more](#tool-calling-fixes)
{% endhint %}

<a href="#run-qwen3-coder-30b-a3b-instruct" class="button secondary">Run 30B-A3B</a><a href="#run-qwen3-coder-480b-a35b-instruct" class="button secondary">Run 480B-A35B</a>

{% hint style="success" %}
**Does** [**Unsloth Dynamic Quants**](https://docs.unsloth.ai/basics/unsloth-dynamic-2.0-ggufs) **work?** Yes, and very well. In third-party testing on the Aider Polyglot benchmark, the **UD-Q4\_K\_XL (276GB)** dynamic quant nearly matched the **full bf16 (960GB)** Qwen3-coder model, scoring 60.9% vs 61.8%. [More details here.](https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF/discussions/8)
{% endhint %}

#### **Qwen3 Coder - Unsloth Dynamic 2.0 GGUFs**:

| Dynamic 2.0 GGUF (to run)                                                                                                                                                                                                     | 1M Context Dynamic 2.0 GGUF                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <ul><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF">30B-A3B-Instruct</a></li><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF">480B-A35B-Instruct</a></li></ul> | <ul><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-1M-GGUF">30B-A3B-Instruct</a></li><li><a href="https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-1M-GGUF">480B-A35B-Instruct</a></li></ul> |

## 🖥️ **Running Qwen3-Coder**

Below are guides for the [**30B-A3B**](#run-qwen3-coder-30b-a3b-instruct) and [**480B-A35B**](#run-qwen3-coder-480b-a35b-instruct) variants of the model.

### :gear: Recommended Settings

Qwen recommends these inference settings for both models:

`temperature=0.7`, `top_p=0.8`, `top_k=20`, `repetition_penalty=1.05`

* <mark style="background-color:green;">**Temperature of 0.7**</mark>
* Top\_K of 20
* Min\_P of 0.00 (optional, but 0.01 works well, llama.cpp default is 0.1)
* Top\_P of 0.8
* <mark style="background-color:green;">**Repetition Penalty of 1.05**</mark>
* Chat template:&#x20;

{% code overflow="wrap" %}

{% endcode %}
* Recommended context output: 65,536 tokens (can be increased). Details here.

**Chat template/prompt format with newlines un-rendered**

{% code overflow="wrap" %}

<mark style="background-color:yellow;">**Chat template for tool calling**</mark> (Getting the current temperature for San Francisco). More details here for how to format tool calls.

{% hint style="info" %}
Reminder that this model supports only non-thinking mode and does not generate `<think></think>` blocks in its output. Meanwhile, specifying `enable_thinking=False` is no longer required.
{% endhint %}

### Run Qwen3-Coder-30B-A3B-Instruct:

To achieve inference speeds of 6+ tokens per second for our Dynamic 4-bit quant, have at least **18GB of unified memory** (combined VRAM and RAM) or **18GB of system RAM** alone. As a rule of thumb, your available memory should match or exceed the size of the model you’re using. E.g. the UD\_Q8\_K\_XL quant (full precision), which is 32.5GB, will require at least **33GB of unified memory** (VRAM + RAM) or **33GB of RAM** for optimal performance.

**NOTE:** The model can run on less memory than its total size, but this will slow down inference. Maximum memory is only needed for the fastest speeds.

Given that this is a non thinking model, there is no need to set `thinking=False` and the model does not generate `<think> </think>` blocks.

{% hint style="info" %}
Follow the [**best practices above**](#recommended-settings). They're the same as the 480B model.
{% endhint %}

#### 🦙 Ollama: Run Qwen3-Coder-30B-A3B-Instruct Tutorial

1. Install `ollama` if you haven't already! You can only run models up to 32B in size.

2. Run the model! Note you can call `ollama serve`in another terminal if it fails! We include all our fixes and suggested parameters (temperature etc) in `params` in our Hugging Face upload!

#### :sparkles: Llama.cpp: Run Qwen3-Coder-30B-A3B-Instruct Tutorial

1. Obtain the latest `llama.cpp` on [GitHub here](https://github.com/ggml-org/llama.cpp). You can follow the build instructions below as well. Change `-DGGML_CUDA=ON` to `-DGGML_CUDA=OFF` if you don't have a GPU or just want CPU inference.

2. You can directly pull from HuggingFace via:

3. Download the model via (after installing `pip install huggingface_hub hf_transfer` ). You can choose UD\_Q4\_K\_XL or other quantized versions.

**Examples:**

Example 1 (unknown):
```unknown
<|im_start|>user
  Hey there!<|im_end|>
  <|im_start|>assistant
  What is 1+1?<|im_end|>
  <|im_start|>user
  2<|im_end|>
  <|im_start|>assistant
```

Example 2 (unknown):
```unknown
<|im_start|>user\nHey there!<|im_end|>\n<|im_start|>assistant\nWhat is 1+1?<|im_end|>\n<|im_start|>user\n2<|im_end|>\n<|im_start|>assistant\n
```

Example 3 (unknown):
```unknown
<|im_start|>user
What's the temperature in San Francisco now? How about tomorrow?<|im_end|>
<|im_start|>assistant
<tool_call>\n<function=get_current_temperature>\n<parameter=location>\nSan Francisco, CA, USA
</parameter>\n</function>\n</tool_call><|im_end|>
<|im_start|>user
<tool_response>
{"temperature": 26.1, "location": "San Francisco, CA, USA", "unit": "celsius"}
</tool_response>\n<|im_end|>
```

Example 4 (bash):
```bash
apt-get update
apt-get install pciutils -y
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Ensure all audio is at 24 kHz sampling rate (Orpheus’s expected rate)

**URL:** llms-txt#ensure-all-audio-is-at-24-khz-sampling-rate-(orpheus’s-expected-rate)

**Contents:**
  - Fine-Tuning TTS with Unsloth

dataset = dataset.cast_column("audio", Audio(sampling_rate=24000))

filename,text
  0001.wav,Hello there!
  0002.wav,<sigh> I am very tired.
  python
  from datasets import Audio
  dataset = load_dataset("csv", data_files="mydata.csv", split="train")
  dataset = dataset.cast_column("filename", Audio(sampling_rate=24000))
  python
from unsloth import FastLanguageModel
import torch
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = False # Use 4bit quantization to reduce memory usage. Can be False.

model, tokenizer = ***REDACTED***
    model_name = "unsloth/orpheus-3b-0.1-ft",
    max_seq_length= 2048, # Choose any for long context!
    dtype = dtype,
    load_in_4bit = load_in_4bit,
    #token = ***REDACTED***
)

from datasets import load_dataset
dataset = load_dataset("MrDragonFox/Elise", split = "train")
python

**Examples:**

Example 1 (unknown):
```unknown
This will download the dataset (\~328 MB for \~1.2k samples). Each item in `dataset` is a dictionary with at least:

* `"audio"`: the audio clip (waveform array and metadata like sampling rate), and
* `"text"`: the transcript string

Orpheus supports tags like `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>`, etc. For example: `"I missed you <laugh> so much!"`.  These tags are enclosed in angle brackets and will be treated as special tokens by the model (they match [Orpheus’s expected tags](https://github.com/canopyai/Orpheus-TTS) like `<laugh>` and `<sigh>`. During training, the model will learn to associate these tags with the corresponding audio patterns. The Elise dataset with tags already has many of these (e.g., 336 occurrences of “laughs”, 156 of “sighs”, etc. as listed in its card). If your dataset lacks such tags but you want to incorporate them, you can manually annotate the transcripts where the audio contains those expressions.

**Option 2: Preparing a custom dataset** – If you have your own audio files and transcripts:

* Organize audio clips (WAV/FLAC files) in a folder.
* Create a CSV or TSV file with columns for file path and transcript. For example:
```

Example 2 (unknown):
```unknown
* Use `load_dataset("csv", data_files="mydata.csv", split="train")` to load it. You might need to tell the dataset loader how to handle audio paths. An alternative is using the `datasets.Audio` feature to load audio data on the fly:
```

Example 3 (unknown):
```unknown
Then `dataset[i]["audio"]` will contain the audio array.
* **Ensure transcripts are normalized** (no unusual characters that the tokenizer might not know, except the emotion tags if used). Also ensure all audio have a consistent sampling rate (resample them if necessary to the target rate the model expects, e.g. 24kHz for Orpheus).

In summary, for **dataset preparation**:

* You need a **list of (audio, text)** pairs.
* Use the HF `datasets` library to handle loading and optional preprocessing (like resampling).
* Include any **special tags** in the text that you want the model to learn (ensure they are in `<angle_brackets>` format so the model treats them as distinct tokens).
* (Optional) If multi-speaker, you could include a speaker ID token in the text or use a separate speaker embedding approach, but that’s beyond this basic guide (Elise is single-speaker).

### Fine-Tuning TTS with Unsloth

Now, let’s start fine-tuning! We’ll illustrate using Python code (which you can run in a Jupyter notebook, Colab, etc.).

**Step 1: Load the Model and Dataset**

In all our  TTS notebooks, we enable LoRA (16-bit) training and disable QLoRA (4-bit) training with: `load_in_4bit = False`. This is so the model can usually learn your dataset better and have higher accuracy.
```

Example 4 (unknown):
```unknown
{% hint style="info" %}
If memory is very limited or if dataset is large, you can stream or load in chunks. Here, 3h of audio easily fits in RAM. If using your own dataset CSV, load it similarly.
{% endhint %}

**Step 2: Advanced - Preprocess the data for training (Optional)**

We need to prepare inputs for the Trainer. For text-to-speech, one approach is to train the model in a causal manner: concatenate text and audio token IDs as the target sequence. However, since Orpheus is a decoder-only LLM that outputs audio, we can feed the text as input (context) and have the audio token ids as labels. In practice, Unsloth’s integration might do this automatically if the model’s config identifies it as text-to-speech. If not, we can do something like:
```

---

## All Our Models

**URL:** llms-txt#all-our-models

**Contents:**
  - New & recommended models:
  - DeepSeek models:
  - Llama models:
  - Gemma models:
  - Qwen models:
  - Mistral models:
  - Phi models:
  - Other (GLM, Orpheus, Smol, Llava etc.) models:
  - New models:
  - DeepSeek models

Unsloth model catalog for all our [Dynamic](https://docs.unsloth.ai/basics/unsloth-dynamic-2.0-ggufs) GGUF, 4-bit, 16-bit models on Hugging Face.

{% tabs %}
{% tab title="• GGUF + 4-bit" %} <a href="#deepseek-models" class="button secondary">DeepSeek</a><a href="#llama-models" class="button secondary">Llama</a><a href="#gemma-models" class="button secondary">Gemma</a><a href="#qwen-models" class="button secondary">Qwen</a><a href="#mistral-models" class="button secondary">Mistral</a><a href="#phi-models" class="button secondary">Phi</a>

**GGUFs** let you run models in tools like Ollama, Open WebUI, and llama.cpp.\
**Instruct (4-bit)** safetensors can be used for inference or fine-tuning.

### New & recommended models:

| Model                                                                                      | Variant                | GGUF                                                                            | Instruct (4-bit)                                                                            |
| ------------------------------------------------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [**gpt-oss** ](https://docs.unsloth.ai/models/gpt-oss-how-to-run-and-fine-tune)            | 120b                   | [link](https://huggingface.co/unsloth/gpt-oss-120b-GGUF)                        | [link](https://huggingface.co/unsloth/gpt-oss-120b-unsloth-bnb-4bit)                        |
|                                                                                            | 20b                    | [link](https://huggingface.co/unsloth/gpt-oss-20b-GGUF)                         | [link](https://huggingface.co/unsloth/gpt-oss-20b-unsloth-bnb-4bit)                         |
| [**DeepSeek-V3.1**](https://docs.unsloth.ai/models/deepseek-v3.1-how-to-run-locally)       | Terminus               | [link](https://huggingface.co/unsloth/DeepSeek-V3.1-Terminus-GGUF)              | —                                                                                           |
|                                                                                            | V3.1                   | [link](https://huggingface.co/unsloth/DeepSeek-V3.1-GGUF)                       | —                                                                                           |
| [**Qwen3-VL**](https://docs.unsloth.ai/models/qwen3-vl-how-to-run-and-fine-tune)           | 2B-Instruct            | [link](https://huggingface.co/unsloth/Qwen3-VL-2B-Instruct-GGUF)                | [link](https://huggingface.co/unsloth/Qwen3-VL-2B-Instruct-unsloth-bnb-4bit)                |
|                                                                                            | 2B-Thinking            | [link](https://huggingface.co/unsloth/Qwen3-VL-2B-Thinking-GGUF)                | [link](https://huggingface.co/unsloth/Qwen3-VL-2B-Thinking-unsloth-bnb-4bit)                |
|                                                                                            | 4B-Instruct            | [link](https://huggingface.co/unsloth/Qwen3-VL-4B-Instruct-GGUF)                | [link](https://huggingface.co/unsloth/Qwen3-VL-4B-Instruct-unsloth-bnb-4bit)                |
|                                                                                            | 4B-Thinking            | [link](https://huggingface.co/unsloth/Qwen3-VL-4B-Thinking-GGUF)                | [link](https://huggingface.co/unsloth/Qwen3-VL-4B-Thinking-unsloth-bnb-4bit)                |
|                                                                                            | 8B-Instruct            | [link](https://huggingface.co/unsloth/Qwen3-VL-8B-Instruct-GGUF)                | [link](https://huggingface.co/unsloth/Qwen3-VL-8B-Instruct-unsloth-bnb-4bit)                |
|                                                                                            | 8B-Thinking            | [link](https://huggingface.co/unsloth/Qwen3-VL-8B-Thinking-GGUF)                | [link](https://huggingface.co/unsloth/Qwen3-VL-8B-Thinking-unsloth-bnb-4bit)                |
|                                                                                            | 30B-A3B-Instruct       | [link](https://huggingface.co/unsloth/Qwen3-VL-30B-A3B-Instruct-GGUF)           | —                                                                                           |
|                                                                                            | 30B-A3B-Thinking       | [link](https://huggingface.co/unsloth/Qwen3-VL-30B-A3B-Thinking-GGUF)           | —                                                                                           |
|                                                                                            | 32B-Instruct           | [link](https://huggingface.co/unsloth/Qwen3-VL-32B-Instruct-GGUF)               | [link](https://huggingface.co/unsloth/Qwen3-VL-32B-Instruct-unsloth-bnb-4bit)               |
|                                                                                            | 32B-Thinking           | [link](https://huggingface.co/unsloth/Qwen3-VL-32B-Thinking-GGUF)               | [link](https://huggingface.co/unsloth/Qwen3-VL-32B-Thinking-unsloth-bnb-4bit)               |
|                                                                                            | 235B-A22B-Instruct     | [link](https://huggingface.co/unsloth/Qwen3-VL-235B-A22B-Instruct-GGUF)         | —                                                                                           |
|                                                                                            | 235B-A22B-Thinking     | [link](https://huggingface.co/unsloth/Qwen3-VL-235B-A22B-Thinking-GGUF)         | —                                                                                           |
| [**Qwen3-2507**](https://docs.unsloth.ai/models/qwen3-how-to-run-and-fine-tune/qwen3-2507) | 30B-A3B-Instruct       | [link](https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF)         | —                                                                                           |
|                                                                                            | 30B-A3B-Thinking       | [link](https://huggingface.co/unsloth/Qwen3-30B-A3B-Thinking-2507-GGUF)         | —                                                                                           |
|                                                                                            | 235B-A22B-Thinking     | [link](https://huggingface.co/unsloth/Qwen3-235B-A22B-Thinking-2507-GGUF/)      | —                                                                                           |
|                                                                                            | 235B-A22B-Instruct     | [link](https://huggingface.co/unsloth/Qwen3-235B-A22B-Instruct-2507-GGUF/)      | —                                                                                           |
| **Qwen3-Coder**                                                                            | 30B-A3B                | [link](https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF)        | —                                                                                           |
|                                                                                            | 480B-A35B              | [link](https://huggingface.co/unsloth/Qwen3-Coder-480B-A35B-Instruct-GGUF)      | —                                                                                           |
| **Granite-4.0 (new)**                                                                      | H-Small                | [link](https://huggingface.co/unsloth/granite-4.0-h-small-GGUF)                 | [link](https://huggingface.co/unsloth/granite-4.0-h-small-unsloth-bnb-4bit)                 |
| **GLM (new)**                                                                              | 4.6                    | [link](https://huggingface.co/unsloth/GLM-4.6-GGUF)                             | —                                                                                           |
|                                                                                            | 4.5-Air                | [link](https://huggingface.co/unsloth/GLM-4.5-Air-GGUF)                         | —                                                                                           |
| **Kimi-K2-0905**                                                                           | 1T                     | [link](https://huggingface.co/unsloth/Kimi-K2-Instruct-0905-GGUF)               | —                                                                                           |
| **Gemma 3n**                                                                               | E2B                    | [link](https://huggingface.co/unsloth/gemma-3n-E2B-it-GGUF)                     | [link](https://huggingface.co/unsloth/gemma-3n-E2B-it-unsloth-bnb-4bit)                     |
|                                                                                            | E4B                    | [link](https://huggingface.co/unsloth/gemma-3n-E4B-it-GGUF)                     | [link](https://huggingface.co/unsloth/gemma-3n-E4B-it-unsloth-bnb-4bit)                     |
| **DeepSeek-R1-0528**                                                                       | R1-0528-Qwen3-8B       | [link](https://huggingface.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF)           | [link](https://huggingface.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-unsloth-bnb-4bit)           |
|                                                                                            | R1-0528                | [link](https://huggingface.co/unsloth/DeepSeek-R1-0528-GGUF)                    | —                                                                                           |
| **Mistral**                                                                                | Magistral Small (2509) | [link](https://huggingface.co/unsloth/Magistral-Small-2509-GGUF)                | [link](https://huggingface.co/unsloth/Magistral-Small-2509-unsloth-bnb-4bit)                |
|                                                                                            | Magistral Small (2507) | [link](https://huggingface.co/unsloth/Magistral-Small-2507-GGUF)                | [link](https://huggingface.co/unsloth/Magistral-Small-2507-unsloth-bnb-4bit)                |
|                                                                                            | Small 3.2 24B (2506)   | [link](https://huggingface.co/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF) | [link](https://huggingface.co/unsloth/Mistral-Small-3.2-24B-Instruct-2506-unsloth-bnb-4bit) |

... [Content truncated, total 810,852 chars] ...