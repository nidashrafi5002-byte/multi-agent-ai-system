import requests
import os
import sys
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def enhance_prompt(user_query: str) -> str:
    """Use AI to enhance the image prompt"""
    prompt = f"""
    You are an expert image prompt engineer.
    Convert this user request into a detailed,
    vivid image generation prompt.

    User request: {user_query}

    Create a detailed prompt that includes:
    - Main subject
    - Art style
    - Lighting
    - Colors
    - Mood
    - Quality keywords like: highly detailed, 
      photorealistic, 8k, professional

    Reply with ONLY the enhanced prompt.
    Nothing else. No explanation.
    Keep it under 200 characters.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Prompt enhancement failed: {e}")
        # Fallback to original query if enhancement fails
        return user_query[:200]

def generate_image(user_query: str) -> dict:
    """Generate image using Pollinations AI"""

    print("\n" + "="*60)
    print("   IMAGE GENERATION PIPELINE STARTED")
    print("="*60)

    # Step 1 - Enhance prompt
    print("\n✨ Step 1: Enhancing prompt...")
    enhanced_prompt = enhance_prompt(user_query)
    print(f"✅ Enhanced prompt: {enhanced_prompt[:80]}...")

    # Step 2 - Generate image
    print("\n🎨 Step 2: Generating image...")
    encoded_prompt = quote(enhanced_prompt)
    
    # Pollinations AI URL with additional parameters for better quality
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={int(datetime.now().timestamp())}&model=flux"

    # Verify the URL is accessible
    try:
        response = requests.head(image_url, timeout=10)
        if response.status_code == 200:
            print("✅ Image generated successfully!")
        else:
            print(f"⚠️ Image URL returned status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Could not verify image URL: {e}")

    now = datetime.now().strftime("%d-%m-%Y %H:%M")

    return {
        "original_query": user_query,
        "enhanced_prompt": enhanced_prompt,
        "image_url": image_url,
        "generated_at": now
    }