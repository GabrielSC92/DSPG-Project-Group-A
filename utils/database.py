"""
Database utilities for the Quality of Dutch Government application.
Handles database connections and operations for Auth and Quant tables.
"""

import os
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import database libraries
try:
    import sqlalchemy
    from sqlalchemy import create_engine, text, Column, String, Integer, Numeric, Date, Text, ForeignKey, CheckConstraint, DateTime
    from sqlalchemy.sql import func
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


# Database configuration
# Priority: DATABASE_URL env var > PostgreSQL config > SQLite fallback
def get_database_url() -> str:
    """
    Get the database URL from environment or use defaults.
    
    Environment variables:
    - DATABASE_URL: Full connection string (takes priority)
    - DB_TYPE: 'postgresql' or 'sqlite' (default: sqlite)
    - DB_HOST: Database host (default: localhost)
    - DB_PORT: Database port (default: 5432 for postgres)
    - DB_NAME: Database name (default: qog_dev)
    - DB_USER: Database user (default: postgres)
    - DB_PASSWORD: Database password
    """
    # Check for full DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    db_type = os.getenv("DB_TYPE", "sqlite").lower()

    if db_type == "postgresql" or db_type == "postgres":
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "qog_dev")
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")

        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            return f"postgresql://{user}@{host}:{port}/{name}"

    else:
        # SQLite fallback - creates a local file
        db_path = os.getenv("DB_PATH", "data/qog_local.db")
        # Ensure directory exists
        os.makedirs(
            os.path.dirname(db_path) if os.path.dirname(db_path) else ".",
            exist_ok=True)
        return f"sqlite:///{db_path}"


