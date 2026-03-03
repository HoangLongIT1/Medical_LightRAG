# db.py
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from database.models import Users, ChatThread, ChatMessage, Base as ModelBase

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# Create tables if they don't exist
ModelBase.metadata.create_all(bind=engine)

metadata = MetaData(schema="public")
metadata.reflect(bind=engine)

Base = automap_base(metadata=metadata)
Base.prepare()

# Access ORM classes using automap for backward compatibility
Users = Base.classes.users
ChatThreads = Base.classes.chat_threads
ChatMessages = Base.classes.chat_messages

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
