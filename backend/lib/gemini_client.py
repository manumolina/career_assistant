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

    prompt = f"""Analiza el siguiente CV y extrae información clave sobre:
- Experiencia laboral
- Habilidades técnicas
- Educación
- Logros destacados
- Áreas de especialización

CV:
{cv_text}

Proporciona un análisis estructurado del CV."""

    response = model.generate_content(prompt)
    return response.text


async def analyze_job_offer(job_offer_text: str) -> str:
    """Analyze job offer and extract key information"""
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""Analiza la siguiente oferta de trabajo y extrae información clave sobre:
- Requisitos técnicos
- Experiencia requerida
- Habilidades necesarias
- Responsabilidades
- Preferencias adicionales

Oferta de trabajo:
{job_offer_text}

Proporciona un análisis estructurado de la oferta."""

    response = model.generate_content(prompt)
    return response.text


async def compare_cv_and_offer(
    cv_analysis: str,
    job_offer_analysis: str,
    additional_considerations: Optional[str] = None
) -> dict:
    """Compare CV and job offer to generate analysis"""
    model = genai.GenerativeModel(MODEL_NAME)

    considerations_text = f"\nConsideraciones adicionales del usuario que deben estar siempre relacionadas con la oferta de trabajo: {additional_considerations}" if additional_considerations else ""

    prompt = f"""Compara el análisis del CV con el análisis de la oferta de trabajo y proporciona:

1. PUNTOS FUERTES: Lista de 5-8 puntos fuertes que el candidato tiene para esta oferta (formato: lista con viñetas)
2. PUNTOS DÉBILES: Lista de 5-8 puntos débiles o áreas de mejora (formato: lista con viñetas)
3. RECOMENDACIÓN: Un resumen de 2-3 líneas indicando si recomiendas aplicar o no, y por qué
4. PLAN DE 4 SEMANAS: Un plan detallado de 4 semanas (una semana por sección) para que el candidato se ponga al día con los conceptos que le faltan. Cada semana debe incluir objetivos específicos y acciones concretas.

Análisis del CV:
{cv_analysis}

Análisis de la Oferta:
{job_offer_analysis}
{considerations_text}

Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta (sin texto adicional antes o después):
{{
  "strengths": ["fortaleza 1", "fortaleza 2", ...],
  "weaknesses": ["debilidad 1", "debilidad 2", ...],
  "recommendation": "recomendación de 2-3 líneas",
  "matchPercentage": 75,
  "fourWeekPlan": "Plan detallado de 4 semanas con formato claro, cada semana en una línea separada"
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
        "strengths": strengths if strengths else ["Análisis completado"],
        "weaknesses": weaknesses if weaknesses else ["Revisar detalles"],
        "recommendation": recommendation.strip() or "Revisa el análisis completo para tomar una decisión.",
        "matchPercentage": match_percentage,
        "fourWeekPlan": four_week_plan.strip() or "Plan de mejora personalizado basado en el análisis."
    }
