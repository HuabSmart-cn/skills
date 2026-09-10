# Axolotl - Other

**Pages:** 26

---

## Mixed Precision Training

**URL:** https://docs.axolotl.ai/docs/mixed_precision.html

**Contents:**
- Mixed Precision Training
- 1 FP16 Mixed Precision
  - 1.1 Overview
  - 1.2 Configuration
  - 1.3 FP16 Considerations
- 2 BF16 Mixed Precision
  - 2.1 Overview
  - 2.2 Configuration
- 3 FP8 Mixed Precision
  - 3.1 What is FP8?

Mixed precision training uses lower precision data types to reduce memory usage and increase training speed while maintaining model quality. Axolotl supports several mixed precision formats:

FP16 is the traditional half-precision format, supported on older GPUs but can be less numerically stable than BF16.

BF16 (Brain Float 16) offers better numerical stability than FP16 and is the recommended mixed precision format for modern GPUs. It provides the same dynamic range as FP32 while using half the memory.

FP8 support is experimental and requires compatible hardware (H100, H200) and recent PyTorch versions with TorchAO.

FP8 (8-bit floating point) can provide significant time savings compared to FP16/BF16 while maintaining training stability. Axolotl’s implementation uses PyTorch’s TorchAO library with “tensorwise” scaling strategy.

Add to your YAML config:

torch.compile is critical for FP8 performance

FP8 training requires torch_compile: true to see meaningful speedups. Without compilation, FP8 may actually be slower and use more memory than FP16/BF16.

For FSDP (Fully Sharded Data Parallel) training:

Always validate your mixed precision setup:

See examples/llama-3/3b-fp8-fsdp2.yaml for an optimized example config. Enabling FP8 mixed precision + FP8 all-gather training results in ~10% faster iterations per second vs. BF16 for a relatively small (3B param) model

For more information on multi-GPU training, see our Multi-GPU guide.

**Examples:**

Example 1 (yaml):
```yaml
# Automatic BF16 detection (recommended)
bf16: auto

# Or explicitly enable
bf16: true

# For evaluation with BF16
bf16: full  # Equivalent to bf16_full_eval in the HF trainer
```

Example 2 (yaml):
```yaml
# Enable FP8 mixed precision
fp8: true

# Optional: Enable FP8 for FSDP all-gather operations
fp8_enable_fsdp_float8_all_gather: true

# Enable torch.compile (almost always necessary for FP8 speedups)
torch_compile: true
```

Example 3 (yaml):
```yaml
fp8: true
fp8_enable_fsdp_float8_all_gather: true

torch_compile: true

# FSDP configuration
fsdp_version: 2
fsdp_config:
  offload_params: false
  cpu_ram_efficient_loading: true
  auto_wrap_policy: TRANSFORMER_BASED_WRAP
  transformer_layer_cls_to_wrap: LlamaDecoderLayer
  state_dict_type: FULL_STATE_DICT
  reshard_after_forward: true
```

---

## FAQ

**URL:** https://docs.axolotl.ai/docs/faq.html

**Contents:**
- FAQ
  - General
  - Chat templates

Q: The trainer stopped and hasn’t progressed in several minutes.

A: Usually an issue with the GPUs communicating with each other. See the NCCL doc

A: This usually happens when you run out of system RAM.

Q: exitcode: -7 while using deepspeed

A: Try upgrading deepspeed w: pip install -U deepspeed

Q: AttributeError: ‘DummyOptim’ object has no attribute ‘step’

Q: ModuleNotFoundError: No module named ‘mpi4py’ using single GPU with deepspeed

A: You may be using deepspeed with single gpu. Please remove the deepspeed: section in the yaml file or --deepspeed CLI flag.

Q: The codes is stuck on saving preprocessed datasets.

A: This is usually an issue with the GPU. This can be resolved through setting the os environment variable CUDA_VISIBLE_DEVICES=0. If you are on runpod, this is usually a pod issue. Starting a new pod should take care of it.

