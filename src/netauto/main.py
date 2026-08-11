from sqlalchemy.orm import sessionmaker

from netauto.api.app import create_app
from netauto.persistence.sqlalchemy.database import (
    create_schema,
    create_sqlite_engine,
)
from netauto.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
    SqliteModelWriteUnitOfWork,
)

engine = create_sqlite_engine("sqlite:///netauto.sqlite3")
create_schema(engine)

session_factory = sessionmaker(
    engine,
    expire_on_commit=False,
)

app = create_app(
    lambda: SqlAlchemyUnitOfWork(session_factory),
    model_write_uow_factory=lambda: SqliteModelWriteUnitOfWork(session_factory),
)
