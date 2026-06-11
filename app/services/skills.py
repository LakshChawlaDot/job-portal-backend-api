from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Skill


def get_or_create_skills(db: Session, names: list[str]) -> list[Skill]:
    normalized = sorted({name.strip().lower() for name in names if name.strip()})
    if not normalized:
        return []

    existing = db.scalars(select(Skill).where(Skill.name.in_(normalized))).all()
    existing_by_name = {skill.name: skill for skill in existing}
    created = []
    for name in normalized:
        if name not in existing_by_name:
            skill = Skill(name=name)
            db.add(skill)
            created.append(skill)
    db.flush()
    return existing + created
