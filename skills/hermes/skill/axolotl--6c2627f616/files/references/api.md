# Axolotl - Api

**Pages:** 150

---

## cli.cloud.modal_

**URL:** https://docs.axolotl.ai/docs/api/cli.cloud.modal_.html

**Contents:**
- cli.cloud.modal_
- Classes
  - ModalCloud
- Functions
  - run_cmd

Modal Cloud support from CLI

Modal Cloud implementation.

Run a command inside a folder, with Modal Volume reloading before and commit on success.

**Examples:**

Example 1 (python):
```python
cli.cloud.modal_.ModalCloud(config, app=None)
```

Example 2 (python):
```python
cli.cloud.modal_.run_cmd(cmd, run_folder, volumes=None)
```

---

## core.trainers.base

**URL:** https://docs.axolotl.ai/docs/api/core.trainers.base.html

**Contents:**
- core.trainers.base
- Classes
  - AxolotlTrainer
    - Methods
      - log
        - Parameters
      - push_to_hub
      - store_metrics
        - Parameters

Module for customized trainers

Extend the base Trainer for axolotl helpers

Log logs on the various objects watching training, including stored metrics.

Overwrite the push_to_hub method in order to force-add the tags when pushing the model on the Hub. Please refer to ~transformers.Trainer.push_to_hub for more details.

Store metrics with specified reduction type.

**Examples:**

Example 1 (python):
```python
core.trainers.base.AxolotlTrainer(
    *_args,
    bench_data_collator=None,
    eval_data_collator=None,
    dataset_tags=None,
    **kwargs,
)
```

Example 2 (python):
```python
core.trainers.base.AxolotlTrainer.log(logs, start_time=None)
```

Example 3 (python):
```python
core.trainers.base.AxolotlTrainer.push_to_hub(*args, **kwargs)
```

Example 4 (python):
```python
core.trainers.base.AxolotlTrainer.store_metrics(
    metrics,
    train_eval='train',
    reduction='mean',
)
```

---

## prompt_strategies.input_output

**URL:** https://docs.axolotl.ai/docs/api/prompt_strategies.input_output.html

**Contents:**
- prompt_strategies.input_output
- Classes
  - RawInputOutputPrompter
  - RawInputOutputStrategy

prompt_strategies.input_output

Module for plain input/output prompt pairs

prompter for raw i/o data

Prompt Strategy class for input/output pairs

**Examples:**

Example 1 (python):
```python
prompt_strategies.input_output.RawInputOutputPrompter()
```

Example 2 (python):
```python
prompt_strategies.input_output.RawInputOutputStrategy(
    *args,
    eos_token=***REDACTED***
    **kwargs,
)
```

---

## prompt_strategies.completion

**URL:** https://docs.axolotl.ai/docs/api/prompt_strategies.completion.html

**Contents:**
- prompt_strategies.completion
- Classes
  - CompletionPromptTokenizingStrategy
  - CompletionPrompter

prompt_strategies.completion

Basic completion text

Tokenizing strategy for Completion prompts.

Prompter for completion

**Examples:**

Example 1 (python):
```python
prompt_strategies.completion.CompletionPromptTokenizingStrategy(
    *args,
    max_length=None,
    **kwargs,
)
```

Example 2 (python):
```python
prompt_strategies.completion.CompletionPrompter()
```

---

## utils.collators.core

**URL:** https://docs.axolotl.ai/docs/api/utils.collators.core.html

**Contents:**
- utils.collators.core

basic shared collator constants

---

## monkeypatch.data.batch_dataset_fetcher

**URL:** https://docs.axolotl.ai/docs/api/monkeypatch.data.batch_dataset_fetcher.html

**Contents:**
- monkeypatch.data.batch_dataset_fetcher
- Functions
  - apply_multipack_dataloader_patch
  - patch_fetchers
  - patched_worker_loop
  - remove_multipack_dataloader_patch

monkeypatch.data.batch_dataset_fetcher

