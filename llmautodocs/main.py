import langroid.language_models as lm
import langroid as lr
from llmautodocs.config.llmconfig import llm_config
from langroid.language_models import Role, LLMMessage
from llmautodocs.code_agent.code_agent import CodeChangeAnalysisAgent


def main():
    llm = lm.OpenAIGPT(llm_config)

    agent = CodeChangeAnalysisAgent(llm)
    result = agent.analyze_diff("diff_content")
    print(result)
