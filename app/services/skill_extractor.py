from app.utils.skill_dict import load_skill_dict


def normalize_text(text: str) -> str:
    return text.lower()


def extract_skills_from_text(text: str) -> list[str]:
    skill_dict = load_skill_dict()
    normalized_text = normalize_text(text)

    found_skills = set()

    for canonical, variations in skill_dict.items():
        for variation in variations:
            if variation in normalized_text:
                found_skills.add(canonical)
                break

    return sorted(list(found_skills))