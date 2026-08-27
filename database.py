"""
Универсал маълумотлар базаси модули:
- PostgreSQL (Railway, Supabase, Render, Docker ва б.)
- SQLite (Local ва fallback режими)
"""

import csv
import io
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiosqlite
try:
    import asyncpg
except ImportError:
    asyncpg = None

logger = logging.getLogger(__name__)

DB_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "bot_database.db")


class Database:
    def __init__(self):
        raw_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("DATABASE_PRIVATE_URL")
        if raw_url and raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)

        self.db_url = raw_url
        self.is_postgres = bool(self.db_url and asyncpg is not None)
        self.pool = None
        self.sqlite_path = DB_SQLITE_PATH

    async def init_db(self):
        """Базани аниқлаб, мос жадвалларни яратади."""
        # Қайта текшириш (муҳит ўзгарувчилари юклангандан сўнг)
        raw_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("DATABASE_PRIVATE_URL")
        if raw_url and raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql://", 1)

        if raw_url and asyncpg is not None:
            self.db_url = raw_url
            self.is_postgres = True

        if self.is_postgres:
            logger.info("🐘 PostgreSQL маълумотлар базасига уланмоқда...")
            try:
                self.pool = await asyncpg.create_pool(dsn=self.db_url, min_size=1, max_size=10)
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            user_id BIGINT PRIMARY KEY,
                            username TEXT,
                            first_name TEXT,
                            last_name TEXT,
                            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            calc_count INTEGER DEFAULT 0
                        );
                        CREATE TABLE IF NOT EXISTS calculations (
                            id BIGSERIAL PRIMARY KEY,
                            user_id BIGINT,
                            calc_type TEXT,
                            gfr_val DOUBLE PRECISION,
                            acr_val DOUBLE PRECISION,
                            stage TEXT,
                            risk TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                logger.info("✅ PostgreSQL маълумотлар базаси муваффақиятли уланди ва созланди.")
                return
            except Exception as e:
                logger.error(f"⚠️ PostgreSQL га уланишда хатолик: {e}. SQLite режимига ўтилмоқда...")
                self.is_postgres = False

        # SQLite Fallback
        logger.info("📁 SQLite маълумотлар базасига уланмоқда...")
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    calc_count INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    calc_type TEXT,
                    gfr_val REAL,
                    acr_val REAL,
                    stage TEXT,
                    risk TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)
            await db.commit()
        logger.info("✅ SQLite маълумотлар базаси муваффақиятли уланди.")

    async def add_or_update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ):
        """Фойдаланувчини базага ёзиш ёки янгилаш."""
        now = datetime.now()
        if self.is_postgres and self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, joined_at, last_active_at, calc_count)
                    VALUES ($1, $2, $3, $4, $5, $5, 0)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        last_active_at = EXCLUDED.last_active_at
                """, user_id, username, first_name, last_name, now)
        else:
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, joined_at, last_active_at, calc_count)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        last_active_at = ?
                """, (user_id, username, first_name, last_name, now_str, now_str, now_str))
                await db.commit()

    async def log_calculation(
        self,
        user_id: int,
        calc_type: str,
        gfr_val: Optional[float] = None,
        acr_val: Optional[float] = None,
        stage: Optional[str] = None,
        risk: Optional[str] = None
    ):
        """Ҳисоб-китобни базага қайд қилиш."""
        now = datetime.now()
        if self.is_postgres and self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO calculations (user_id, calc_type, gfr_val, acr_val, stage, risk, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, user_id, calc_type, gfr_val, acr_val, stage, risk, now)
                await conn.execute("""
                    UPDATE users 
                    SET calc_count = calc_count + 1,
                        last_active_at = $1
                    WHERE user_id = $2
                """, now, user_id)
        else:
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO calculations (user_id, calc_type, gfr_val, acr_val, stage, risk, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, calc_type, gfr_val, acr_val, stage, risk, now_str))
                await db.execute("""
                    UPDATE users 
                    SET calc_count = calc_count + 1,
                        last_active_at = ?
                    WHERE user_id = ?
                """, (now_str, user_id))
                await db.commit()

    async def get_detailed_statistics(self) -> Dict[str, Any]:
        """Тўлиқ статистика ҳисоботи."""
        now = datetime.now()
        today_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_dt = today_dt - timedelta(days=7)
        thirty_days_dt = today_dt - timedelta(days=30)

        if self.is_postgres and self.pool:
            async with self.pool.acquire() as conn:
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
                new_today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE joined_at >= $1", today_dt)
                new_7d = await conn.fetchval("SELECT COUNT(*) FROM users WHERE joined_at >= $1", seven_days_dt)
                new_30d = await conn.fetchval("SELECT COUNT(*) FROM users WHERE joined_at >= $1", thirty_days_dt)

                active_today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_active_at >= $1", today_dt)
                active_7d = await conn.fetchval("SELECT COUNT(*) FROM users WHERE last_active_at >= $1", seven_days_dt)

                total_calcs = await conn.fetchval("SELECT COUNT(*) FROM calculations")
                full_calcs = await conn.fetchval("SELECT COUNT(*) FROM calculations WHERE calc_type = 'full'")
                gfr_calcs = await conn.fetchval("SELECT COUNT(*) FROM calculations WHERE calc_type = 'gfr'")
                acr_calcs = await conn.fetchval("SELECT COUNT(*) FROM calculations WHERE calc_type = 'acr'")

                top_stages_rows = await conn.fetch("""
                    SELECT stage, COUNT(*) as cnt 
                    FROM calculations 
                    WHERE stage IS NOT NULL AND stage != ''
                    GROUP BY stage 
                    ORDER BY cnt DESC 
                    LIMIT 5
                """)
                top_stages = [(r["stage"], r["cnt"]) for r in top_stages_rows]

                top_risks_rows = await conn.fetch("""
                    SELECT risk, COUNT(*) as cnt 
                    FROM calculations 
                    WHERE risk IS NOT NULL AND risk != ''
                    GROUP BY risk 
                    ORDER BY cnt DESC
                """)
                top_risks = [(r["risk"], r["cnt"]) for r in top_risks_rows]
        else:
            today_str = today_dt.strftime("%Y-%m-%d 00:00:00")
            seven_days_str = seven_days_dt.strftime("%Y-%m-%d 00:00:00")
            thirty_days_str = thirty_days_dt.strftime("%Y-%m-%d 00:00:00")

            async with aiosqlite.connect(self.sqlite_path) as db:
                async with db.execute("SELECT COUNT(*) FROM users") as cur:
                    total_users = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (today_str,)) as cur:
                    new_today = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (seven_days_str,)) as cur:
                    new_7d = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (thirty_days_str,)) as cur:
                    new_30d = (await cur.fetchone())[0]

                async with db.execute("SELECT COUNT(*) FROM users WHERE last_active_at >= ?", (today_str,)) as cur:
                    active_today = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM users WHERE last_active_at >= ?", (seven_days_str,)) as cur:
                    active_7d = (await cur.fetchone())[0]

                async with db.execute("SELECT COUNT(*) FROM calculations") as cur:
                    total_calcs = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM calculations WHERE calc_type = 'full'") as cur:
                    full_calcs = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM calculations WHERE calc_type = 'gfr'") as cur:
                    gfr_calcs = (await cur.fetchone())[0]
                async with db.execute("SELECT COUNT(*) FROM calculations WHERE calc_type = 'acr'") as cur:
                    acr_calcs = (await cur.fetchone())[0]

                async with db.execute("""
                    SELECT stage, COUNT(*) as cnt 
                    FROM calculations 
                    WHERE stage IS NOT NULL AND stage != ''
                    GROUP BY stage 
                    ORDER BY cnt DESC 
                    LIMIT 5
                """) as cur:
                    top_stages = await cur.fetchall()

                async with db.execute("""
                    SELECT risk, COUNT(*) as cnt 
                    FROM calculations 
                    WHERE risk IS NOT NULL AND risk != ''
                    GROUP BY risk 
                    ORDER BY cnt DESC
                """) as cur:
                    top_risks = await cur.fetchall()

        return {
            "total_users": total_users,
            "new_today": new_today,
            "new_7d": new_7d,
            "new_30d": new_30d,
            "active_today": active_today,
            "active_7d": active_7d,
            "total_calcs": total_calcs,
            "full_calcs": full_calcs,
            "gfr_calcs": gfr_calcs,
            "acr_calcs": acr_calcs,
            "top_stages": top_stages,
            "top_risks": top_risks
        }

    async def export_users_csv(self) -> io.BytesIO:
        """Фойдаланувчилар рўйхатини CSV форматида экспорт қилади."""
        if self.is_postgres and self.pool:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT user_id, username, first_name, last_name, 
                           to_char(joined_at, 'YYYY-MM-DD HH24:MI:SS') as j_at,
                           to_char(last_active_at, 'YYYY-MM-DD HH24:MI:SS') as la_at,
                           calc_count
                    FROM users
                    ORDER BY joined_at DESC
                """)
                csv_data = [list(r.values()) for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                async with db.execute("""
                    SELECT user_id, username, first_name, last_name, joined_at, last_active_at, calc_count
                    FROM users
                    ORDER BY joined_at DESC
                """) as cur:
                    csv_data = await cur.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "User ID", "Username", "First Name", "Last Name",
            "Joined At", "Last Active", "Total Calculations"
        ])
        for row in csv_data:
            writer.writerow(row)

        bytes_io = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        bytes_io.seek(0)
        return bytes_io

    async def get_all_user_ids(self) -> List[int]:
        """Оммавий хабар тарқатиш учун барча фойдаланувчилар ID си."""
        if self.is_postgres and self.pool:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT user_id FROM users")
                return [r["user_id"] for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                async with db.execute("SELECT user_id FROM users") as cur:
                    rows = await cur.fetchall()
                    return [r[0] for r in rows]


db = Database()
