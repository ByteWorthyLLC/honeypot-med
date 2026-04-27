---
license: mit
task_categories:
- text-classification
- question-answering
language:
- en
tags:
- prompt-injection
- healthcare-ai
- local-first
- honeypot-med
---

# Honeypot Med Healthcare AI Challenge Dataset Card

This card describes a local Honeypot Med eval artifact. It is ready to paste into a Hugging Face Dataset repository, but generation does not upload anything.

## Dataset Summary

- Source: `pack:healthcare-challenge`
- Events: 10
- High-risk events: 2
- Proven findings: 3

## Intended Use

Use these records for local healthcare AI prompt-injection regression tests, not for medical decision-making.

## Limitations

The records are synthetic or user-supplied challenge traps. They do not establish clinical safety, regulatory compliance, or broad model robustness.

## Local Generation

```bash
python app.py eval-kit --pack healthcare-challenge --outdir reports/eval-kit
```
