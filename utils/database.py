"""
Database utilities for the Quality of Dutch Government application.
Handles database connections and operations for Auth and Quant tables.
"""

import os
from datetime import datetime, date
from sqlalchemy import create_engine, text, Column, String, Integer, Numeric, Date, Text, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.sql import func
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
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        return f"sqlite:///{db_path}"


# SQLAlchemy setup
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class AuthUser(Base):
        """Auth table model matching the provided schema."""
        __tablename__ = 'auth'
        __table_args__ = (
            CheckConstraint("access_level IN ('U', 'R')", name='check_access_level'),
        )
        
        user_id = Column(String(10), primary_key=True)
        access_level = Column(String(1), nullable=False)  # 'U' for End-User, 'R' for Researcher
        email = Column(String(40), unique=True, nullable=False)
        password_hash = Column(String(128), nullable=False)  # SHA256 hash
        created_date = Column(Date, nullable=False)
        interaction_count = Column(Integer, default=0, nullable=False)
        satisfaction_baseline = Column(Numeric(3, 1))  # Can be NULL until first rating
    
    class QuantInteraction(Base):
        """Quant table model matching the provided schema."""
        __tablename__ = 'quant'
        __table_args__ = (
            CheckConstraint("verification_flag IN ('V', 'U')", name='check_verification_flag'),
            CheckConstraint("satisfaction_raw >= 0 AND satisfaction_raw <= 10", name='check_satisfaction_range'),
        )
        
        interaction_id = Column(String(12), primary_key=True)
        user_id = Column(String(10), ForeignKey('auth.user_id'), nullable=False)
        correlation_index = Column(Numeric(5, 3))  # Can be NULL, set by RAG
        verification_flag = Column(String(1), nullable=False, default='U')  # 'V' for verified, 'U' for unverified
        satisfaction_raw = Column(Numeric(3, 1), nullable=False)
        satisfaction_normalized = Column(Numeric(3, 1))  # Can be NULL until normalized
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

        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    class RagChunk(Base):
        """
        Stores chunked text for RAG retrieval. One document has many chunks.
        """
        __tablename__ = "rag_chunks"

        id = Column(Integer, primary_key=True, autoincrement=True)

        document_id = Column(Integer, ForeignKey("rag_documents.id"), nullable=False)
        chunk_index = Column(Integer, nullable=False)

        page_start = Column(Integer, nullable=True)
        page_end = Column(Integer, nullable=True)

        chunk_text = Column(Text, nullable=False)

        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
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

        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    class RagChunk(Base):
        """
        Stores chunked text for RAG retrieval. One document has many chunks.
        """
        __tablename__ = "rag_chunks"

        id = Column(Integer, primary_key=True, autoincrement=True)

        document_id = Column(Integer, ForeignKey("rag_documents.id"), nullable=False)
        chunk_index = Column(Integer, nullable=False)

        page_start = Column(Integer, nullable=True)
        page_end = Column(Integer, nullable=True)

        chunk_text = Column(Text, nullable=False)

        created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

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
            print(f"DATABASE: Connected to {database_url.split('@')[-1] if '@' in database_url else database_url}")
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

import hashlib

def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(password) == password_hash


def get_user_by_email(email: str, include_hash: bool = False) -> Optional[Dict[str, Any]]:
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
        user = session.query(AuthUser).filter(AuthUser.email == email.lower()).first()
        if user:
            result = {
                'user_id': user.user_id,
                'access_level': user.access_level,
                'email': user.email,
                'created_date': user.created_date,
                'interaction_count': user.interaction_count or 0,
                'satisfaction_baseline': float(user.satisfaction_baseline) if user.satisfaction_baseline else None
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


def authenticate_user_db(email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
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
        exists = session.query(AuthUser).filter(AuthUser.email == email.lower().strip()).first() is not None
        return exists
    except Exception:
        return False
    finally:
        session.close()


def create_user(user_id: str, email: str, access_level: str = 'U', password: Optional[str] = None) -> Tuple[bool, str]:
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
        pwd_hash = hash_password(password) if password else hash_password("changeme")
        
        new_user = AuthUser(
            user_id=user_id[:10],
            email=email_clean,
            password_hash=pwd_hash,
            access_level=access_clean,
            created_date=date.today(),
            interaction_count=0,
            satisfaction_baseline=None
        )
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
        user = session.query(AuthUser).filter(AuthUser.user_id == user_id).first()
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
        user = session.query(AuthUser).filter(AuthUser.user_id == user_id).first()
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
    correlation_index: Optional[float] = None,
    verification_flag: str = 'U',
    satisfaction_normalized: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Save a new interaction to the Quant table.
    
    Args:
        user_id: The user's ID
        satisfaction_raw: Raw satisfaction score (0-10)
        summary: Topic summary from the interaction
        correlation_index: Similarity/correlation score (optional, set by RAG)
        verification_flag: 'V' for verified, 'U' for unverified
        satisfaction_normalized: Normalized satisfaction score (optional)
        
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
            correlation_index=correlation_index,
            verification_flag=verification_flag[0].upper(),
            satisfaction_raw=satisfaction_raw,
            satisfaction_normalized=satisfaction_normalized,
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


def get_all_interactions(
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Get interactions from the Quant table with optional filters.
    
    Args:
        user_id: Filter by user ID (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum number of records to return
        
    Returns:
        List of interaction dicts
    """
    session = get_session()
    if session is None:
        return []
    
    try:
        query = session.query(QuantInteraction)
        
        if user_id:
            query = query.filter(QuantInteraction.user_id == user_id)
        if start_date:
            query = query.filter(QuantInteraction.interaction_date >= start_date)
        if end_date:
            query = query.filter(QuantInteraction.interaction_date <= end_date)
        
        query = query.order_by(QuantInteraction.interaction_date.desc()).limit(limit)
        
        results = []
        for interaction in query.all():
            results.append({
                'interaction_id': interaction.interaction_id,
                'user_id': interaction.user_id,
                'correlation_index': float(interaction.correlation_index) if interaction.correlation_index else None,
                'verification_flag': interaction.verification_flag,
                'satisfaction_raw': float(interaction.satisfaction_raw) if interaction.satisfaction_raw else None,
                'satisfaction_normalized': float(interaction.satisfaction_normalized) if interaction.satisfaction_normalized else None,
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
            func.count(QuantInteraction.interaction_id).label('total_interactions'),
            func.avg(QuantInteraction.satisfaction_raw).label('avg_satisfaction'),
            func.count(func.distinct(QuantInteraction.user_id)).label('unique_users'),
            func.sum(
                sqlalchemy.case((QuantInteraction.verification_flag == 'V', 1), else_=0)
            ).label('verified_count')
        ).first()
        
        return {
            'total_interactions': stats.total_interactions or 0,
            'avg_satisfaction': round(float(stats.avg_satisfaction), 2) if stats.avg_satisfaction else 0,
            'unique_users': stats.unique_users or 0,
            'verified_count': stats.verified_count or 0
        }
    except Exception as e:
        print(f"DATABASE: Error getting stats: {e}")
        return {}
    finally:
        session.close()
