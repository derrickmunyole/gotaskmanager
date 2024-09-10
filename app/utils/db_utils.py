from sqlalchemy.sql import func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime


class UtcNow(func.now):
    def __init__(self):
        super().__init__()


@compiles(UtcNow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@compiles(UtcNow, 'sqlite')
def sqlite_utcnow(element, compiler, **kw):
    return "CURRENT_TIMESTAMP"