Monkey patches for the dataset fetcher to handle batches of packed indexes.

This patch allows DataLoader to correctly process batches that contain multiple bins of packed sequences.

Apply patches to PyTorch’s DataLoader components.

Worker loop that ensures patches are applied in worker processes.

Remove the monkeypatch and restore original PyTorch DataLoader behavior.

**Examples:**

Example 1 (python):
```python
monkeypatch.data.batch_dataset_fetcher.apply_multipack_dataloader_patch()
```

Example 2 (python):
```python
monkeypatch.data.batch_dataset_fetcher.patch_fetchers()
```

Example 3 (python):
```python
monkeypatch.data.batch_dataset_fetcher.patched_worker_loop(*args, **kwargs)
```

Example 4 (python):
```python
monkeypatch.data.batch_dataset_fetcher.remove_multipack_dataloader_patch()
```

---

## core.datasets.chat

**URL:** https://docs.axolotl.ai/docs/api/core.datasets.chat.html

**Contents:**
- core.datasets.chat
- Classes
  - TokenizedChatDataset

Tokenized chat dataset

**Examples:**

Example 1 (python):
```python
core.datasets.chat.TokenizedChatDataset(
    data,
    model_transform,
    *args,
    message_transform=None,
    formatter=None,
    process_count=None,
    keep_in_memory=False,
    **kwargs,
)
```

---

## utils.freeze

**URL:** https://docs.axolotl.ai/docs/api/utils.freeze.html

**Contents:**
- utils.freeze
- Classes
  - LayerNamePattern
    - Methods
      - match
- Functions
  - freeze_layers_except

module to freeze/unfreeze parameters by name

Represents a regex pattern for layer names, potentially including a parameter index range.

Checks if the given layer name matches the regex pattern.

Parameters: - name (str): The layer name to check.

Returns: - bool: True if the layer name matches the pattern, False otherwise.

Freezes all layers of the given model except for the layers that match given regex patterns. Periods in the patterns are treated as literal periods, not as wildcard characters.

Parameters: - model (nn.Module): The PyTorch model to be modified. - regex_patterns (list of str): List of regex patterns to match layer names to keep unfrozen. Note that you cannot use a dot as a wildcard character in the patterns since it is reserved for separating layer names. Also, to match the entire layer name, the pattern should start with “^” and end with “\(", otherwise it will match any part of the layer name. The range pattern part is optional and it is not compiled as a regex pattern which means you must put "\)” before the range pattern if you want to match the entire layer name. E.g., [“^model.embed_tokens.weight\([:32000]", "layers.2[0-9]+.block_sparse_moe.gate.[a-z]+\)”]

Returns: None; the model is modified in place.

**Examples:**

Example 1 (python):
```python
utils.freeze.LayerNamePattern(pattern)
```

Example 2 (python):
```python
utils.freeze.LayerNamePattern.match(name)
```

Example 3 (python):
```python
utils.freeze.freeze_layers_except(model, regex_patterns)
```

---

## monkeypatch.unsloth_

**URL:** https://docs.axolotl.ai/docs/api/monkeypatch.unsloth_.html

**Contents:**
- monkeypatch.unsloth_

module for patching with unsloth optimizations

---

## utils.schemas.datasets

**URL:** https://docs.axolotl.ai/docs/api/utils.schemas.datasets.html

**Contents:**
- utils.schemas.datasets
- Classes
  - DPODataset
  - KTODataset
  - PretrainingDataset
  - SFTDataset
    - Methods
      - handle_legacy_message_fields
  - StepwiseSupervisedDataset
  - UserDefinedDPOType

utils.schemas.datasets

Pydantic models for datasets-related configuration

DPO configuration subset

KTO configuration subset

Pretraining dataset configuration subset

SFT configuration subset

Handle backwards compatibility between legacy message field mapping and new property mapping system.

Stepwise supervised dataset configuration subset

User defined typing for DPO

