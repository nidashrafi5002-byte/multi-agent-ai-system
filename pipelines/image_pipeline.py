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
    """Search for images using Unsplash Source API (free, no API key required)"""

    print("\n" + "="*60)
    print("   IMAGE SEARCH PIPELINE STARTED")
    print("="*60)

    # Step 1 - Generate image URL using Unsplash Source
    print("\n🔍 Step 1: Searching for images...")
    encoded_query = quote(user_query)
    # Unsplash Source API - free, no authentication required
    image_url = f"https://source.unsplash.com/1024x768/?{encoded_query}&sig={int(datetime.now().timestamp())}"

    try:
        response = requests.get(image_url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        image_bytes = response.content
        content_type = response.headers.get("content-type", "")
        
        if not image_bytes or not content_type.startswith("image/"):
            raise RuntimeError("Image provider returned an empty or invalid response")
        
        print("✅ Image fetched successfully!")
        
    except Exception as e:
        raise RuntimeError(f"Image search failed: {e}") from e

    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    return {
        "original_query": user_query,
        "enhanced_prompt": f"Photo of {user_query}",
        "image_url": image_url,
        "image_bytes": image_bytes,
        "generated_at": now
    }