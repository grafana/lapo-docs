> [!NOTE]  
> This is a Hackathon project Feb 2025

# LLM auto update docs

This project aims to create a workflow or llm agent to keep documentation up to date based on the changes to source code.

## Requirements

* python 3.12.7
* pdm (latest)
* A gemini key in your env as `$GEMINI_API_KEY`

## Usage

### The python nonsense

Python installation and dependencies are hard to handle, we use pdm for dependency management and virtual environments. See the [pdm docs](https://pdm.fming.dev/) for more information.

Run the following commands:

```bash
pdm venv create
pdm use .venv
pdm install
```

Is this failing?  make sure you are using python 3.12.7