User defined typing for KTO

Structure for user defined prompt types

**Examples:**

Example 1 (python):
```python
utils.schemas.datasets.DPODataset()
```

Example 2 (python):
```python
utils.schemas.datasets.KTODataset()
```

Example 3 (python):
```python
utils.schemas.datasets.PretrainingDataset()
```

Example 4 (python):
```python
utils.schemas.datasets.SFTDataset()
```

---

## core.chat.format.llama3x

**URL:** https://docs.axolotl.ai/docs/api/core.chat.format.llama3x.html

**Contents:**
- core.chat.format.llama3x

core.chat.format.llama3x

Llama 3.x chat formatting functions for MessageContents

---

## datasets

**URL:** https://docs.axolotl.ai/docs/api/datasets.html

**Contents:**
- datasets
- Classes
  - TokenizedPromptDataset
    - Parameters

Module containing dataset functionality.

We want this to be a wrapper for an existing dataset that we have loaded. Lets use the concept of middlewares to wrap each dataset. We’ll use the collators later on to pad the datasets.

Dataset that returns tokenized prompts from a stream of text files.

**Examples:**

Example 1 (python):
```python
datasets.TokenizedPromptDataset(
    prompt_tokenizer,
    dataset,
    process_count=None,
    keep_in_memory=False,
    **kwargs,
)
```

---

## prompt_strategies.bradley_terry.llama3

**URL:** https://docs.axolotl.ai/docs/api/prompt_strategies.bradley_terry.llama3.html

**Contents:**
- prompt_strategies.bradley_terry.llama3
- Functions
  - icr

prompt_strategies.bradley_terry.llama3

chatml transforms for datasets with system, input, chosen, rejected to match llama3 chat template

chatml transforms for datasets with system, input, chosen, rejected ex. https://huggingface.co/datasets/argilla/distilabel-intel-orca-dpo-pairs

**Examples:**

Example 1 (python):
```python
prompt_strategies.bradley_terry.llama3.icr(cfg, **kwargs)
```

---

## common.datasets

**URL:** https://docs.axolotl.ai/docs/api/common.datasets.html

**Contents:**
- common.datasets
- Classes
  - TrainDatasetMeta
- Functions
  - load_datasets
    - Parameters
    - Returns
  - load_preference_datasets
    - Parameters
    - Returns

Dataset loading utilities.

Dataclass with fields for training and validation datasets and metadata.

Loads one or more training or evaluation datasets, calling axolotl.utils.data.prepare_datasets. Optionally, logs out debug information.

Loads one or more training or evaluation datasets for RL training using paired preference data, calling axolotl.utils.data.rl.prepare_preference_datasets. Optionally, logs out debug information.

Randomly sample num_samples samples with replacement from dataset.

**Examples:**

Example 1 (python):
```python
common.datasets.TrainDatasetMeta(
    train_dataset,
    eval_dataset=None,
    total_num_steps=None,
)
```

Example 2 (python):
```python
common.datasets.load_datasets(cfg, cli_args=None, debug=False)
```

Example 3 (python):
```python
common.datasets.load_preference_datasets(cfg, cli_args=None)
```

Example 4 (python):
```python
common.datasets.sample_dataset(dataset, num_samples)
```

---

## cli.train

**URL:** https://docs.axolotl.ai/docs/api/cli.train.html

**Contents:**
- cli.train
- Functions
  - do_cli
    - Parameters
  - do_train
    - Parameters

CLI to run training on a model.

Parses axolotl config, CLI args, and calls do_train.

Trains a transformers model by first loading the dataset(s) specified in the axolotl config, and then calling axolotl.train.train. Also runs the plugin manager’s post_train_unload once training completes.

**Examples:**

Example 1 (python):
```python
cli.train.do_cli(config=Path('examples/'), **kwargs)
```

Example 2 (python):
```python
cli.train.do_train(cfg, cli_args)
```

---

## cli.utils.fetch