# SQLAlchemy setup
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class AuthUser(Base):
        """Auth table model matching the provided schema."""
        __tablename__ = 'auth'
        __table_args__ = (CheckConstraint("access_level IN ('U', 'R')",
                                          name='check_access_level'), )

        user_id = Column(String(10), primary_key=True)
        access_level = Column(
            String(1), nullable=False)  # 'U' for End-User, 'R' for Researcher
        email = Column(String(40), unique=True, nullable=False)
        password_hash = Column(String(128), nullable=False)  # SHA256 hash
        created_date = Column(Date, nullable=False)
        interaction_count = Column(Integer, default=0, nullable=False)
        satisfaction_baseline = Column(Numeric(
            3, 1))  # Can be NULL until first rating

    class QuantInteraction(Base):
        """Quant table model matching the provided schema."""
        __tablename__ = 'quant'
        __table_args__ = (
            CheckConstraint("verification_flag IN ('V', 'U')",
                            name='check_verification_flag'),
            CheckConstraint("satisfaction_raw >= 1 AND satisfaction_raw <= 5",
                            name='check_satisfaction_range'),
        )

        interaction_id = Column(String(12), primary_key=True)
        user_id = Column(String(10),
                         ForeignKey('auth.user_id'),
                         nullable=False)
        topic_id = Column(Integer,
                          ForeignKey('topics.id'),
                          nullable=True)  # Links to topics table for normalization
        correlation_index = Column(Numeric(5, 3))  # Can be NULL, set by RAG
        verification_flag = Column(
            String(1), nullable=False,
            default='U')  # 'V' for verified, 'U' for unverified
        satisfaction_raw = Column(Numeric(3, 1), nullable=False)
        interaction_date = Column(Date, nullable=False)
        summary = Column(Text)  # Can be NULL if no summary

    class RagDocument(Base):
        """
        Stores one row per ingested document (PDF).
        """
        __tablename__ = "rag_documents"

        id = Column(Integer, primary_key=True, autoincrement=True)

        # Stable key so re-ingestion updates the same doc
        # Example: "defensie/Brief+Defensie+PAC24.pdf"
        doc_key = Column(String(255), unique=True, nullable=False)

        # Folder/category name derived from the folder the PDF is in
        source_folder = Column(String(80), nullable=False)

        file_name = Column(String(255), nullable=False)
        file_path = Column(String(500), nullable=True)
        
        # Document-level summary generated by LLM during ingestion
        summary = Column(Text, nullable=True)

        created_at = Column(DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False)

    class RagChunk(Base):
        """
        Stores chunked text for RAG retrieval. One document has many chunks.
        Each chunk is linked to a sub-topic for efficient filtering.
        """
        __tablename__ = "rag_chunks"

        id = Column(Integer, primary_key=True, autoincrement=True)

        document_id = Column(Integer,
                             ForeignKey("rag_documents.id"),
                             nullable=False)
        
        # Link to sub-topic for efficient filtering (nullable for backward compatibility)
        subtopic_id = Column(Integer, ForeignKey("subtopics.id"), nullable=True)
        
        chunk_index = Column(Integer, nullable=False)

        page_start = Column(Integer, nullable=True)
        page_end = Column(Integer, nullable=True)

        chunk_text = Column(Text, nullable=False)

        created_at = Column(DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False)

    class Topic(Base):
        """
        Stores available topics generated from ingested documents.
        Topics are derived from source folders and translated to English labels.
        """
        __tablename__ = "topics"

        id = Column(Integer, primary_key=True, autoincrement=True)
        
        # Original source folder name (e.g., "defensie")
        source_folder = Column(String(80), unique=True, nullable=False)
        
        # English label for the topic (e.g., "Defence")
        label_en = Column(String(100), nullable=False)
        
        # Number of documents associated with this topic
        document_count = Column(Integer, default=0, nullable=False)
        
        created_at = Column(DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False)
        updated_at = Column(DateTime(timezone=True),
                            server_default=func.now(),
                            onupdate=func.now(),
                            nullable=False)

    class SubTopic(Base):
        """
        Stores sub-topics within a topic. Each chunk is linked to a sub-topic.
        Sub-topics are generated from chunk content during ingestion.
        
        Example: Topic "Defence" -> SubTopics: "Submarine Procurement", "Military Budget", etc.
        """
        __tablename__ = "subtopics"

        id = Column(Integer, primary_key=True, autoincrement=True)
        
        # Foreign key to parent topic
        topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
        
        # English label for the sub-topic (e.g., "Submarine Procurement")
        label_en = Column(String(150), nullable=False)
        
        # Number of chunks associated with this sub-topic
        chunk_count = Column(Integer, default=0, nullable=False)
        
        created_at = Column(DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False)

    class Feedback(Base):
        """
        Stores user feedback submitted through the feedback modal.
        """
        __tablename__ = "feedback"

        id = Column(Integer, primary_key=True, autoincrement=True)
        
        # User info (can be "anonymous" if user opts out)
        user_id = Column(String(10), nullable=True)
        user_email = Column(String(40), nullable=True)
        
        # Feedback details
        feedback_type = Column(String(30), nullable=False)  # General Feedback, Bug Report, etc.
        message = Column(Text, nullable=False)
        
        created_at = Column(DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False)


_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine (singleton)."""
    global _engine
    if not SQLALCHEMY_AVAILABLE:
        return None

    if _engine is None:
        try:
            database_url = get_database_url()
            _engine = create_engine(database_url, echo=False)
            print(
                f"DATABASE: Connected to {database_url.split('@')[-1] if '@' in database_url else database_url}"
            )
        except Exception as e:
            print(f"DATABASE: Failed to create engine: {e}")
            return None
    return _engine


def get_session():
    """Get a new database session."""
    global _SessionLocal

    engine = get_engine()
    if engine is None:
        return None

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine)

    return _SessionLocal()


def init_database() -> Tuple[bool, str]:
    """
    Initialize the database tables if they don't exist.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not SQLALCHEMY_AVAILABLE:
        return False, "SQLAlchemy not installed. Run: pip install sqlalchemy"

    engine = get_engine()
    if engine is None:
        return False, "Failed to connect to database"

    try:
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        return True, "Database initialized successfully"
    except Exception as e:
        return False, f"Failed to initialize database: {e}"


