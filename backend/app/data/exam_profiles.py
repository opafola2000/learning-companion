"""Certification exam profiles for grounded curriculum and quiz generation."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExamProfile:
    cert_name: str
    exam_code: str
    blueprint_version: str
    effective_date: str
    passing_score: str
    question_style: str
    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=list)
    trusted_resource_domains: list[str] = field(default_factory=list)
    freshness_months: int = 18


DEFAULT_PROFILE = ExamProfile(
    cert_name="Generic Certification",
    exam_code="GENERIC",
    blueprint_version="2025-01",
    effective_date="2025-01-01",
    passing_score="varies",
    question_style="single-answer multiple choice with scenario-based questions",
    allowed_domains=[
        "aws.amazon.com",
        "docs.aws.amazon.com",
        "learn.microsoft.com",
        "cloud.google.com",
        "comptia.org",
        "isc2.org",
        "oracle.com",
    ],
    trusted_resource_domains=[
        "aws.amazon.com",
        "docs.aws.amazon.com",
        "learn.microsoft.com",
        "developer.mozilla.org",
        "youtube.com",
    ],
)

EXAM_PROFILES: list[ExamProfile] = [
    ExamProfile(
        cert_name="AWS Certified AI Practitioner",
        exam_code="AIF-C01",
        blueprint_version="2024-08",
        effective_date="2024-08-01",
        passing_score="720/1000",
        question_style="65 questions, 90 minutes, single-answer and scenario-based",
        allowed_domains=[
            "aws.amazon.com",
            "docs.aws.amazon.com",
            "d1.awsstatic.com",
            "aws.amazon.com/certification",
        ],
        trusted_resource_domains=[
            "aws.amazon.com",
            "docs.aws.amazon.com",
            "learn.amazonaws.com",
            "youtube.com",
        ],
    ),
    ExamProfile(
        cert_name="AWS Certified Solutions Architect",
        exam_code="SAA-C03",
        blueprint_version="2024-01",
        effective_date="2024-01-01",
        passing_score="720/1000",
        question_style="65 questions, 130 minutes, scenario-heavy",
        allowed_domains=[
            "aws.amazon.com",
            "docs.aws.amazon.com",
            "d1.awsstatic.com",
        ],
        trusted_resource_domains=[
            "aws.amazon.com",
            "docs.aws.amazon.com",
            "youtube.com",
        ],
    ),
]

BLOCKED_DOMAINS = [
    "braindump",
    "examcollection",
    "pass4sure",
    "actualtests",
]


def match_exam_profile(skill_name: str) -> ExamProfile:
    normalized = skill_name.lower()
    for profile in EXAM_PROFILES:
        if profile.cert_name.lower() in normalized or profile.exam_code.lower() in normalized:
            return profile
        cert_tokens = profile.cert_name.lower().split()
        if all(token in normalized for token in cert_tokens[:3]):
            return profile
    if "aws" in normalized and "ai" in normalized:
        return EXAM_PROFILES[0]
    if "aws" in normalized and "architect" in normalized:
        return EXAM_PROFILES[1]
    return DEFAULT_PROFILE
