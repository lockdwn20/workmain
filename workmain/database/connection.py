"""
WorkmAIn
Database Connection v0.1.0
20251219

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
    
    def test_connection(self):
        """
        Test database connection
        
        Returns:
            dict: Connection test results
        """
        results = {
            "connected": False,
            "version": None,
            "tables": [],
            "error": None
        }
        
        try:
            engine = self.connect()
            
            # Test basic connection
            with engine.connect() as conn:
                # Get PostgreSQL version
                version_result = conn.execute(text("SELECT version()"))
                results["version"] = version_result.scalar()
                
                # Get table list
                tables_result = conn.execute(text("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname='public'
                    ORDER BY tablename
                """))
                results["tables"] = [row[0] for row in tables_result]
                
                results["connected"] = True
                
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def get_table_count(self, table_name):
        """
        Get row count for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            int: Number of rows
        """
        with self.session_scope() as session:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    
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