def is_database_connected() -> bool:
    """Check if database connection is working."""
    if not SQLALCHEMY_AVAILABLE:
        return False

    engine = get_engine()
    if engine is None:
        return False

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# ============== AUTH TABLE OPERATIONS ==============

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with automatic salt generation.
    This is much more secure than SHA-256 as it:
    - Includes automatic salt generation
    - Is computationally expensive (prevents brute force)
    - Is designed specifically for password hashing
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    Handles both new bcrypt hashes and legacy SHA-256 hashes for backwards compatibility.
    """
    try:
        # Try bcrypt verification first (new format)
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except (ValueError, AttributeError):
        # Fallback for legacy SHA-256 hashes (for existing users)
        # This should be removed after all passwords are migrated
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == password_hash


def get_user_by_email(email: str,
                      include_hash: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a user by email address.
    
    Args:
        email: User's email address
        include_hash: Whether to include password_hash in result
        
    Returns:
        User data dict or None if not found
    """
    session = get_session()
    if session is None:
        return None

    try:
        user = session.query(AuthUser).filter(
            AuthUser.email == email.lower()).first()
        if user:
            result = {
                'user_id':
                user.user_id,
                'access_level':
                user.access_level,
                'email':
                user.email,
                'created_date':
                user.created_date,
                'interaction_count':
                user.interaction_count or 0,
                'satisfaction_baseline':
                float(user.satisfaction_baseline)
                if user.satisfaction_baseline else None
            }
            if include_hash:
                result['password_hash'] = user.password_hash
            return result
        return None
    except Exception as e:
        print(f"DATABASE: Error getting user: {e}")
        return None
    finally:
        session.close()


def authenticate_user_db(
        email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Authenticate a user against the database.
    
    Args:
        email: User's email address
        password: User's plain text password
        
    Returns:
        Tuple of (success: bool, user_data: dict or None)
    """
    user = get_user_by_email(email, include_hash=True)

    if user is None:
        return False, None

    password_hash = user.pop('password_hash', None)

    if password_hash is None:
        return False, None

    if verify_password(password, password_hash):
        return True, user

    return False, None


def check_email_exists(email: str) -> bool:
    """Check if an email already exists in the database."""
    session = get_session()
    if session is None:
        return False

    try:
        exists = session.query(AuthUser).filter(
            AuthUser.email == email.lower().strip()).first() is not None
        return exists
    except Exception:
        return False
    finally:
        session.close()


def create_user(user_id: str,
                email: str,
                access_level: str = 'U',
                password: Optional[str] = None) -> Tuple[bool, str]:
    """
    Create a new user in the Auth table.
    
    Args:
        user_id: Unique user ID (max 10 chars)
        email: User's email address
        access_level: 'U' for End-User, 'R' for Researcher
        password: Plain text password (will be hashed)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    session = get_session()
    if session is None:
        return False, "Database not connected"

    # Sanitize inputs
    email_clean = email.lower().strip()[:40]
    access_clean = access_level[0].upper() if access_level else 'U'

    # Validate access_level
    if access_clean not in ('U', 'R'):
        return False, "Invalid access level. Must be 'U' (User) or 'R' (Researcher)"

    try:
        # Hash the password if provided
        pwd_hash = hash_password(password) if password else hash_password(
            "changeme")

        new_user = AuthUser(user_id=user_id[:10],
                            email=email_clean,
                            password_hash=pwd_hash,
                            access_level=access_clean,
                            created_date=date.today(),
                            interaction_count=0,
                            satisfaction_baseline=None)
        session.add(new_user)
        session.commit()
        return True, f"User {user_id} created successfully"
    except IntegrityError as e:
        session.rollback()
        error_str = str(e).lower()
        if 'unique' in error_str or 'email' in error_str or 'duplicate' in error_str:
            return False, "An account with this email already exists"
        elif 'user_id' in error_str or 'primary' in error_str:
            return False, "A user with this ID already exists"
        elif 'check_access_level' in error_str:
            return False, "Invalid access level. Must be 'U' or 'R'"
        else:
            return False, "Database constraint violation"
    except Exception as e:
        session.rollback()
        return False, f"Failed to create user: {e}"
    finally:
        session.close()


def update_user_interaction_count(user_id: str) -> bool:
    """Increment the user's interaction count."""
    session = get_session()
    if session is None:
        return False

    try:
        user = session.query(AuthUser).filter(
            AuthUser.user_id == user_id).first()
        if user:
            user.interaction_count = (user.interaction_count or 0) + 1
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"DATABASE: Error updating interaction count: {e}")
        return False
    finally:
        session.close()


