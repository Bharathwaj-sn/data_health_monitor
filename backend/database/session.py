from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker


_session_factory: sessionmaker[Session] | None = None


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


def dispose_session_factory() -> None:
    global _session_factory
    _session_factory = None


def get_database_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()