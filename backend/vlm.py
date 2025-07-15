import config
from openai import OpenAI
import base64

# Reuse existing configuration from main app
client = config.get_client()

def analyze_image(image_path, question="Describe this image in details."):
    """Simpler solution for exercise 3 - VLM image analysis"""
    
    print(f"Analyzing image: {image_path}")
    print(f"Question: {question}")
    
    # Encode image to base64 format required by the API
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Call QwenVL model via OpenRouter API
    response = client.chat.completions.create(
        model="qwen/qwen-2-vl-7b-instruct",  # Vision-language model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},  # Text prompt
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}  # Base64 image
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    # Extract and display the analysis result
    result = response.choices[0].message.content
    print(f"\nResult:\n{result}")
    return result

if __name__ == "__main__":
    # Test the function with a sample image and question
    analyze_image("test_image.jpg", "What do you see in this image? Describe it in detail.")