Q: Received mismatch error on merge adapters / loading adapters between torch.Size of checkpoint and model.

A: This is likely due to vocab size mismatch. By default, Axolotl expands the model’s embeddings if the tokenizer has more tokens than the model. Please use the axolotl merge-lora command to merge the adapters instead of using your own scripts.

On the other hand, if the model has more tokens than the tokenizer, Axolotl does not shrink the model’s embeddings unless shrink_embeddings: ***REDACTED***

Q: How to call Axolotl via custom python scripts?

A: Since Axolotl is just Python, please see src/axolotl/cli/main.py on how each command is called.

Q: How to know the value to use for fsdp_transformer_layer_cls_to_wrap?

A: This is the class name of the transformer layer to wrap with FSDP. For example, for LlamaForCausalLM, the value is LlamaDecoderLayer. To find this for a specific model, check the model’s PreTrainedModel definition and look for _no_split_modules variable in the modeling_<model_name>.py file within transformers library.

Q: ValueError: Asking to pad but the tokenizer does not have a padding token. Please select a token to use as pad_token

A: This is because the tokenizer does not have a padding token. Please add a padding token to the tokenizer via:

Q: IterableDataset error or KeyError: 'input_ids' when using preprocess CLI

A: This is because you may be using preprocess CLI with pretraining_dataset: or skip_prepare_dataset: true respectively. Please use axolotl train CLI directly instead as these datasets are prepared on demand.

Q: vLLM is not working with Axolotl

A: We currently recommend torch 2.6.0 for use with vllm. Please ensure you use the right version. For Docker, please use the main-py3.11-cu124-2.6.0 tag.

Q: FA2 2.8.0 undefined symbol runtime error on CUDA 12.4

A: There seems to be a wheel issue with FA2 2.8.0 on CUDA 12.4. Try CUDA 12.6 instead or downgrade to FA2 2.7.4. Please refer to the upstream issue: https://github.com/Dao-AILab/flash-attention/issues/1717.

Q: Can we mix text and text+image datasets for VLM training?

A: Yes, you can for newer VLM arch. The ones that would not work are LLaVA / Pixtral arch. If you notice one not working, please let us know!

Q: Why is memory/max_* different from nvidia-smi?

A: We use torch APIs to retrieve this information. You can see https://docs.pytorch.org/docs/stable/notes/cuda.html#cuda-memory-management for more information.

Q: jinja2.exceptions.UndefinedError: 'dict object' has no attribute 'content' / 'role' / ____

A: This means that the property mapping for the stated attribute does not exist when building chat_template prompt. For example, if no attribute 'content', please check you have added the correct mapping for content under message_property_mappings.

Q: Empty template generated for turn ___

A: The content is empty for that turn.

Q: Could not find content start/end boundary for turn __

A: The specific turn’s start/end could not be detected. Please ensure you have set the eos_token following your chat_template. Otherwise, this could be a chat_template which doesn’t use proper boundaries for each turn (like system). On the rare occurrence, make sure your content is not [[dummy_message]]. Please let us know about this.

Q: Content end boundary is before start boundary for turn ___

A: This is an edge case which should not occur. Please create an Issue if this happens.

Q: Content end boundary is the same as start boundary for turn ___. This is likely an empty turn.

A: This is likely an empty turn.

Q: The EOS token is incorrectly being masked or not being masked / EOS token __ not found in chat template.

A: There can be two reasons:

Q: “chat_template choice is tokenizer_default but tokenizer’s chat_template is null. Please add a chat_template in tokenizer config”

A: This is because the tokenizer does not have a chat template. Please add a chat template in the tokenizer config. See chat_template for more details.

Q: The EOT token(s) are incorrectly being masked or not being masked / EOT token __ not found in chat template.

A: There can be two reasons:

Q: EOT token encoding failed. Please check if the token is valid and can be encoded.

A: There could be some issue with the tokenizer or unicode encoding. Please raise an issue with examples with the EOT token & tokenizer causing the issue.

