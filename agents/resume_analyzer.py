import io
import json
import re
from typing import Dict, Any
from tools.groq_utils import create_chat_completion

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from PDF, DOCX, or TXT file bytes."""
    filename_lower = filename.lower()
    text = ""
    
    if filename_lower.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            print(f"PDF extraction: {page_count} pages, {len(text)} characters extracted")
        except ImportError:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise ValueError(f"Failed to read PDF file: {str(e)}")

    elif filename_lower.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [para.text for para in doc.paragraphs if para.text]
            text = "\n".join(paragraphs)
            print(f"DOCX extraction: {len(paragraphs)} paragraphs, {len(text)} characters extracted")
        except ImportError:
            raise ValueError("python-docx is required. Please install via: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Failed to read DOCX file: {str(e)}")

    elif filename_lower.endswith((".txt", ".md")):
        text = file_bytes.decode("utf-8", errors="ignore")
        print(f"TXT extraction: {len(text)} characters extracted")
    else:
        raise ValueError("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")

    cleaned_text = text.strip()
    
    # More lenient threshold and better error message
    if not cleaned_text:
        raise ValueError("The uploaded document appears to be empty or could not be read.")
    elif len(cleaned_text) < 20:
        raise ValueError(f"The uploaded document contains very little text ({len(cleaned_text)} characters). Please ensure your resume has sufficient content.")
    
    print(f"Final cleaned text length: {len(cleaned_text)} characters")
    return cleaned_text


def analyze_resume(raw_text: str) -> Dict[str, Any]:
    """Extract structured candidate profile from resume text using Groq LLM."""
    prompt = f"""
    You are an expert Technical Recruiter and Resume Analyzer Agent.
    Analyze the candidate's resume text below and extract a structured, grounded candidate profile.

    STRICT RULES:
    1. Only include information explicitly stated in the resume text.
    2. Do NOT invent companies, metrics, projects, or skills not present in the text.
    3. Return valid JSON only, matching the exact schema below.

    SCHEMA:
    {{
        "candidate_name": "Full Name or 'Candidate'",
        "education": [
            {{"degree": "Degree name", "institution": "College/University", "year": "Year or N/A"}}
        ],
        "skills": ["Skill 1", "Skill 2"],
        "programming_languages": ["Python", "JavaScript"],
        "frameworks_and_tools": ["FastAPI", "Docker", "PyTorch"],
        "projects": [
            {{
                "title": "Project Name",
                "technologies": ["Tech 1", "Tech 2"],
                "description": "Brief summary of what was built",
                "key_claims": ["Claimed achievements, e.g., 'Built LangGraph RAG'"]
            }}
        ],
        "experience": [
            {{
                "role": "Job/Internship Title",
                "company": "Company Name",
                "duration": "Duration or N/A",
                "responsibilities": ["Key responsibility 1"]
            }}
        ],
        "certifications": ["Cert 1"],
        "achievements": ["Achievement 1"]
    }}

    RESUME TEXT:
    \"\"\"{raw_text[:7000]}\"\"\"

    Return ONLY the raw JSON object. Do not include markdown code block formatting.
    """

    try:
        response = create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        
        profile = json.loads(content)
        profile["raw_resume_text"] = raw_text[:4000]
        return profile
    except Exception as e:
        return {
            "candidate_name": "Candidate",
            "education": [],
            "skills": ["Engineering"],
            "programming_languages": [],
            "frameworks_and_tools": [],
            "projects": [{"title": "Projects from Resume", "technologies": [], "description": raw_text[:300], "key_claims": []}],
            "experience": [],
            "certifications": [],
            "achievements": [],
            "raw_resume_text": raw_text[:4000]
        }