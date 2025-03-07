from dataclasses import dataclass
from types import NoneType
from typing import TypedDict
from rich import print as rprint
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.anthropic import AnthropicModel
import os
import tempfile
import subprocess
import logfire


def scrubbing_callback(m: logfire.ScrubMatch):
    if (
        m.path == ('message', 'prompt')
        and m.pattern_match.group(0) == 'credential'
    ):
        return m.value

    if (
        m.path == ('attributes', 'prompt')
        and m.pattern_match.group(0) == 'credential'
    ):
        return m.value


logfire.configure(send_to_logfire="if-token-present", scrubbing=logfire.ScrubbingOptions(callback=scrubbing_callback))


class PullRequestContent(BaseModel):
    reasoning: str = Field(
        description="The reason behind the pull request changes",
    )
    patch_diff: str = Field(
        description="The patch diff for the pull request",
    )
    title: str = Field(
        description="The title of the pull request",
    )


class DocumentContent(TypedDict):
    file_path: str
    content: str
    exists: bool


@dataclass
class Deps:
    docs_repo_path: str


generate_pr_agent = Agent(
    AnthropicModel('claude-3-5-sonnet-latest'),
    # GeminiModel('gemini-2.0-flash'), # gemini sucks at generating patches
    retries=3,
    deps_type=Deps,
    system_prompt=(
        'You are an expert system on generating git patches for documentation based on code changes',
        'You will analyze the presented list of POSSIBLE affected documents by a code change (diff)'
        'think carefully if the code change (diff) affects the document related  content'
        'you can use the full document content to better decide'
        'If the code changes affect the document in a way that it requires changes then you will generate a pull request',
        'to update the document.'
        'you must only change the content of the document that is affected by the code change (diff)',
        'Generate the patch for git if multiple patches for multiple files are generated, concat them all in one'
        'use the `get_document` tool to get the full content of a document.'
        'use the `validate_patch` tool to validate the generated patch. it should return OK if the patch is valid'
    ),
    result_type=PullRequestContent,
)


@generate_pr_agent.tool(retries=5)
async def get_document(ctx: RunContext[Deps], file_name: str) -> DocumentContent:
    print("get_document", file_name)
    file_path = os.path.join(ctx.deps.docs_repo_path, file_name)
    if not os.path.exists(file_path):
        return {"file_path": file_name, "content": "", "exists": False}
    with open(file_path, "r") as f:
        return {"file_path": file_name, "content": f.read(), "exists": True}


@generate_pr_agent.tool(retries=10)
async def validate_patch(ctx: RunContext[Deps], patch: str) -> str:
    print("validate_patch", patch)
    # store patch in a temporal file
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(patch)
        f.flush()
        print("patch", f.name)
        try:
            result = subprocess.run(["git", "apply", "--check", f.name],
                                    cwd=ctx.deps.docs_repo_path,
                                    capture_output=True,
                                    text=True,
                                    check=True)
            print("patch valid", result)
            return "OK"
        except Exception as e:
            print("error with patch", e.stderr)
            raise ModelRetry("error validating patch: " + str(e.stderr))