Q: EOT token __ is encoded as multiple tokens.

A: This is because the EOT token is encoded as multiple tokens which can cause unexpected behavior. Please add it under tokens: or (recommended) override unused added_tokens via added_tokens_overrides:.

Q: Conflict between train_on_eos and train_on_eot. eos_token is in eot_tokens and train_on_eos != train_on_eot

A: This is because the EOS token is in the eot_tokens: while mismatch between train_on_eos: and train_on_eot:. This will cause one to override the other. Please ensure that train_on_eos: and train_on_eot: are the same or remove the EOS token from eot_tokens:.

Q: If eot_tokens: is not provided, what happens?

A: If eot_tokens: is not provided, the default behavior is the same as before. EOS tokens used to delimit turns are masked/unmasked depending on whether the turn is trainable.

Internally, eot_tokens: ***REDACTED***

Q: Data processing error: CAS service error

A: Try disabling XET with export HF_HUB_DISABLE_XET=1

Q: torch._inductor.exc.LoweringException: NoValidChoicesError: No choices to select, please consider adding ATEN into max_autotune_gemm_backends config (defined in torch/_inductor/config.py) to allow at least one choice.

A: Depending on the version of torch, you may need to include this in your YAML:

**Q: ValueError("Backward pass should have cleared tracker of all tensors")

A: This may happen due to edge cases in using the modern OffloadActivations context manager for CUDA streams. If you encounter this error, you may have success using the naive implementation with offload_activations: legacy in your YAML.

**Q: Error parsing tool_calls arguments as JSON.

A: There is an error parsing string arguments to a dict. Please check your dataset and the error message for more details.

**Examples:**

Example 1 (yaml):
```yaml
special_tokens:
  ***REDACTED***
  pad_token: ***REDACTED***
```

Example 2 (yaml):
```yaml
flex_attn_compile_kwargs:
  dynamic: false
  mode: max-autotune-no-cudagraphs
```

---

## Installation

**URL:** https://docs.axolotl.ai/docs/installation.html

**Contents:**
- Installation
- 1 Requirements
- 2 Installation Methods
  - 2.1 PyPI Installation (Recommended)
  - 2.2 uv Installation
  - 2.3 Edge/Development Build
  - 2.4 Docker
- 3 Cloud Environments
  - 3.1 Cloud GPU Providers
  - 3.2 Google Colab

This guide covers all the ways you can install and set up Axolotl for your environment.

Please make sure to have Pytorch installed before installing Axolotl in your local environment.

Follow the instructions at: https://pytorch.org/get-started/locally/

For Blackwell GPUs, please use Pytorch 2.7.0 and CUDA 12.8.

We use --no-build-isolation in order to detect the installed PyTorch version (if installed) in order not to clobber it, and so that we set the correct version of dependencies that are specific to the PyTorch version or other installed co-dependencies.

uv is a fast, reliable Python package installer and resolver built in Rust. It offers significant performance improvements over pip and provides better dependency resolution, making it an excellent choice for complex environments.

Install uv if not already installed

Choose your CUDA version to use with PyTorch; e.g. cu124, cu126, cu128, then create the venv and activate

Install PyTorch - PyTorch 2.6.0 recommended

Install axolotl from PyPi

For the latest features between releases:

For development with Docker:

For Blackwell GPUs, please use axolotlai/axolotl:main-py3.11-cu128-2.7.0 or the cloud variant axolotlai/axolotl-cloud:main-py3.11-cu128-2.7.0.

Please refer to the Docker documentation for more information on the different Docker images that are available.

For providers supporting Docker:

See Section 6 for Mac-specific issues.

We recommend using WSL2 (Windows Subsystem for Linux) or Docker.

Install PyTorch: https://pytorch.org/get-started/locally/

(Optional) Login to Hugging Face:

If you encounter installation issues, see our FAQ and Debugging Guide.

**Examples:**

Example 1 (bash):
```bash
pip3 install -U packaging setuptools wheel ninja
pip3 install --no-build-isolation axolotl[flash-attn,deepspeed]
```

