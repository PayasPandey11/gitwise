class GitWiseError(Exception):
    pass

class SecurityError(GitWiseError):
    pass

class GitOperationError(GitWiseError):
    pass

class LLMError(GitWiseError):
    pass

class ConfigurationError(GitWiseError):
    pass

class ValidationError(GitWiseError):
    pass

class NetworkError(GitWiseError):
    pass