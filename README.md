> [!NOTE]  
> This is a Hackathon project Feb 2025

# LLM auto update docs

This project aims to create a workflow or llm agent to keep documentation up to date based on the changes to source code.

Lapo Docs stands for 

**L**LM
**A**gent
**P**atcher
**O**f
**D**ocs

## Requirements

* python 3.12.7
* [uv](https://github.com/astral-sh/uv) (python package manager)
* An anthropic api key stored in the environment variable `ANTHROPIC_API_KEY`
* A GITHUB_TOKEN stored in the environment variable `GITHUB_TOKEN`[1]

[1] If you use github CLI you can add GITHUB_TOKEN=$(gh auth token) before any `uv` command to set the environment variable


## Usage

### The python nonsense

Python installation and dependencies are hard to handle, we use uv for dependency management and virtual environments. See [uv](https://github.com/astral-sh/uv) for more information.

## Run

using UV you can just run the example directly

```bash
uv run lapo.py
```

Is this failing?  make sure you are using python 3.12.7

Does it keep failing? Python is like that. 
