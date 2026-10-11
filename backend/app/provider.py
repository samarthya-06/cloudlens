from app.gemini import GeminiProvider


def create_provider(settings, repository):
    return GeminiProvider(settings, repository)