Example 2 (bash):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Example 3 (bash):
```bash
export UV_TORCH_BACKEND=cu126
uv venv --no-project --relocatable
source .venv/bin/activate
```

Example 4 (bash):
```bash
uv pip install packaging setuptools wheel
uv pip install torch==2.6.0
uv pip install awscli pydantic
```

---

## Dataset Preprocessing

**URL:** https://docs.axolotl.ai/docs/dataset_preprocessing.html

**Contents:**
- Dataset Preprocessing
- Overview
  - What are the benefits of pre-processing?
  - What are the edge cases?

Dataset pre-processing is the step where Axolotl takes each dataset you’ve configured alongside the dataset format and prompt strategies to:

The processing of the datasets can happen one of two ways:

When training interactively or for sweeps (e.g. you are restarting the trainer often), processing the datasets can oftentimes be frustratingly slow. Pre-processing will cache the tokenized/formatted datasets according to a hash of dependent training parameters so that it will intelligently pull from its cache when possible.

The path of the cache is controlled by dataset_prepared_path: and is often left blank in example YAMLs as this leads to a more robust solution that prevents unexpectedly reusing cached data.

If dataset_prepared_path: is left empty, when training, the processed dataset will be cached in a default path of ./last_run_prepared/, but will ignore anything already cached there. By explicitly setting dataset_prepared_path: ./last_run_prepared, the trainer will use whatever pre-processed data is in the cache.

Let’s say you are writing a custom prompt strategy or using a user-defined prompt template. Because the trainer cannot readily detect these changes, we cannot change the calculated hash value for the pre-processed dataset.

If you have dataset_prepared_path: ... set and change your prompt templating logic, it may not pick up the changes you made and you will be training over the old prompt.

---

## Inference and Merging

**URL:** https://docs.axolotl.ai/docs/inference.html

**Contents:**
- Inference and Merging
- 1 Quick Start
  - 1.1 Basic Inference
- 2 Advanced Usage
  - 2.1 Gradio Interface
  - 2.2 File-based Prompts
  - 2.3 Memory Optimization
- 3 Merging LoRA Weights
  - 3.1 Memory Management for Merging
- 4 Tokenization

This guide covers how to use your trained models for inference, including model loading, interactive testing, merging adapters, and common troubleshooting steps.

Use the same config used for training on inference/merging.

Launch an interactive web interface:

Process prompts from a text file:

For large models or limited memory:

Merge LoRA adapters with the base model:

Tokenization mismatches between training and inference are a common source of problems.

Verify inference tokenization by decoding tokens before model input

Compare token IDs between training and inference

Configure special tokens in your YAML:

***REDACTED***

**Examples:**

Example 1 (bash):
```bash
axolotl inference your_config.yml --lora-model-dir="./lora-output-dir"
```

Example 2 (bash):
```bash
axolotl inference your_config.yml --base-model="./completed-model"
```

Example 3 (bash):
```bash
axolotl inference your_config.yml --gradio
```

Example 4 (bash):
```bash
cat /tmp/prompt.txt | axolotl inference your_config.yml \
  --base-model="./completed-model" --prompter=None
```

---

## MultiModal / Vision Language Models (BETA)

**URL:** https://docs.axolotl.ai/docs/multimodal.html

**Contents:**
- MultiModal / Vision Language Models (BETA)
- Supported Models
- Usage
  - Mllama
  - Llama4
  - Pixtral
  - Llava-1.5
  - Mistral-Small-3.1
  - Magistral-Small-2509
  - Voxtral

Multimodal support is limited and doesn’t have full feature parity.

Here are the hyperparams you’ll need to use to finetune a multimodal model.

Please see examples folder for full configs.

Some of our chat_templates have been extended to support broader dataset types. This should not break any existing configs.

As of now, we do not truncate nor drop samples based on sequence_len as each arch has different ways to process non-text tokens. We are looking for help on this.

