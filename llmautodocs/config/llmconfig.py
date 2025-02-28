import langroid.language_models as lm

llm_config = lm.OpenAIGPTConfig(
    chat_model="gemini/" + lm.GeminiModel.GEMINI_2_FLASH
)
