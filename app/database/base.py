from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class untuk semua model ORM SQLAlchemy.
    Semua model harus mewarisi class ini.
    """
    pass
