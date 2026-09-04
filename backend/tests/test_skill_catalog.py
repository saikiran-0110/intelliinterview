from app.services.skill_catalog import (
    compare_skills,
    extract_evidence_passage,
    extract_qualifications,
    extract_seniority,
    extract_skills,
    extract_years_experience,
    parse_cv_profile,
    parse_job_requirements,
)


def test_extract_skills_matches_aliases():
    text = "I use Python, FastAPI, React.js, k8s, postgres, and GitHub Actions."
    skills = extract_skills(text)
    assert "python" in skills
    assert "fastapi" in skills
    assert "react" in skills
    assert "kubernetes" in skills
    assert "postgresql" in skills
    assert "ci/cd" in skills


def test_extract_skills_is_sorted_and_unique():
    skills = extract_skills("Python python PYTHON FastAPI")
    assert skills == sorted(set(skills))
    assert skills.count("python") == 1


def test_extract_years_experience_takes_maximum():
    text = "3 years of experience, later 8+ years experience building APIs."
    assert extract_years_experience(text) == 8
    assert extract_years_experience("No tenure listed") is None


def test_extract_seniority_levels():
    assert extract_seniority("Looking for a junior engineer") == "junior"
    assert extract_seniority("Mid-level software engineer") == "mid"
    assert extract_seniority("Senior staff engineer") == "senior"
    assert extract_seniority("Software engineer") is None


def test_extract_qualifications():
    quals = extract_qualifications("BSc Computer Science and AWS certified")
    assert "Bachelor's degree" in quals
    assert "Certification" in quals
    assert extract_qualifications("self taught") == []


def test_extract_evidence_passage_uses_alias_when_canonical_missing():
    text = "Built services on Amazon Web Services with S3 and Lambda."
    passage = extract_evidence_passage(text, "aws")
    assert passage is not None
    assert "Amazon Web Services" in passage
    assert extract_evidence_passage(text, "cobol") is None


def test_parse_cv_and_job_shapes():
    cv = parse_cv_profile("Senior engineer with 6 years of experience. Python, FastAPI. BSc.")
    job = parse_job_requirements("Need senior engineer, 5 years experience, FastAPI and Kubernetes.")
    assert cv["years_experience"] == 6
    assert cv["seniority"] == "senior"
    assert "python" in cv["skills"]
    assert job["years_experience_required"] == 5
    assert "kubernetes" in job["required_skills"]


def test_compare_skills_strong_partial_and_gap():
    result = compare_skills(
        cv_skills=["python", "fastapi", "docker"],
        job_skills=["python", "kubernetes", "fastapi"],
    )
    strong_names = {item["name"] for item in result["strong"]}
    partial_names = {item["name"] for item in result["partial"]}
    gap_names = {item["name"] for item in result["gaps"]}
    assert "python" in strong_names
    assert "fastapi" in strong_names
    assert "kubernetes" in partial_names
    assert result["partial"][0]["related_cv_skill"] == "docker"
    assert gap_names == set()


def test_compare_skills_true_gap_when_unrelated():
    result = compare_skills(cv_skills=["html"], job_skills=["rust"])
    assert result["strong"] == []
    assert result["partial"] == []
    assert result["gaps"][0]["name"] == "rust"