def update_user_satisfaction_baseline(user_id: str, baseline: float) -> bool:
    """Update the user's satisfaction baseline."""
    session = get_session()
    if session is None:
        return False

    try:
        user = session.query(AuthUser).filter(
            AuthUser.user_id == user_id).first()
        if user:
            user.satisfaction_baseline = baseline
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"DATABASE: Error updating satisfaction baseline: {e}")
        return False
    finally:
        session.close()


# ============== QUANT TABLE OPERATIONS ==============


def generate_interaction_id() -> str:
    """Generate a unique interaction ID."""
    import uuid
    return f"INT_{uuid.uuid4().hex[:8].upper()}"


def save_interaction(
        user_id: str,
        satisfaction_raw: float,
        summary: str,
        topic_id: Optional[int] = None,
        correlation_index: Optional[float] = None,
        verification_flag: str = 'U') -> Tuple[bool, str]:
    """
    Save a new interaction to the Quant table.
    
    Args:
        user_id: The user's ID
        satisfaction_raw: Raw satisfaction score (1-5 Likert scale)
        summary: Topic summary from the interaction
        topic_id: ID of the topic (from topics table) for normalization
        correlation_index: Similarity/correlation score (optional, set by RAG)
        verification_flag: 'V' for verified, 'U' for unverified
        
    Returns:
        Tuple of (success: bool, interaction_id or error message)
    """
    session = get_session()
    if session is None:
        return False, "Database not connected"

    try:
        interaction_id = generate_interaction_id()

        new_interaction = QuantInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            topic_id=topic_id,
            correlation_index=correlation_index,
            verification_flag=verification_flag[0].upper(),
            satisfaction_raw=satisfaction_raw,
            interaction_date=date.today(),
            summary=summary[:5000] if summary else None  # Limit summary length
        )
        session.add(new_interaction)
        session.commit()

        # Also update user's interaction count
        update_user_interaction_count(user_id)

        return True, interaction_id
    except Exception as e:
        session.rollback()
        return False, f"Failed to save interaction: {e}"
    finally:
        session.close()