**URL:** https://docs.axolotl.ai/docs/api/cli.utils.fetch.html

**Contents:**
- cli.utils.fetch
- Functions
  - fetch_from_github
    - Parameters

Utilities for axolotl fetch CLI command.

Sync files from a specific directory in the GitHub repository. Only downloads files that don’t exist locally or have changed.

**Examples:**

Example 1 (python):
```python
cli.utils.fetch.fetch_from_github(dir_prefix, dest_dir=None, max_workers=5)
```

---

## utils.tokenization

**URL:** https://docs.axolotl.ai/docs/api/utils.tokenization.html

**Contents:**
- utils.tokenization
- Functions
  - color_token_for_rl_debug
  - process_tokens_for_rl_debug

Module for tokenization utilities

Helper function to color tokens based on their type.

Helper function to process and color tokens.

**Examples:**

Example 1 (python):
```python
utils.tokenization.color_token_for_rl_debug(
    decoded_token,
    encoded_token,
    color,
    text_only,
)
```

Example 2 (python):
```python
utils.tokenization.process_tokens_for_rl_debug(
    tokens,
    color,
    tokenizer,
    text_only,
)
```

---

## core.trainers.grpo.sampler

**URL:** https://docs.axolotl.ai/docs/api/core.trainers.grpo.sampler.html

**Contents:**
- core.trainers.grpo.sampler
- Classes
  - SequenceParallelRepeatRandomSampler
    - Parameters
    - Methods
      - set_epoch
        - Parameters

core.trainers.grpo.sampler

