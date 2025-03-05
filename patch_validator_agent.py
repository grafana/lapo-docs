from typing import TypedDict, List
from rich import print as rprint
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.gemini import GeminiModel
import os
import tempfile
import subprocess

validate_patch_agent = Agent(
    GeminiModel('gemini-2.0-flash'),
    retries=3,
    deps_type=None,
    system_prompt=(
        'You are an expert system at validating git patches'
        'you will analyze the passed patch and determine if the format is correct'
        'if the format is correct you will return simply PATCH_VALID'
        'if the format is incorrect you will return a description of the error'
        'you will objectively evaluate the patch without providing any recommendation'
        'you will not comment in anyway on the files or code in the patch'
        'you must focus in the validity of the git patch format'
    ),
    result_type=str,
)
