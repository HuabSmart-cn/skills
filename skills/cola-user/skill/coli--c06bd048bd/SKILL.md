---
name: coli
description: "Speech recognition (ASR) toolkit — transcribe audio files to text. Use when the user provides an audio file to transcribe."
homepage: https://github.com/nicepkg/coli
metadata:
  category: system
---

# Coli — Speech Recognition (ASR)

`coli` is a CLI for speech recognition (ASR). Only the `asr` subcommand is available.

**Do NOT use `coli tts`, `coli cloud-tts`, or any other subcommand.** Only `coli asr` is permitted.

## When to use

- User provides an audio file to transcribe → **ASR**

## ASR (transcription)

Transcribe audio files. Default engine is `sensevoice` (multilingual).

- `coli asr <audio-file>`
- `coli asr --engine whisper <audio-file>` (use only if user asks for Whisper)
- `coli asr --help` for supported formats and engines

## Discovery

Run `coli asr --help` for detailed options. Check help before constructing commands — flags may change across versions.
