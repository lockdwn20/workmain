"""
Database connection management using SQLAlchemy
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# How long a write that records an outside action waits on a row lock.
# Such a write is one short insert or update, done in milliseconds. It waits
# only when another transaction holds the row: its own caller, which never
# lets go (DEVELOPMENT_STANDARDS §4.3), or another process, which under §4.1
# holds a written row only for its own database work, well under a second.
RECORD_LOCK_TIMEOUT = '5s'

# Create declarative base for models
Base = declarative_base()

# Database configuration from environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "workmain")
DB_USER = os.getenv("DB_USER", "workmain_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "workmain_dev_pass")

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class DatabaseConnection:
    """Manages database connection and sessions"""
    
    def __init__(self, url=None):
        """
        Initialize database connection
        
        Args:
            url: Database URL (defaults to env config)
        """
        self.url = url or DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Create database engine and session factory"""
        if self.engine is None:
            self.engine = create_engine(
                self.url,
                poolclass=NullPool,  # Disable connection pooling for now
                echo=False  # Set to True for SQL debugging
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self.engine
    
    def get_session(self):
        """Get a new database session"""
        if self.SessionLocal is None:
            self.connect()
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope for database operations
        
        Usage:
            with db.session_scope() as session:
                # Do database work
                session.add(obj)
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def record_scope(self):
        """
        session_scope() for a write that records an outside action
        (docs/DEVELOPMENT_STANDARDS.md §4.3).

        lock_timeout bounds a wait on a row another transaction holds, so a
        record that reaches a row its own caller holds raises instead of
        hanging.
        """
        with self.session_scope() as session:
            session.execute(text(f"SET LOCAL lock_timeout = '{RECORD_LOCK_TIMEOUT}'"))
            yield session

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None


# Global database instance
db = DatabaseConnection()


def get_db():
    """Get database connection instance"""
    return db


def init_db():
    """Initialize database (create tables if needed)"""
    # This will be implemented when we have models
    pass
