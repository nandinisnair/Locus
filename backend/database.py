"""
Database initialization and management for Locus Copilot
"""

import sqlite3
import hashlib
import os
from pathlib import Path
from passlib.context import CryptContext

DB_PATH = Path(__file__).parent / "locus_copilot.db"
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 16
MAX_BCRYPT_PASSWORD_BYTES = 72


def normalize_email(email: str) -> str:
    """Canonicalize email for uniqueness and authentication lookups."""
    return (email or "").strip().lower()


def password_exceeds_bcrypt_limit(password: str) -> bool:
    """Return True when password is too long for bcrypt (72-byte limit)."""
    if password is None:
        return False
    return len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES


def password_length_is_valid(password: str) -> bool:
    """Return True when password length is within policy bounds (characters)."""
    if password is None:
        return False
    return MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Hash password using a stable default scheme (pbkdf2_sha256)."""
    return pwd_context.hash(password)


def _legacy_sha256_hash(password: str) -> str:
    """Legacy SHA256 hash for backward compatibility with older demo data."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Search history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            locality_name TEXT,
            latitude REAL,
            longitude REAL,
            search_radius REAL,
            business_type TEXT,
            weights TEXT,
            result_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Saved preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preference_name TEXT,
            weights TEXT,
            business_type TEXT,
            search_radius REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Favorite locations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            location_id TEXT,
            location_name TEXT,
            latitude REAL,
            longitude REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()

    # Canonical uniqueness guard for case-insensitive email handling.
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_nocase ON users(email COLLATE NOCASE)")
        conn.commit()
    except sqlite3.IntegrityError:
        # Existing legacy duplicates may block index creation; app-level checks still enforce canonical uniqueness.
        pass
    
    # Create default admin user if not exists
    admin_email = normalize_email(os.getenv("LOCUS_ADMIN_EMAIL", "admin@locuscopilot.com"))
    admin_password = os.getenv("LOCUS_ADMIN_PASSWORD", "admin123")
    cursor.execute("SELECT * FROM users WHERE lower(trim(email)) = ?", (admin_email,))
    if not cursor.fetchone():
        admin_password_hash = hash_password(admin_password)
        cursor.execute("""
            INSERT INTO users (email, password, full_name, is_admin, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (admin_email, admin_password_hash, "Admin User", 1, 1))
        conn.commit()
        print(f"[INFO] Default admin created for {admin_email}")
    
    conn.close()
    print("[INFO] Database initialized")

# User functions
def create_user(email: str, password: str, full_name: str = "") -> dict:
    """Create a new user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        email = normalize_email(email)
        full_name = (full_name or "").strip()

        if not email:
            conn.close()
            return {"success": False, "message": "Email is required"}

        if not password_length_is_valid(password):
            conn.close()
            return {
                "success": False,
                "message": f"Password must be {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters.",
            }

        cursor.execute("SELECT id FROM users WHERE lower(trim(email)) = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "Email already registered"}
        
        password_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO users (email, password, full_name)
            VALUES (?, ?, ?)
        """, (email, password_hash, full_name))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return {"success": True, "user_id": user_id, "message": "User created successfully"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Email already registered"}
    except Exception as e:
        message = str(e)
        if "72 bytes" in message:
            return {
                "success": False,
                "message": f"Password must be {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters.",
            }
        return {"success": False, "message": "Registration failed. Please try again."}

def get_user_by_email(email: str) -> dict:
    """Get user by email"""
    canonical_email = normalize_email(email)
    if not canonical_email:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE lower(trim(email)) = ?", (canonical_email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

def verify_password(email: str, password: str) -> bool:
    """Verify user password"""
    user = get_user_by_email(email)
    if not user:
        return False

    stored = user.get("password", "")

    # Preferred path: passlib hash (bcrypt, pbkdf2_sha256, etc.)
    if stored.startswith("$"):
        if stored.startswith("$2") and password_exceeds_bcrypt_limit(password):
            return False
        try:
            return pwd_context.verify(password, stored)
        except Exception:
            return False

    # Backward compatibility: legacy SHA256, then auto-upgrade to current hash
    legacy_match = stored == _legacy_sha256_hash(password)
    if legacy_match:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(password), user["id"]))
            conn.commit()
            conn.close()
        except Exception:
            pass

    return legacy_match

def update_last_login(user_id: int):
    """Update last login timestamp"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# Search history functions
def save_search(user_id: int, locality_name: str, lat: float, lon: float, 
                radius: float, business_type: str, weights: dict, result_count: int):
    """Save search to history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    import json
    weights_json = json.dumps(weights)
    
    cursor.execute("""
        INSERT INTO searches 
        (user_id, locality_name, latitude, longitude, search_radius, business_type, weights, result_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, locality_name, lat, lon, radius, business_type, weights_json, result_count))
    
    conn.commit()
    conn.close()

def get_user_searches(user_id: int, limit: int = 50) -> list:
    """Get user search history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM searches WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit))
    
    searches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    import json
    for search in searches:
        search['weights'] = json.loads(search['weights'])
    
    return searches

# Saved preferences functions
def save_preference(user_id: int, preference_name: str, weights: dict, 
                   business_type: str = None, search_radius: float = 5.0, description: str = ""):
    """Save a search preference"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    import json
    weights_json = json.dumps(weights)
    
    cursor.execute("""
        INSERT INTO saved_preferences 
        (user_id, preference_name, weights, business_type, search_radius, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, preference_name, weights_json, business_type, search_radius, description))
    
    conn.commit()
    conn.close()

def get_user_preferences(user_id: int) -> list:
    """Get user saved preferences"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM saved_preferences WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    prefs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    import json
    for pref in prefs:
        pref['weights'] = json.loads(pref['weights'])
    
    return prefs

# Favorites functions
def add_favorite(user_id: int, location_id: str, location_name: str, 
                lat: float, lon: float, notes: str = ""):
    """Add location to favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO favorites (user_id, location_id, location_name, latitude, longitude, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, location_id, location_name, lat, lon, notes))
    
    conn.commit()
    conn.close()

def get_user_favorites(user_id: int) -> list:
    """Get user favorite locations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM favorites WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    
    favorites = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return favorites

def remove_favorite(favorite_id: int, user_id: int = None):
    """Remove favorite location, optionally verifying ownership."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id is not None:
        cursor.execute("DELETE FROM favorites WHERE id = ? AND user_id = ?", (favorite_id, user_id))
    else:
        cursor.execute("DELETE FROM favorites WHERE id = ?", (favorite_id,))
    conn.commit()
    conn.close()

# Admin functions
def get_all_users() -> list:
    """Get all users (admin only)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, full_name, is_admin, is_active, created_at, last_login 
        FROM users 
        ORDER BY created_at DESC
    """)
    
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return users

def get_user_stats() -> dict:
    """Get system statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total users
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = 1")
    total_users = dict(cursor.fetchone())['count']
    
    # Total searches
    cursor.execute("SELECT COUNT(*) as count FROM searches")
    total_searches = dict(cursor.fetchone())['count']
    
    # Total favorites
    cursor.execute("SELECT COUNT(*) as count FROM favorites")
    total_favorites = dict(cursor.fetchone())['count']
    
    # Active today
    cursor.execute("""
        SELECT COUNT(DISTINCT user_id) as count FROM searches 
        WHERE DATE(created_at) = DATE('now')
    """)
    active_today = dict(cursor.fetchone())['count']
    
    conn.close()
    
    return {
        "total_users": total_users,
        "total_searches": total_searches,
        "total_favorites": total_favorites,
        "active_today": active_today
    }

def deactivate_user(user_id: int):
    """Deactivate user account"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
