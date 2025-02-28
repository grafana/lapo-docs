import langroid.language_models as lm
import langroid as lr
from llmautodocs.config.llmconfig import llm_config
from langroid.language_models import Role, LLMMessage


def main():
    # llm = lm.OpenAIGPT(llm_config)
    agent = lr.ChatAgent(lr.ChatAgentConfig(llm=llm_config))
    task = lr.Task(agent, interactive=True)

    task.run()
# messages = [
#     LLMMessage(content="You are a helpful assistant", role=Role.SYSTEM),
#     LLMMessage(content="What is the capital of Ontario?", role=Role.USER),
# ]
# response = llm.chat(messages, max_tokens=50)
