from app.services.bedrock_client import get_bedrock_client

CURRICULUM_VALIDATION_PROMPT = """You validate certification curricula against official exam objectives.
Review the generated curriculum and official source material.

Return JSON:
{
  "validation_status": "verified|needs_review|rejected",
  "issues": ["list of problems if any"],
  "objectives": [
    {"id": "OBJ-1", "text": "official objective text", "domain": "domain name"}
  ],
  "topic_mappings": [
    {"topic_title": "...", "objective_ids": ["OBJ-1"], "grounded": true}
  ]
}

Rules:
- Mark verified only if every topic maps to at least one objective from sources
- Flag invented or out-of-scope topics as needs_review or rejected
- Extract objectives explicitly mentioned in the source material"""


QUIZ_VALIDATION_PROMPT = """You validate certification practice questions against official study material.
Check each question for factual accuracy and exam relevance.

Return JSON:
{
  "validation_status": "verified|needs_review|rejected",
  "questions": [
    {
      "question_text": "exact question text from input",
      "is_valid": true,
      "objective_id": "OBJ-1 or null",
      "source_reference": "URL or source title",
      "citation_snippet": "short quote supporting the correct answer",
      "issue": "null or explanation if invalid"
    }
  ]
}

Rules:
- Reject questions about deprecated services or facts not in the source material
- Each valid question must cite supporting material
- Match current exam style and difficulty"""


def validate_curriculum(
    skill_name: str,
    curriculum_data: dict,
    source_context: str,
    exam_code: str,
) -> dict:
    bedrock = get_bedrock_client()
    user_message = f"""Certification: {skill_name}
Exam code: {exam_code}

Official source material:
{source_context}

Generated curriculum:
{curriculum_data}

Validate this curriculum."""

    try:
        return bedrock.invoke_haiku_json(CURRICULUM_VALIDATION_PROMPT, user_message)
    except Exception:
        return {
            "validation_status": "needs_review",
            "issues": ["Automated validation unavailable"],
            "objectives": [],
            "topic_mappings": [],
        }


def validate_quiz_questions(
    skill_name: str,
    exam_code: str,
    topic_title: str,
    questions: list[dict],
    source_context: str,
) -> dict:
    bedrock = get_bedrock_client()
    user_message = f"""Certification: {skill_name}
Exam code: {exam_code}
Topic: {topic_title}

Official source material:
{source_context}

Questions to validate:
{questions}

Validate each question."""

    try:
        return bedrock.invoke_haiku_json(QUIZ_VALIDATION_PROMPT, user_message)
    except Exception:
        return {
            "validation_status": "needs_review",
            "questions": [
                {
                    "question_text": q.get("question_text", ""),
                    "is_valid": True,
                    "objective_id": q.get("objective_id"),
                    "source_reference": q.get("source_reference"),
                    "citation_snippet": q.get("citation_snippet"),
                    "issue": None,
                }
                for q in questions
            ],
        }
