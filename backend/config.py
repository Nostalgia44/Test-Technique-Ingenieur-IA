# get_client() initializes and returns an OpenAI client configured with API key from environment variables
def get_client():
    from openai import OpenAI
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Retrieve OpenRouter API key from environment variables
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not defined")
    
    # Initialize OpenAI client with OpenRouter endpoint
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",  # OpenRouter API endpoint
        api_key=api_key
    )
    return client