from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.link import Link
from app.services.link_service import LinkExpiredError, LinkService


def test_expired_link_is_not_resolved() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        expired_link = Link(
            code="expired-link",
            original_url="https://open.gov.sg/",
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        session.add(expired_link)
        session.commit()

        with pytest.raises(LinkExpiredError):
            LinkService().resolve(session, "expired-link")

    Base.metadata.drop_all(engine)


def test_generated_code_collision_retries_with_a_new_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Link(code="taken-code", original_url="https://open.gov.sg/"))
        session.commit()

        generated_codes = iter(["taken-code", "fresh-code"])
        service = LinkService()
        monkeypatch.setattr(service, "_generate_code", lambda: next(generated_codes))

        link = service.create(session, "https://example.com/")

        assert link.code == "fresh-code"

    Base.metadata.drop_all(engine)