Please make sure to install vision lib via pip install 'mistral-common[opencv]==1.8.5'

Please make sure to install vision lib via pip install 'mistral-common[opencv]==1.8.5'

Please make sure to install audio lib via pip3 install librosa==0.11.0 'mistral_common[audio]==1.8.3'

The Gemma3-1B model is a text-only model, so please train as regular text model.

For multi-modal 4B/12B/27B models, use the following config:

The model’s initial loss and grad norm will be very high. We suspect this to be due to the Conv in the vision layers.

Please make sure to install timm via pip3 install timm==1.0.17

Please make sure to install num2words via pip3 install num2words==0.5.14

Please uninstall causal-conv1d via pip3 uninstall -y causal-conv1d

For multi-modal datasets, we adopt an extended chat_template format similar to OpenAI’s Message format.

For backwards compatibility:

For image loading, you can use the following keys within content alongside "type": "image":

For audio loading, you can use the following keys within content alongside "type": "audio":

You may need to install librosa via pip3 install librosa==0.11.0.

This is not well tested at the moment. We welcome contributors!

For video loading, you can use the following keys within content alongside "type": "video":

Here is an example of a multi-modal dataset:

PIL could not retrieve the file at url using requests. Please check for typo. One alternative reason is that the request is blocked by the server.

**Examples:**

Example 1 (yaml):
```yaml
processor_type: AutoProcessor

skip_prepare_dataset: true
remove_unused_columns: false  # leave columns in place as they are needed to handle image embeddings during training
sample_packing: false  # not yet supported with multimodal

chat_template:  # see in next section if specified

# example dataset
datasets:
  - path: HuggingFaceH4/llava-instruct-mix-vsft
    type: chat_template
    split: train[:1%]

# (optional) if doing lora, only finetune the Language model,
# leave the vision model and vision tower frozen
# load_in_8bit: true
adapter: lora
lora_target_modules: 'model.language_model.layers.[\d]+.(mlp|cross_attn|self_attn).(up|down|gate|q|k|v|o)_proj'

# (optional) if you want to resize images to a set size
image_size: 512
image_resize_algorithm: bilinear
```

Example 2 (yaml):
```yaml
base_model: meta-llama/Llama-3.2-11B-Vision-Instruct

chat_template: llama3_2_vision
```

Example 3 (yaml):
```yaml
base_model: meta-llama/Llama-4-Scout-17B-16E-Instruct

chat_template: llama4
```

Example 4 (yaml):
```yaml
base_model: mistralai/Pixtral-12B-2409

chat_template: pixtral
```

---

## Reward Modelling

**URL:** https://docs.axolotl.ai/docs/reward_modelling.html

**Contents:**
- Reward Modelling
  - Overview
  - (Outcome) Reward Models
  - Process Reward Models (PRM)

Reward modelling is a technique used to train models to predict the reward or value of a given input. This is particularly useful in reinforcement learning scenarios where the model needs to evaluate the quality of its actions or predictions. We support the reward modelling techniques supported by trl.

Outcome reward models are trained using data which contains preference annotations for an entire interaction between the user and model (e.g. rather than per-turn or per-step). For improved training stability, you can use the center_rewards_coefficient parameter to encourage mean-zero reward outputs (see TRL docs).

Bradley-Terry chat templates expect single-turn conversations in the following format:

Check out our PRM blog.

Process reward models are trained using data which contains preference annotations for each step in a series of interactions. Typically, PRMs are trained to provide reward signals over each step of a reasoning trace and are used for downstream reinforcement learning.

Please see stepwise_supervised for more details on the dataset format.

**Examples:**

Example 1 (yaml):
```yaml
base_model: google/gemma-2-2b
model_type: AutoModelForSequenceClassification
num_labels: 1
tokenizer_type: ***REDACTED***

reward_model: true
chat_template: gemma
datasets:
  - path: argilla/distilabel-intel-orca-dpo-pairs
    type: bradley_terry.chat_template

val_set_size: 0.1
eval_steps: 100
```

