import requests
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def generate_image(user_query: str) -> dict:
    """Generate image using Pollinations AI (free, no API key required)"""

    print("\n" + "="*60)
    print("   IMAGE GENERATION PIPELINE STARTED")
    print("="*60)

    # Step 1 - Generate image URL using Pollinations
    print("\n🎨 Step 1: Generating image...")
    encoded_query = quote(user_query)
    # Pollinations AI - simple URL format, no model parameter
    image_url = f"https://image.pollinations.ai/prompt/{encoded_query}?width=1024&height=768&nologo=true&seed={int(datetime.now().timestamp())}"

    try:
        response = requests.get(image_url, timeout=90)
        response.raise_for_status()
        image_bytes = response.content
        content_type = response.headers.get("content-type", "")
        
        if not image_bytes or not content_type.startswith("image/"):
            raise RuntimeError("Image provider returned an empty or invalid response")
        
        print("✅ Image generated successfully!")
        
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}") from e

    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    return {
        "original_query": user_query,
        "enhanced_prompt": user_query,
        "image_url": image_url,
        "image_bytes": image_bytes,
        "generated_at": now
    }