Repeat random sampler (similar to the one implemented in https://github.com/huggingface/trl/blob/main/trl/trainer/grpo_trainer.py) that adds sequence parallelism functionality; i.e., duplicating data across ranks in the same sequence parallel group.

Sampler for GRPO training with sequence parallelism.

This sampler ensures: - Ranks in the same sequence parallel (SP) group receive identical data. - Each index is repeated multiple times for sampling different completions. - Entire batches are repeated for reuse in multiple updates. - Data is properly distributed across SP groups.

In the table below, the values represent dataset indices. Each SP group has context_parallel_size = 2 GPUs working together on the same data. There are 2 SP groups (SP0 and SP1), with world_size = 4 total GPUs.

grad_accum=2 ▲ ▲ 0 0 [0 0 0 1 1 1] [2 2 2 3 3 3] <- SP groups get different data ▼ | 0 1 [0 0 0 1 1 1] [2 2 2 3 3 3] <- Same data for each SP group GPU | | 1 2 [0 0 0 1 1 1] [2 2 2 3 3 3] <- Repeat same indices for iterations num_iterations=2 ▼ 1 3 [0 0 0 1 1 1] [2 2 2 3 3 3] <- When using gradient accumulation

Sets the epoch for this sampler.

**Examples:**

Example 1 (python):
```python
core.trainers.grpo.sampler.SequenceParallelRepeatRandomSampler(
    dataset,
    mini_repeat_count,
    world_size,
    rank,
    batch_size=1,
    repeat_count=1,
    context_parallel_size=1,
    shuffle=True,
    seed=0,
    drop_last=False,
)
```

Example 2 (unknown):
```unknown
Sequence Parallel Groups
                                |       SP0        |       SP1        |
                                |  GPU 0  |  GPU 1 |  GPU 2  |  GPU 3 |
            global_step  step    <---> mini_repeat_count=3
                                    <----------> batch_size=2 per SP group
```

Example 3 (unknown):
```unknown
2       4         [4 4 4  5 5 5]     [6 6 6  7 7 7]   <- New batch of data indices
                 2       5         [4 4 4  5 5 5]     [6 6 6  7 7 7]
                                    ...
```

Example 4 (python):
```python
core.trainers.grpo.sampler.SequenceParallelRepeatRandomSampler.set_epoch(epoch)
```

---

## evaluate

**URL:** https://docs.axolotl.ai/docs/api/evaluate.html

**Contents:**
- evaluate
- Functions
  - evaluate
    - Parameters
    - Returns
  - evaluate_dataset
    - Parameters
    - Returns

Module for evaluating models.

Evaluate a model on training and validation datasets.

Helper function to evaluate a single dataset.

**Examples:**

Example 1 (python):
```python
evaluate.evaluate(cfg, dataset_meta)
```

Example 2 (python):
```python
evaluate.evaluate_dataset(trainer, dataset, dataset_type, flash_optimum=False)
```

---

## utils.optimizers.adopt

**URL:** https://docs.axolotl.ai/docs/api/utils.optimizers.adopt.html

**Contents:**
- utils.optimizers.adopt
- Functions
  - adopt

utils.optimizers.adopt

Copied from https://github.com/iShohei220/adopt

ADOPT: Modified Adam Can Converge with Any β2 with the Optimal Rate (2024) Taniguchi, Shohei and Harada, Keno and Minegishi, Gouki and Oshima, Yuta and Jeong, Seong Cheol and Nagahara, Go and Iiyama, Tomoshi and Suzuki, Masahiro and Iwasawa, Yusuke and Matsuo, Yutaka

Functional API that performs ADOPT algorithm computation.

**Examples:**

Example 1 (python):
```python
utils.optimizers.adopt.adopt(
    params,
    grads,
    exp_avgs,
    exp_avg_sqs,
    state_steps,
    foreach=None,
    capturable=False,
    differentiable=False,
    fused=None,
    grad_scale=None,
    found_inf=None,
    has_complex=False,
    *,
    beta1,
    beta2,
    lr,
    clip_lambda,
    weight_decay,
    decouple,
    eps,
    maximize,
)
```

---

## prompt_tokenizers

**URL:** https://docs.axolotl.ai/docs/api/prompt_tokenizers.html

**Contents:**
- prompt_tokenizers
- Classes
  - AlpacaMultipleChoicePromptTokenizingStrategy
  - AlpacaPromptTokenizingStrategy
  - AlpacaReflectionPTStrategy
  - DatasetWrappingStrategy
  - GPTeacherPromptTokenizingStrategy
  - InstructionPromptTokenizingStrategy
  - InvalidDataException
  - JeopardyPromptTokenizingStrategy

Module containing PromptTokenizingStrategy and Prompter classes

Tokenizing strategy for Alpaca Multiple Choice prompts.

Tokenizing strategy for Alpaca prompts.

Tokenizing strategy for Alpaca Reflection prompts.

Abstract class for wrapping datasets for Chat Messages

Tokenizing strategy for GPTeacher prompts.

Tokenizing strategy for instruction-based prompts.

Exception raised when the data is invalid

Tokenizing strategy for Jeopardy prompts.

Tokenizing strategy for NomicGPT4All prompts.

Tokenizing strategy for OpenAssistant prompts.

Abstract class for tokenizing strategies

Tokenizing strategy for Reflection prompts.

Tokenizing strategy for SummarizeTLDR prompts.

Parses the tokenized prompt and append the tokenized input_ids, attention_mask and labels to the result

Returns the default values for the tokenize prompt function

**Examples:**

Example 1 (python):
```python
prompt_tokenizers.AlpacaMultipleChoicePromptTokenizingStrategy(
    prompter,
    tokenizer,
    train_on_inputs=False,
    sequence_len=2048,
)
```

Example 2 (python):
```python
prompt_tokenizers.AlpacaPromptTokenizingStrategy(
    prompter,
    tokenizer,
    train_on_inputs=False,
    sequence_len=2048,
)
```

Example 3 (python):
```python
prompt_tokenizers.AlpacaReflectionPTStrategy(
    prompter,
    tokenizer,
    train_on_inputs=False,
    sequence_len=2048,
)
```

Example 4 (python):
```python
prompt_tokenizers.DatasetWrappingStrategy()
```

---

## cli.art

**URL:** https://docs.axolotl.ai/docs/api/cli.art.html

**Contents:**
- cli.art
- Functions
  - print_axolotl_text_art

Axolotl ASCII logo utils.

Prints axolotl ASCII art.

**Examples:**

Example 1 (python):
```python
cli.art.print_axolotl_text_art()
```

---

## utils.callbacks.perplexity

**URL:** https://docs.axolotl.ai/docs/api/utils.callbacks.perplexity.html

**Contents:**
- utils.callbacks.perplexity
- Classes
  - Perplexity
    - Methods
      - compute

utils.callbacks.perplexity

callback to calculate perplexity as an evaluation metric.

Calculate perplexity as defined in https://huggingface.co/docs/transformers/en/perplexity. This is a custom variant that doesn’t re-tokenize the input or re-load the model.

Compute perplexity in a fixed length sliding window across the sequence.

**Examples:**

Example 1 (python):
```python
utils.callbacks.perplexity.Perplexity(tokenizer, max_seq_len, stride=***REDACTED***
```

Example 2 (python):
```python
utils.callbacks.perplexity.Perplexity.compute(model, references=None)
```

---

## cli.utils.train

**URL:** https://docs.axolotl.ai/docs/api/cli.utils.train.html

**Contents:**
- cli.utils.train
- Functions
  - build_command
    - Parameters
    - Returns
  - generate_config_files
    - Parameters
  - launch_training

Utilities for axolotl train CLI command.

Build command list from base command and options.

Generate list of configuration files to process. Yields a tuple of the configuration file name and a boolean indicating whether this is a group of configurations (i.e., a sweep).

Execute training with the given configuration.

**Examples:**

Example 1 (python):
```python
cli.utils.train.build_command(base_cmd, options)
```

Example 2 (python):
```python
cli.utils.train.generate_config_files(config, sweep)
```

Example 3 (python):
```python
cli.utils.train.launch_training(
    cfg_file,
    launcher,
    cloud,
    kwargs,
    launcher_args=None,
    use_exec=False,
)
```

---

## cli.vllm_serve

**URL:** https://docs.axolotl.ai/docs/api/cli.vllm_serve.html

**Contents:**
- cli.vllm_serve
- Classes
  - AxolotlScriptArguments
- Functions
  - do_vllm_serve
    - Returns

CLI to start the vllm server for online RL

Additional arguments for the VLLM server

Starts the VLLM server for serving LLM models used for online RL

Args :param cfg: Parsed doct of the YAML config :param cli_args: dict of additional command-line arguments of type VllmServeCliArgs

**Examples:**

Example 1 (python):
```python
cli.vllm_serve.AxolotlScriptArguments(
    reasoning_parser='',
    enable_reasoning=None,
)
```

Example 2 (python):
```python
cli.vllm_serve.do_vllm_serve(config, cli_args)
```

---

## convert

**URL:** https://docs.axolotl.ai/docs/api/convert.html

**Contents:**
- convert
- Classes
  - FileReader
  - FileWriter
  - JsonParser
  - JsonToJsonlConverter
  - JsonlSerializer
  - StdoutWriter

Module containing File Reader, File Writer, Json Parser, and Jsonl Serializer classes

Reads a file and returns its contents as a string

Writes a string to a file

Parses a string as JSON and returns the result

Converts a JSON file to JSONL

Serializes a list of JSON objects into a JSONL string

Writes a string to stdout

**Examples:**

Example 1 (python):
```python
convert.FileReader()
```

Example 2 (python):
```python
convert.FileWriter(file_path)
```

Example 3 (python):
```python
convert.JsonParser()
```

Example 4 (python):
```python
convert.JsonToJsonlConverter(
    file_reader,
    file_writer,
    json_parser,
    jsonl_serializer,
)
```

---

## monkeypatch.utils

**URL:** https://docs.axolotl.ai/docs/api/monkeypatch.utils.html

**Contents:**
- monkeypatch.utils
- Functions
  - get_cu_seqlens
  - get_cu_seqlens_from_pos_ids
  - mask_2d_to_4d

Shared utils for the monkeypatches

generate a cumulative sequence length mask for flash attention using attn mask

generate a cumulative sequence length mask for flash attention using pos ids

Expands attention_mask from [bsz, seq_len] to [bsz, 1, tgt_seq_len, src_seq_len]. This expansion handles packed sequences so that sequences share the same attention mask integer value when they attend to each other within that sequence. This expansion transforms the mask to lower triangular form to prevent future peeking.

**Examples:**

Example 1 (python):
```python
monkeypatch.utils.get_cu_seqlens(attn_mask)
```

Example 2 (python):
```python
monkeypatch.utils.get_cu_seqlens_from_pos_ids(position_ids)
```

Example 3 (python):
```python
monkeypatch.utils.mask_2d_to_4d(mask, dtype, tgt_len=None)
```

---

## prompt_strategies.pygmalion

**URL:** https://docs.axolotl.ai/docs/api/prompt_strategies.pygmalion.html

**Contents:**
- prompt_strategies.pygmalion
- Classes
  - PygmalionPromptTokenizingStrategy
  - PygmalionPrompter

prompt_strategies.pygmalion

Module containing the PygmalionPromptTokenizingStrategy and PygmalionPrompter class

Tokenizing strategy for Pygmalion.

Prompter for Pygmalion.

**Examples:**

Example 1 (python):
```python
prompt_strategies.pygmalion.PygmalionPromptTokenizingStrategy(
    prompter,
    tokenizer,
    *args,
    **kwargs,
)
```

Example 2 (python):
```python
prompt_strategies.pygmalion.PygmalionPrompter(*args, **kwargs)
```

---

## utils.callbacks.mlflow_

**URL:** https://docs.axolotl.ai/docs/api/utils.callbacks.mlflow_.html

**Contents:**
- utils.callbacks.mlflow_
- Classes
  - SaveAxolotlConfigtoMlflowCallback

utils.callbacks.mlflow_

MLFlow module for trainer callbacks

Callback to save axolotl config to mlflow

**Examples:**

Example 1 (python):
```python
utils.callbacks.mlflow_.SaveAxolotlConfigtoMlflowCallback(axolotl_config_path)
```

---

## loaders.adapter

**URL:** https://docs.axolotl.ai/docs/api/loaders.adapter.html

**Contents:**
- loaders.adapter
- Functions
  - setup_quantized_meta_for_peft
  - setup_quantized_peft_meta_for_training

Adapter loading functionality, including LoRA / QLoRA and associated utils

Replaces quant_state.to with a dummy function to prevent PEFT from moving quant_state to meta device

Replaces dummy quant_state.to method with the original function to allow training to continue

**Examples:**

Example 1 (python):
```python
loaders.adapter.setup_quantized_meta_for_peft(model)
```

Example 2 (python):
```python
loaders.adapter.setup_quantized_peft_meta_for_training(model)
```

---

## cli.cloud.base

**URL:** https://docs.axolotl.ai/docs/api/cli.cloud.base.html

**Contents:**
- cli.cloud.base
- Classes
  - Cloud

base class for cloud platforms from cli

Abstract base class for cloud platforms.

**Examples:**

Example 1 (python):
```python
cli.cloud.base.Cloud()
```

---

## monkeypatch.llama_attn_hijack_flash

**URL:** https://docs.axolotl.ai/docs/api/monkeypatch.llama_attn_hijack_flash.html

**Contents:**
- monkeypatch.llama_attn_hijack_flash
- Functions
  - flashattn_forward_with_s2attn

monkeypatch.llama_attn_hijack_flash

Flash attention monkey patch for llama model

Input shape: Batch x Time x Channel

From: https://github.com/dvlab-research/L

... [Content truncated, total 120,861 chars] ...