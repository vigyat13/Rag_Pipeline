# app/db/base.py

from app.core.db import Base

# Import all models so SQLAlchemy registers them
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.models.analytics import QueryEvent, QueryDocument
