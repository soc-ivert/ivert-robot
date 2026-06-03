class AgentError(Exception):
    pass

class SystemPromptError(AgentError):
    pass

class ChatCreationError(AgentError):
    pass