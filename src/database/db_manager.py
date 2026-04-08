import sqlite3
import os
import threading
from src.utils.logger import get_logger

logger = get_logger("DBManager")

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _init_db(self):
        db_path = os.path.join(os.getcwd(), 'data')
        os.makedirs(db_path, exist_ok=True)
        self.db_file = os.path.join(db_path, 'app.db')

        self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        try:
            cursor = self.connection.cursor()

            # Settings Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Profiles Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    group_name TEXT,
                    proxy_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_opened TIMESTAMP,
                    user_agent TEXT,
                    status TEXT DEFAULT 'Ready',
                    external_path TEXT
                )
            ''')

            # Add external_path column to existing tables if missing (migration)
            try:
                cursor.execute('ALTER TABLE profiles ADD COLUMN external_path TEXT')
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Proxies Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    port TEXT NOT NULL,
                    username TEXT,
                    password TEXT,
                    status TEXT DEFAULT 'Untested'
                )
            ''')

            self.connection.commit()
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")

    def execute(self, query, params=()):
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                self.connection.commit()
                return cursor
            except Exception as e:
                logger.error(f"Database execution error: {e} - Query: {query}")
                return None

    def fetchall(self, query, params=()):
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
            except Exception as e:
                logger.error(f"Database fetchall error: {e} - Query: {query}")
                return []

    def fetchone(self, query, params=()):
        with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                return cursor.fetchone()
            except Exception as e:
                logger.error(f"Database fetchone error: {e} - Query: {query}")
                return None
