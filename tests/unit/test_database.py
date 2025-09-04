"""
Unit tests for backend.database

Tests database configuration and session management including:
- Database engine configuration
- Session factory creation
- Database session lifecycle
- Connection parameters and settings
- Error handling and cleanup

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import DATABASE_URL, engine, SessionLocal, get_db


class TestDatabaseConfiguration:
    """Test database configuration and setup."""

    def test_database_url_configuration(self):
        """Test that DATABASE_URL is properly configured."""
        assert DATABASE_URL == "sqlite:///steve-mom-archive.db"
        assert isinstance(DATABASE_URL, str)
        assert DATABASE_URL.startswith("sqlite:///")

    def test_engine_configuration(self):
        """Test that database engine is properly configured."""
        assert engine is not None
        assert str(engine.url) == DATABASE_URL

        # Check that engine is configured for SQLite
        assert engine.name == "sqlite"
        assert engine.driver == "pysqlite"

    def test_session_local_configuration(self):
        """Test SessionLocal factory configuration."""
        assert SessionLocal is not None

        # Test that SessionLocal creates Session instances
        session = SessionLocal()
        assert isinstance(session, Session)
        session.close()

    def test_session_local_parameters(self):
        """Test SessionLocal factory parameters."""
        # Create a session to test configuration
        session = SessionLocal()

        try:
            # Test autoflush settings (autocommit is not available in SQLAlchemy 2.0)
            assert session.autoflush is False
            assert session.bind == engine
        finally:
            session.close()


class TestGetDbFunction:
    """Test get_db function for dependency injection."""

    def test_get_db_returns_generator(self):
        """Test that get_db returns a generator."""
        db_generator = get_db()
        assert hasattr(db_generator, '__next__')
        assert hasattr(db_generator, '__iter__')

    def test_get_db_yields_session(self):
        """Test that get_db yields a database session."""
        db_generator = get_db()

        try:
            session = next(db_generator)
            assert isinstance(session, Session)
            assert session.bind == engine
        except StopIteration:
            pytest.fail("get_db should yield a session")
        finally:
            # Clean up the generator
            try:
                next(db_generator)
            except StopIteration:
                pass  # Expected when generator finishes

    def test_get_db_session_cleanup(self):
        """Test that get_db properly closes sessions."""
        db_generator = get_db()

        # Get the session
        session = next(db_generator)
        session_id = id(session)

        # Mock the session close method to verify it's called
        with patch.object(session, 'close') as mock_close:
            # Trigger cleanup by exhausting the generator
            try:
                next(db_generator)
            except StopIteration:
                pass  # Expected

            # Verify close was called
            mock_close.assert_called_once()

    def test_get_db_multiple_calls(self):
        """Test that multiple calls to get_db return different sessions."""
        db_gen1 = get_db()
        db_gen2 = get_db()

        session1 = next(db_gen1)
        session2 = next(db_gen2)

        # Should be different session instances
        assert session1 is not session2
        assert id(session1) != id(session2)

        # Clean up
        for gen in [db_gen1, db_gen2]:
            try:
                next(gen)
            except StopIteration:
                pass

    def test_get_db_exception_handling(self):
        """Test that get_db handles exceptions properly."""
        db_generator = get_db()
        session = next(db_generator)

        # Mock session.close to verify it's called even if an exception occurs
        with patch.object(session, 'close') as mock_close:
            # Simulate an exception during session usage
            with pytest.raises(Exception):
                # Force an exception in the generator
                db_generator.throw(Exception("Test exception"))

            # Verify close was still called
            mock_close.assert_called_once()


class TestDatabaseIntegration:
    """Test database integration and basic operations."""

    def test_database_connection(self):
        """Test basic database connection."""
        # Test that we can create a connection
        connection = engine.connect()
        assert connection is not None

        # Test basic query execution
        result = connection.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row[0] == 1

        connection.close()

    def test_session_creation_and_basic_operations(self):
        """Test session creation and basic operations."""
        session = SessionLocal()

        try:
            # Test that session is properly configured
            assert session.bind == engine
            assert not session.dirty  # No pending changes
            assert not session.new    # No new objects

            # Test basic query execution through session
            result = session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            assert row[0] == 1

        finally:
            session.close()

    def test_session_transaction_behavior(self):
        """Test session transaction behavior."""
        session = SessionLocal()

        try:
            # Test that we can start a transaction
            session.begin()
            assert session.in_transaction()

            # Test rollback
            session.rollback()

        finally:
            session.close()

    def test_multiple_sessions_isolation(self):
        """Test that multiple sessions are properly isolated."""
        session1 = SessionLocal()
        session2 = SessionLocal()

        try:
            # Sessions should be different instances
            assert session1 is not session2

            # Both should be connected to the same engine
            assert session1.bind == engine
            assert session2.bind == engine

            # Both should have the same configuration
            assert session1.autoflush == session2.autoflush

        finally:
            session1.close()
            session2.close()


class TestErrorHandling:
    """Test error handling in database operations."""

    def test_invalid_database_url_handling(self):
        """Test handling of invalid database URLs."""
        # Test that invalid URL raises appropriate error
        with pytest.raises(Exception):
            invalid_engine = create_engine("invalid://url")
            invalid_engine.connect()

    def test_session_error_handling(self):
        """Test session error handling."""
        session = SessionLocal()

        try:
            # Test that invalid SQL raises appropriate error
            with pytest.raises(Exception):
                session.execute("INVALID SQL STATEMENT")

        finally:
            session.close()

    def test_get_db_with_session_error(self):
        """Test get_db behavior when session operations fail."""
        db_generator = get_db()
        session = next(db_generator)

        # Mock session to raise an error
        with patch.object(session, 'execute', side_effect=Exception("DB Error")):
            with patch.object(session, 'close') as mock_close:
                # Even if session operations fail, close should still be called
                try:
                    next(db_generator)
                except StopIteration:
                    pass

                mock_close.assert_called_once()


class TestDatabaseConstants:
    """Test database-related constants and configurations."""

    def test_database_url_format(self):
        """Test DATABASE_URL format and structure."""
        assert DATABASE_URL.startswith("sqlite:///")
        assert "steve-mom-archive.db" in DATABASE_URL

        # Should be a relative path (no leading slash after sqlite:///)
        db_path = DATABASE_URL.replace("sqlite:///", "")
        assert not db_path.startswith("/")

    def test_engine_properties(self):
        """Test engine properties and configuration."""
        assert engine.name == "sqlite"
        assert engine.driver == "pysqlite"

        # Test that engine is properly configured for SQLite
        assert hasattr(engine, 'pool')
        assert hasattr(engine, 'dialect')

    def test_session_factory_properties(self):
        """Test SessionLocal factory properties."""
        # Test that SessionLocal is a sessionmaker instance
        from sqlalchemy.orm import sessionmaker
        assert isinstance(SessionLocal, sessionmaker)

        # Test configuration
        assert SessionLocal.kw['autocommit'] is False
        assert SessionLocal.kw['autoflush'] is False
        assert SessionLocal.kw['bind'] == engine