def get_all_interactions(user_id: Optional[str] = None,
                         start_date: Optional[date] = None,
                         end_date: Optional[date] = None,
                         limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Get interactions from the Quant table with optional filters.
    Joins with topics table to get topic labels.
    
    Args:
        user_id: Filter by user ID (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum number of records to return
        
    Returns:
        List of interaction dicts with topic info
    """
    session = get_session()
    if session is None:
        return []

    try:
        # Join with topics table to get topic label
        query = session.query(
            QuantInteraction,
            Topic.label_en.label('topic_label')
        ).outerjoin(Topic, QuantInteraction.topic_id == Topic.id)

        if user_id:
            query = query.filter(QuantInteraction.user_id == user_id)
        if start_date:
            query = query.filter(
                QuantInteraction.interaction_date >= start_date)
        if end_date:
            query = query.filter(QuantInteraction.interaction_date <= end_date)

        query = query.order_by(
            QuantInteraction.interaction_date.desc()).limit(limit)

        results = []
        for interaction, topic_label in query.all():
            results.append({
                'interaction_id': interaction.interaction_id,
                'user_id': interaction.user_id,
                'topic_id': interaction.topic_id,
                'topic': topic_label or 'General',  # Fallback if no topic set
                'correlation_index': float(interaction.correlation_index) if interaction.correlation_index else None,
                'verification_flag': interaction.verification_flag,
                'satisfaction_raw': float(interaction.satisfaction_raw) if interaction.satisfaction_raw else None,
                'interaction_date': interaction.interaction_date,
                'summary': interaction.summary
            })

        return results
    except Exception as e:
        print(f"DATABASE: Error getting interactions: {e}")
        return []
    finally:
        session.close()


def get_interaction_stats() -> Dict[str, Any]:
    """Get aggregate statistics from the Quant table."""
    session = get_session()
    if session is None:
        return {}

    try:
        from sqlalchemy import func

        stats = session.query(
            func.count(
                QuantInteraction.interaction_id).label('total_interactions'),
            func.avg(
                QuantInteraction.satisfaction_raw).label('avg_satisfaction'),
            func.count(func.distinct(
                QuantInteraction.user_id)).label('unique_users'),
            func.sum(
                sqlalchemy.case((QuantInteraction.verification_flag == 'V', 1),
                                else_=0)).label('verified_count')).first()

        return {
            'total_interactions':
            stats.total_interactions or 0,
            'avg_satisfaction':
            round(float(stats.avg_satisfaction), 2)
            if stats.avg_satisfaction else 0,
            'unique_users':
            stats.unique_users or 0,
            'verified_count':
            stats.verified_count or 0
        }
    except Exception as e:
        print(f"DATABASE: Error getting stats: {e}")
        return {}
    finally:
        session.close()


# ============== TOPIC TABLE OPERATIONS ==============


def get_available_topics() -> List[Dict[str, Any]]:
    """
    Get all available topics from the database.
    
    Returns:
        List of topic dicts with 'source_folder', 'label_en', and 'document_count'
    """
    session = get_session()
    if session is None:
        return []

    try:
        topics = session.query(Topic).order_by(Topic.label_en).all()
        return [
            {
                'id': t.id,
                'source_folder': t.source_folder,
                'label_en': t.label_en,
                'document_count': t.document_count
            }
            for t in topics
        ]
    except Exception as e:
        print(f"DATABASE: Error getting topics: {e}")
        return []
    finally:
        session.close()


def upsert_topic(source_folder: str, label_en: str, document_count: int = 0) -> Tuple[bool, str]:
    """
    Create or update a topic in the database.
    
    Args:
        source_folder: Original folder name (e.g., "defensie")
        label_en: English label (e.g., "Defence")
        document_count: Number of documents for this topic
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    session = get_session()
    if session is None:
        return False, "Database not connected"

    try:
        topic = session.query(Topic).filter(
            Topic.source_folder == source_folder.lower()
        ).one_or_none()
        
        if topic is None:
            topic = Topic(
                source_folder=source_folder.lower(),
                label_en=label_en,
                document_count=document_count
            )
            session.add(topic)
        else:
            topic.label_en = label_en
            topic.document_count = document_count
        
        session.commit()
        return True, f"Topic '{label_en}' saved"
    except Exception as e:
        session.rollback()
        return False, f"Failed to save topic: {e}"
    finally:
        session.close()


def update_topic_counts() -> Tuple[bool, str]:
    """
    Update document counts for all topics based on rag_documents table.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    session = get_session()
    if session is None:
        return False, "Database not connected"

    try:
        # Get counts per source_folder from rag_documents
        from sqlalchemy import func
        counts = session.query(
            RagDocument.source_folder,
            func.count(RagDocument.id).label('count')
        ).group_by(RagDocument.source_folder).all()
        
        for source_folder, count in counts:
            topic = session.query(Topic).filter(
                Topic.source_folder == source_folder.lower()
            ).one_or_none()
            
            if topic:
                topic.document_count = count
        
        session.commit()
        return True, f"Updated counts for {len(counts)} topics"
    except Exception as e:
        session.rollback()
        return False, f"Failed to update topic counts: {e}"
    finally:
        session.close()


def get_topic_label_by_folder(source_folder: str) -> Optional[str]:
    """
    Get the English label for a topic by its source folder name.
    
    Args:
        source_folder: Original folder name (e.g., "defensie")
        
    Returns:
        English label or None if not found
    """
    session = get_session()
    if session is None:
        return None

    try:
        topic = session.query(Topic).filter(
            Topic.source_folder == source_folder.lower()
        ).one_or_none()
        
        return topic.label_en if topic else None
    except Exception as e:
        print(f"DATABASE: Error getting topic label: {e}")
        return None
    finally:
        session.close()


def get_topic_id_by_folder(source_folder: str) -> Optional[int]:
    """
    Get the topic ID by its source folder name.
    
    Args:
        source_folder: Original folder name (e.g., "defensie")
        
    Returns:
        Topic ID or None if not found
    """
    session = get_session()
    if session is None:
        return None

    try:
        topic = session.query(Topic).filter(
            Topic.source_folder == source_folder.lower()
        ).one_or_none()
        
        return topic.id if topic else None
    except Exception as e:
        print(f"DATABASE: Error getting topic ID: {e}")
        return None
    finally:
        session.close()


def get_topic_id_by_label(label_en: str) -> Optional[int]:
    """
    Get the topic ID by its English label.
    
    Args:
        label_en: English label (e.g., "Defence")
        
    Returns:
        Topic ID or None if not found
    """
    session = get_session()
    if session is None:
        return None

    try:
        topic = session.query(Topic).filter(
            Topic.label_en == label_en
        ).one_or_none()
        
        return topic.id if topic else None
    except Exception as e:
        print(f"DATABASE: Error getting topic ID by label: {e}")
        return None
    finally:
        session.close()


# ============== SUBTOPIC TABLE OPERATIONS ==============


def get_or_create_subtopic(session, topic_id: int, label_en: str) -> int:
    """
    Get existing subtopic or create a new one.
    
    Args:
        session: Database session (must be passed for transaction consistency)
        topic_id: Parent topic ID
        label_en: English label for the sub-topic
        
    Returns:
        SubTopic ID
    """
    # Normalize the label
    label_normalized = label_en.strip().title()[:150]
    
    subtopic = session.query(SubTopic).filter(
        SubTopic.topic_id == topic_id,
        SubTopic.label_en == label_normalized
    ).one_or_none()
    
    if subtopic is None:
        subtopic = SubTopic(
            topic_id=topic_id,
            label_en=label_normalized,
            chunk_count=0
        )
        session.add(subtopic)
        session.flush()  # Get the ID
    
    return subtopic.id


def get_subtopics_by_topic(topic_id: int) -> List[Dict[str, Any]]:
    """
    Get all sub-topics for a given topic.
    
    Args:
        topic_id: Parent topic ID
        
    Returns:
        List of subtopic dicts
    """
    session = get_session()
    if session is None:
        return []

    try:
        subtopics = session.query(SubTopic).filter(
            SubTopic.topic_id == topic_id
        ).order_by(SubTopic.label_en).all()
        
        return [
            {
                'id': st.id,
                'topic_id': st.topic_id,
                'label_en': st.label_en,
                'chunk_count': st.chunk_count
            }
            for st in subtopics
        ]
    except Exception as e:
        print(f"DATABASE: Error getting subtopics: {e}")
        return []
    finally:
        session.close()


def get_subtopics_by_topic_label(topic_label: str) -> List[Dict[str, Any]]:
    """
    Get all sub-topics for a given topic label (English).
    
    Args:
        topic_label: English topic label (e.g., "Defence")
        
    Returns:
        List of subtopic dicts with label and chunk count
    """
    session = get_session()
    if session is None:
        return []

    try:
        # Find topic by label
        topic = session.query(Topic).filter(
            Topic.label_en == topic_label
        ).one_or_none()
        
        if not topic:
            return []
        
        subtopics = session.query(SubTopic).filter(
            SubTopic.topic_id == topic.id
        ).order_by(SubTopic.chunk_count.desc()).all()
        
        return [
            {
                'id': st.id,
                'label_en': st.label_en,
                'chunk_count': st.chunk_count
            }
            for st in subtopics
        ]
    except Exception as e:
        print(f"DATABASE: Error getting subtopics by label: {e}")
        return []
    finally:
        session.close()


def get_all_subtopics_with_topics() -> List[Dict[str, Any]]:
    """
    Get all sub-topics with their parent topic information.
    Used by the Agent for efficient filtering.
    
    Returns:
        List of dicts with topic and subtopic info
    """
    session = get_session()
    if session is None:
        return []

    try:
        results = session.query(
            SubTopic.id,
            SubTopic.label_en.label('subtopic'),
            SubTopic.chunk_count,
            Topic.label_en.label('topic'),
            Topic.source_folder
        ).join(Topic, SubTopic.topic_id == Topic.id).order_by(
            Topic.label_en, SubTopic.label_en
        ).all()
        
        return [
            {
                'subtopic_id': r.id,
                'subtopic': r.subtopic,
                'chunk_count': r.chunk_count,
                'topic': r.topic,
                'source_folder': r.source_folder
            }
            for r in results
        ]
    except Exception as e:
        print(f"DATABASE: Error getting all subtopics: {e}")
        return []
    finally:
        session.close()


def update_subtopic_counts() -> Tuple[bool, str]:
    """
    Update chunk counts for all subtopics based on rag_chunks table.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    session = get_session()
    if session is None:
        return False, "Database not connected"

    try:
        from sqlalchemy import func
        
        # Get counts per subtopic from rag_chunks
        counts = session.query(
            RagChunk.subtopic_id,
            func.count(RagChunk.id).label('count')
        ).filter(
            RagChunk.subtopic_id.isnot(None)
        ).group_by(RagChunk.subtopic_id).all()
        
        for subtopic_id, count in counts:
            subtopic = session.query(SubTopic).filter(
                SubTopic.id == subtopic_id
            ).one_or_none()
            
            if subtopic:
                subtopic.chunk_count = count
        
        session.commit()
        return True, f"Updated counts for {len(counts)} subtopics"
    except Exception as e:
        session.rollback()
        return False, f"Failed to update subtopic counts: {e}"
    finally:
        session.close()


def update_chunk_subtopic(session, chunk_id: int, subtopic_id: int) -> bool:
    """
    Update the subtopic_id for a chunk.
    
    Args:
        session: Database session
        chunk_id: Chunk ID
        subtopic_id: SubTopic ID
        
    Returns:
        True if successful
    """
    try:
        chunk = session.query(RagChunk).filter(RagChunk.id == chunk_id).one_or_none()
        if chunk:
            chunk.subtopic_id = subtopic_id
            return True
        return False
    except Exception as e:
        print(f"DATABASE: Error updating chunk subtopic: {e}")
        return False


# ============== FEEDBACK TABLE OPERATIONS ==============


def save_feedback(
        feedback_type: str,
        message: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None) -> Tuple[bool, str]:
    """
    Save user feedback to the database.
    
    Args:
        feedback_type: Type of feedback (General Feedback, Bug Report, etc.)
        message: The feedback message content
        user_id: User ID or None/anonymous
        user_email: User email or None/anonymous
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    session = get_session()
    if session is None:
        return False, "Database not connected"

    try:
        # Handle anonymous values
        uid = user_id if user_id and user_id != "anonymous" else None
        email = user_email if user_email and user_email != "anonymous" else None
        
        new_feedback = Feedback(
            user_id=uid,
            user_email=email,
            feedback_type=feedback_type[:30],
            message=message[:5000]  # Limit message length
        )
        session.add(new_feedback)
        session.commit()
        return True, "Feedback saved successfully"
    except Exception as e:
        session.rollback()
        return False, f"Failed to save feedback: {e}"
    finally:
        session.close()


def get_all_feedback(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all feedback entries from the database.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        List of feedback dicts
    """
    session = get_session()
    if session is None:
        return []

    try:
        feedbacks = session.query(Feedback).order_by(
            Feedback.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                'id': f.id,
                'user_id': f.user_id,
                'user_email': f.user_email,
                'feedback_type': f.feedback_type,
                'message': f.message,
                'created_at': f.created_at
            }
            for f in feedbacks
        ]
    except Exception as e:
        print(f"DATABASE: Error getting feedback: {e}")
        return []
    finally:
        session.close()
