import os
from typing import Optional
import google.generativeai as genai
import json
import re

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)

# Get model name from environment or use default
# Common models: gemini-1.5-flash, gemini-1.5-pro, gemini-pro
# You can set GEMINI_MODEL environment variable to override
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


async def analyze_cv(cv_text: str) -> str:
    """Analyze CV and extract key information"""
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""Analyze the following CV and extract key information about:
- Work experience
- Technical skills
- Education
- Notable achievements
- Areas of specialization

CV:
{cv_text}

Provide a structured analysis of the CV."""

    response = model.generate_content(prompt)
    return response.text


async def analyze_job_offer(job_offer_text: str) -> str:
    """Analyze job offer and extract key information"""
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""Analyze the following job offer and extract key information about:
- Technical requirements
- Required experience
- Necessary skills
- Responsibilities
- Additional preferences

Job offer:
{job_offer_text}

Provide a structured analysis of the offer."""

    response = model.generate_content(prompt)
    return response.text


async def compare_cv_and_offer(
    cv_analysis: str,
    job_offer_analysis: str,
    additional_considerations: Optional[str] = None
) -> dict:
    """Compare CV and job offer to generate analysis"""
    model = genai.GenerativeModel(MODEL_NAME)

    considerations_text = f"\nAdditional user considerations that must always be related to the job offer: {additional_considerations}" if additional_considerations else ""

    prompt = f"""Compare the CV analysis with the job offer analysis and provide:

1. STRENGTHS: List of 5-8 strengths the candidate has for this offer (format: bullet list)
2. WEAKNESSES: List of 5-8 weaknesses or areas for improvement (format: bullet list)
3. RECOMMENDATION: A 2-3 line summary indicating whether you recommend applying or not, and why
4. 4-WEEK PLAN: A detailed 4-week plan (one week per section) for the candidate to catch up on missing concepts. Each week must include specific objectives and concrete actions.

CV Analysis:
{cv_analysis}

Job Offer Analysis:
{job_offer_analysis}
{considerations_text}

Respond ONLY in valid JSON format with this exact structure (no additional text before or after):
{{
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...],
  "recommendation": "2-3 line recommendation",
  "matchPercentage": 75,
  "fourWeekPlan": "Detailed 4-week plan with clear format, each week on a separate line"
}}"""

    response = model.generate_content(prompt)
    text = response.text

    # Try to extract JSON from the response
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            return {
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", []),
                "recommendation": result.get("recommendation", ""),
                "matchPercentage": result.get("matchPercentage", 50),
                "fourWeekPlan": result.get("fourWeekPlan", "")
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")

    # Fallback parsing
    return parse_fallback_response(text)


def parse_fallback_response(text: str) -> dict:
    """Fallback parser if JSON extraction fails"""
    strengths = []
    weaknesses = []
    recommendation = ""
    match_percentage = 50
    four_week_plan = ""

    lines = text.split('\n')
    current_section = ""

    for line in lines:
        line_lower = line.lower()
        if 'puntos fuertes' in line_lower or 'strengths' in line_lower:
            current_section = 'strengths'
        elif 'puntos débiles' in line_lower or 'weaknesses' in line_lower:
            current_section = 'weaknesses'
        elif 'recomendación' in line_lower or 'recommendation' in line_lower:
            current_section = 'recommendation'
        elif 'plan' in line_lower or '4 semanas' in line_lower:
            current_section = 'plan'
        elif line.strip().startswith(('-', '•', '*')):
            item = line.strip()[1:].strip()
            if current_section == 'strengths':
                strengths.append(item)
            elif current_section == 'weaknesses':
                weaknesses.append(item)
        elif current_section == 'recommendation' and line.strip():
            recommendation += line.strip() + ' '
        elif current_section == 'plan' and line.strip():
            four_week_plan += line.strip() + '\n'

    total_points = len(strengths) + len(weaknesses)
    if total_points > 0:
        match_percentage = round((len(strengths) / total_points) * 100)

    return {
        "strengths": strengths if strengths else ["Analysis completed"],
        "weaknesses": weaknesses if weaknesses else ["Review details"],
        "recommendation": recommendation.strip() or "Review the complete analysis to make a decision.",
        "matchPercentage": match_percentage,
        "fourWeekPlan": four_week_plan.strip() or "Personalized improvement plan based on the analysis."
    }
