"""Database engine and session management with connection pooling."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.logging import get_logger
from ..core.settings import get_settings

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database engine, sessions, and connection pooling."""
    
    def __init__(self) -> None:
        """Initialize database manager."""
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._initialized:
            return
        
        settings = get_settings()
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            future=True,
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        self._initialized = True
        
        logger.info(
            "Database manager initialized",
            url=settings.database.url.split('@')[0] + '@***',  # Hide credentials
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
        )
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
        
        self._initialized = False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup.
        
        Yields:
            Database session
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with explicit transaction management.
        
        Yields:
            Database session with active transaction
        """
        async with self.get_session() as session:
            async with session.begin():
                yield session
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self.engine:
            await self.initialize()
        
        from .models import Base
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self.engine:
            await self.initialize()
        
        from .models import Base
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped")
    
    async def check_connection(self) -> bool:
        """Check if database connection is working.
        
        Returns:
            True if connection is working
        """
        try:
            if not self.engine:
                await self.initialize()
            
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    async def get_pool_status(self) -> dict[str, int]:
        """Get connection pool status.
        
        Returns:
            Pool status information
        """
        if not self.engine:
            return {}
        
        pool = self.engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalidated(),
        }


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for getting database sessions.
    
    This function can be used with FastAPI dependency injection.
    
    Yields:
        Database session
    """
    async with db_manager.get_session() as session:
        yield session


async def init_database() -> None:
    """Initialize database on application startup."""
    await db_manager.initialize()
    
    # Check if tables exist, create if they don't
    try:
        async with db_manager.get_session() as session:
            # Try to query a table to see if schema exists
            from sqlalchemy import text
            await session.execute(text("SELECT COUNT(*) FROM calendar_sources LIMIT 1"))
        
        logger.info("Database schema already exists")
    except Exception:
        # Tables don't exist, create them
        logger.info("Creating database schema")
        await db_manager.create_tables()


async def cleanup_database() -> None:
    """Cleanup database on application shutdown."""
    await db_manager.close()


async def run_database_migrations() -> None:
    """Run database migrations using Alembic."""
    import subprocess
    import sys
    
    try:
        # Run Alembic upgrade
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        logger.info("Database migrations completed successfully")
        if result.stdout:
            logger.debug(f"Migration output: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Database migration failed: {e}")
        if e.stderr:
            logger.error(f"Migration error: {e.stderr}")
        raise


class TransactionManager:
    """Context manager for handling database transactions."""
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize transaction manager.
        
        Args:
            session: Database session
        """
        self.session = session
        self._transaction = None
    
    async def __aenter__(self) -> AsyncSession:
        """Start transaction."""
        self._transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """End transaction."""
        if exc_type is not None:
            await self._transaction.rollback()
        else:
            await self._transaction.commit()


async def with_transaction(session: AsyncSession) -> TransactionManager:
    """Create transaction manager for session.
    
    Args:
        session: Database session
        
    Returns:
        Transaction manager
    """
    return TransactionManager(session)


# Connection pool monitoring
async def monitor_connection_pool() -> None:
    """Monitor connection pool health."""
    while True:
        try:
            status = await db_manager.get_pool_status()
            
            # Log warning if pool utilization is high
            if status.get("checked_out", 0) > status.get("pool_size", 0) * 0.8:
                logger.warning(
                    "High database connection pool utilization",
                    **status,
                )
            
            # Log pool status periodically
            logger.debug("Connection pool status", **status)
            
        except Exception as e:
            logger.error(f"Error monitoring connection pool: {e}")
        
        # Wait 5 minutes before next check
        await asyncio.sleep(300)