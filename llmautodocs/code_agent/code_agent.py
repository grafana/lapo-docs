from langroid.agent.chat_agent import ChatAgent, ChatAgentConfig


class CodeChangeAnalysisAgent:

    def __init__(self, llm):
        # Create a config for the agent
        config = ChatAgentConfig(
            llm=llm,
            system_message="""
            You are a Code Change Analysis Agent. Your job is to:
            1. Analyze git diffs to identify meaningful code changes
            2. Extract function signature changes, parameter modifications, and behavior changes
            3. Provide a structured report of what changed

            Focus on changes that would affect documentation, such as:
            - API changes (function signatures, parameters)
            - Behavior changes
            - New features or functionality
            """
        )

        # Create the agent
        self.agent = ChatAgent(config=config)

    def analyze_diff(self, diff_content):
        """
        Analyze a git diff and extract meaningful changes

        Args:
            diff_content (str): The git diff content

        Returns:
            str: A structured report of the changes
        """
        # Create a task for this conversation
        task = self.agent.create_task()

        # Run the task with the diff content
        result = task.run(
            f"""
            Please analyze this git diff and provide a structured report of meaningful changes:

            ```
            {diff_content}
            ```

            Focus on extracting:
            1. Changed function signatures
            2. Modified parameters or return values
            3. New or removed functions
            4. Behavior changes

            Format the output as a structured JSON object with the following fields:
            - changed_functions: List of functions that changed
            - for each function:
              - name: Function name
              - old_signature: Previous signature (if applicable)
              - new_signature: New signature
              - params_changed: List of parameters that changed
              - behavior_changes: Description of behavior changes
            """
        )

        return result.content
