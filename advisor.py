"""
Generate resume improvement tips using gpt-4o-mini,
comparing the resume against a specific job description.
"""
from openai import OpenAI

from backend.config import OPENAI_API_KEY, TIPS_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY)

_SYSTEM_PROMPT = """\
You are an expert career coach and resume reviewer.
You will receive a candidate's resume and a job description.
Your task: give 3-5 concise, actionable tips on how the candidate
can improve their resume to better match this specific job.

Format your response as a numbered list. Be specific — reference
actual skills, keywords, or experiences missing from the resume.
Keep each tip to 1-2 sentences. Be direct and constructive.
"""


def get_tips(resume_text: str, job_text: str, job_title: str) -> str:
    """
    Returns a multi-line string with numbered improvement tips.
    """
    user_message = f"""
## Job Title
{job_title}

## Job Description
{job_text[:3000]}

## Candidate Resume
{resume_text[:3000]}

Please provide improvement tips for this resume to better match the job above.
""".strip()

    response = _client.chat.completions.create(
        model=TIPS_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()
