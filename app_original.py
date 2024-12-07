import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def encode_image(image_path):
    """
    Encode an image file to base64 string.
    
    Args:
        image_path (str): Path to the image file.
    Returns:
        str: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_text(text):
    """
    Send text to GPT-4 for analysis
    
    Args:
        text (str): Text to analyze
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes text and provides insights."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=1500
        )

        # Output GPT-4's response
        print("GPT-4 Response:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

def process_image(image_path):
    """
    Process an image by encoding it to base64.
    
    Args:
        image_path (str): Path to the image file.
    """
    try:
        # Encode the image to Base64
        encoded_image = encode_image(image_path)
        print(f"Successfully encoded image: {image_path}")
        print(f"First 100 characters of base64 string: {encoded_image[:100]}...")
        return encoded_image
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def analyze_image(image_path):
    """
    Send an encoded image to GPT-4 for analysis
    
    Args:
        image_path (str): Path to the image file.
    """
    try:
        # First encode the image
        base64_image = encode_image(image_path)
        
        # Send to GPT-4 for analysis
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please list each item exactly as it appears on the receipt, including the exact item codes (like '014400962730') and their prices. Do not interpret or modify any values. List each line exactly as shown, including any 'F' or 'N' suffixes. Then provide the exact subtotal, tax, and final total."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )

        # Output GPT-4's analysis
        print("\nReceipt Analysis:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error analyzing image: {e}")

# Example text to analyze
sample_text = """
Please analyze this text and provide insights about its key points,
main themes, and any important details you notice.
"""

# Path to the local image
image_local = "C:/Users/sanhe/Downloads/IMG_4210.jpeg"

# Process both text and image
print("\nAnalyzing text:")
analyze_text(sample_text)

print("\nAnalyzing receipt image:")
analyze_image(image_local)