Example 2 (json):
```json
{
    "system": "...", // optional
    "input": "...",
    "chosen": "...",
    "rejected": "..."
}
```

Example 3 (yaml):
```yaml
base_model: Qwen/Qwen2.5-3B
model_type: AutoModelForTokenClassification
num_labels: 2

process_reward_model: true
datasets:
  - path: trl-lib/math_shepherd
    type: stepwise_supervised
    split: train

val_set_size: 0.1
eval_steps: 100
```

---

## RLHF (Beta)

**URL:** https://docs.axolotl.ai/docs/rlhf.html

**Contents:**
- RLHF (Beta)
- Overview
- RLHF using Axolotl
  - DPO
    - chatml.argilla
    - chatml.argilla_chat
    - chatml.icr
    - chatml.intel
    - chatml.prompt_pairs
    - chatml.ultra

Reinforcement Learning from Human Feedback is a method whereby a language model is optimized from data using human feedback. Various methods include, but not limited to:

This is a BETA feature and many features are not fully implemented. You are encouraged to open new PRs to improve the integration and functionality.

We rely on the TRL library for implementations of various RL training methods, which we wrap around to expose in axolotl. Each method has their own supported ways of loading datasets and prompt formats.

You can find what each method supports by going into src/axolotl/prompt_strategies/{method} where {method} is one of our supported methods. The type: can be retrieved from {method}.{function_name}.

DPO supports the following types with the following dataset format:

For custom behaviors,

The input format is a simple JSON input with customizable fields based on the above config.

As IPO is just DPO with a different loss function, all supported dataset formats for DPO are also supported for IPO.

Paper: https://arxiv.org/abs/2403.07691

ORPO supports the following types with the following dataset format:

KTO supports the following types with the following dataset format:

For custom behaviors,

The input format is a simple JSON input with customizable fields based on the above config.

Check out our GRPO cookbook.

In the latest GRPO implementation, vLLM is used to significantly speedup trajectory generation during training. In this example, we’re using 4 GPUs - 2 for training, and 2 for vLLM:

Make sure you’ve installed the correct version of vLLM by including it as an extra when installing axolotl, e.g. pip install axolotl[vllm].

Your vLLM instance will now attempt to spin up, and it’s time to kick off training utilizing our remaining two GPUs. In another terminal, execute:

Due to TRL’s implementation with vLLM, the vLLM instance must use the last N GPUs instead of the first N GPUs. This is why in the example above, we use CUDA_VISIBLE_DEVICES=2,3 for the vLLM instance.

GRPO uses custom reward functions and transformations. Please have them ready locally.

For example, to load OpenAI’s GSM8K and use a random reward for completions:

To see other examples of custom reward functions, please see TRL GRPO Docs.

To see all configs, please see TRLConfig.

The DAPO paper and subsequently Dr. GRPO paper proposed an alternative loss function for GRPO to remediate the penalty in longer responses.

For more information, see GRPO docs.

SimPO uses CPOTrainer but with alternative loss function.

This method uses the same dataset format as DPO.

TRL supports auto-unwrapping PEFT models for RL training paradigms which rely on a reference model. This significantly reduces memory pressure as an additional refreference model does not need to be loaded, and reference model log-probabilities can be obtained by disabling PEFT adapters. This is enabled by default. To turn it off, pass the following config:

**Examples:**

Example 1 (yaml):
```yaml
rl: dpo
datasets:
  - path: Intel/orca_dpo_pairs
    split: train
    type: chatml.intel
  - path: argilla/ultrafeedback-binarized-preferences
    split: train
    type: chatml
```

Example 2 (json):
```json
{
    "system": "...", // optional
    "instruction": "...",
    "chosen_response": "...",
    "rejected_response": "..."
}
```

Example 3 (json):
```json
{
    "chosen": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "rejected": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}
```

Example 4 (json):
```json
{
    "system": "...", // optional
    "input": "...",
    "chosen": "...",
    "reje

... [Content truncated, total 140,218 chars] ...