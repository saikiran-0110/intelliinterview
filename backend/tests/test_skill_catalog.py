from app.services.skill_catalog import (
    chunk_document,
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


def test_extract_skills_does_not_match_short_aliases_inside_words():
    text = "Data analyst who reports on KPIs and extracts insights from spreadsheets using SQL and HTML dashboards."
    skills = extract_skills(text)
    assert "typescript" not in skills
    assert "machine learning" not in skills


def test_extract_skills_javascript_does_not_imply_java():
    text = "Five years of professional JavaScript development, mostly React and Node.js."
    skills = extract_skills(text)
    assert "javascript" in skills
    assert "java" not in skills


def test_extract_skills_matches_next_to_punctuation_not_just_spaces():
    # A previous fix padded aliases like " aws " with a leading/trailing space, which
    # missed real mentions sitting next to other punctuation (parens, semicolons,
    # slashes) with no space on one side - e.g. "(AWS," has "(" immediately before it.
    text = "Experience with cloud platforms (AWS, Azure, GCP) and containerization."
    skills = extract_skills(text)
    assert "aws" in skills

    text2 = "Skills: AWS; Docker; Kubernetes"
    assert "aws" in extract_skills(text2)

    text3 = "Strong Java/Kotlin background."
    assert "java" in extract_skills(text3)


def test_compare_skills_true_gap_when_unrelated():
    result = compare_skills(cv_skills=["html"], job_skills=["rust"])
    assert result["strong"] == []
    assert result["partial"] == []
    assert result["gaps"][0]["name"] == "rust"


def test_extract_skills_detects_ios_and_android_ecosystem_terms():
    # The catalog previously had no iOS/Android framework keywords at all - only the
    # bare "swift"/"kotlin" language names - so a fully iOS-loaded job spec extracted
    # just one required skill and any candidate who merely mentioned Swift scored 100%,
    # regardless of having zero real iOS framework experience.
    job_text = (
        "iOS Software Engineer: strong experience with Swift, UIKit, SwiftUI, Core "
        "Data, and the iOS SDK. Familiarity with Xcode is required."
    )
    skills = extract_skills(job_text)
    assert "ios" in skills
    assert "swift" in skills

    android_text = "Android developer skilled in Kotlin, Jetpack Compose, and the Android SDK."
    android_skills = extract_skills(android_text)
    assert "android" in android_skills
    assert "kotlin" in android_skills


def test_compare_skills_credits_swift_as_partial_match_for_ios_gap():
    # A candidate who only knows the Swift language (no iOS framework experience) should
    # be a partial match for an "ios" requirement, not a full gap and not silently absent.
    result = compare_skills(cv_skills=["swift"], job_skills=["ios", "swift"])
    strong_names = {item["name"] for item in result["strong"]}
    partial_names = {item["name"] for item in result["partial"]}
    assert "swift" in strong_names
    assert "ios" in partial_names
    assert result["gaps"] == []


def test_extract_skills_detects_expanded_data_devops_and_frontend_terms():
    text = (
        "Data engineer skilled in Pandas, NumPy, PySpark, Apache Airflow, and Apache "
        "Kafka for ETL pipelines. Infrastructure managed with Terraform and Ansible, "
        "monitored via Prometheus and Grafana. Frontend built with React and Redux, "
        "styled with SCSS. Databases: SQLite and DynamoDB. Tested with Selenium and "
        "Cypress."
    )
    skills = extract_skills(text)
    for expected in [
        "data engineering",
        "terraform",
        "ansible",
        "monitoring",
        "react",
        "state management",
        "css",
        "sqlite",
        "dynamodb",
        "testing",
        "message queues",
    ]:
        assert expected in skills, f"expected {expected!r} in {skills}"


def test_extract_skills_avoids_common_word_false_positives_for_new_aliases():
    # "sass" (a common English word, "don't give me any sass") was deliberately left out
    # of the CSS catalog entry to avoid this; "spark" was deliberately never added bare.
    text = "The manager did not tolerate any sass, but the new hire will spark real change."
    skills = extract_skills(text)
    assert "css" not in skills
    assert "data engineering" not in skills


def test_extract_skills_mobile_frameworks():
    text = "Flutter developer experienced with React Native and cross-platform apps."
    skills = extract_skills(text)
    assert "flutter" in skills
    assert "react" in skills


def test_chunk_document_groups_sentences_with_expected_overlap():
    # 20 five-word sentences; target=20 words (4 sentences/chunk), overlap=10 words
    # (2 sentences) - both counts are exact multiples so the result is predictable.
    sentences = [f"Sentence number {i} has words." for i in range(20)]
    text = " ".join(sentences)

    chunks = chunk_document(text, target_words=20, overlap_words=10)

    assert len(chunks) == 9
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    assert len(first_words) == 20
    # The last 10 words of chunk 0 should be the first 10 words of chunk 1 (the overlap).
    assert first_words[-10:] == second_words[:10]


def test_chunk_document_caps_chunk_size_near_target():
    sentences = [f"This sentence number {i} describes some work done on a notable project." for i in range(40)]
    text = " ".join(sentences)

    chunks = chunk_document(text, target_words=50, overlap_words=10)

    for chunk in chunks:
        assert len(chunk.split()) <= 50 * 1.5


def test_chunk_document_short_text_yields_one_chunk():
    text = "Built a small internal tool used by the whole engineering team daily."
    chunks = chunk_document(text)
    assert len(chunks) == 1


def test_chunk_document_empty_text_yields_no_chunks():
    assert chunk_document("") == []
    assert chunk_document("   \n  ") == []


def test_chunk_document_drops_short_trailing_fragment():
    text = "This is a reasonably long first sentence with plenty of words in it. Short one."
    chunks = chunk_document(text, target_words=100, overlap_words=10)
    assert all(len(chunk.split()) >= 8 for chunk in chunks)


def test_chunk_document_treats_bullet_lines_as_sentence_boundaries():
    text = (
        "Built APIs with FastAPI and PostgreSQL for the platform team\n"
        "Led migration to Kubernetes across all production services company wide"
    )
    chunks = chunk_document(text, target_words=20, overlap_words=2)
    assert len(chunks) >= 1
    assert any("kubernetes" in chunk.lower() for chunk in chunks)


def test_chunk_document_caps_total_chunks_at_sixty():
    sentences = [f"Line {i} describes a unique short responsibility handled by the candidate." for i in range(500)]
    text = " ".join(sentences)
    chunks = chunk_document(text, target_words=20, overlap_words=5)
    assert len(chunks) <= 60
