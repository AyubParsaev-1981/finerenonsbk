"""
SQLite маълумотлар базаси ва тўлиқ аналитика модули (aiosqlite).
"""

import csv
import io
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_database.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Жадвалларни яратиш ва базани ишга тушириш."""
        async with aiosqlite.connect(self.db_path) as db:
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

    async def add_or_update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ):
        """Фойдаланувчини қўшиш ёки фаоллик вақтини янгилаш."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, joined_at, last_active_at, calc_count)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_active_at = ?
            """, (user_id, username, first_name, last_name, now, now, now))
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
        """Ҳисоб-китобни базага қайд қилиш ва фойдаланувчи ҳисобини ошириш."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("""
                INSERT INTO calculations (user_id, calc_type, gfr_val, acr_val, stage, risk, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, calc_type, gfr_val, acr_val, stage, risk, now))

            # Фойдаланувчининг calc_count ни ошириш
            await db.execute("""
                UPDATE users 
                SET calc_count = calc_count + 1,
                    last_active_at = ?
                WHERE user_id = ?
            """, (now, user_id))
            await db.commit()

    async def get_detailed_statistics(self) -> Dict[str, Any]:
        """Тўлиқ ва батафсил статистикани ҳисоблаб қайтариш."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d 00:00:00")
            seven_days_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
            thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")

            # 1. Умумий фойдаланувчилар
            async with db.execute("SELECT COUNT(*) FROM users") as cur:
                total_users = (await cur.fetchone())[0]

            # 2. Янги қўшилганлар (бугун, 7 кун, 30 кун)
            async with db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (today_str,)) as cur:
                new_today = (await cur.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (seven_days_ago,)) as cur:
                new_7d = (await cur.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (thirty_days_ago,)) as cur:
                new_30d = (await cur.fetchone())[0]

            # 3. Фаол фойдаланувчилар (бугун, 7 кун)
            async with db.execute("SELECT COUNT(*) FROM users WHERE last_active_at >= ?", (today_str,)) as cur:
                active_today = (await cur.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM users WHERE last_active_at >= ?", (seven_days_ago,)) as cur:
                active_7d = (await cur.fetchone())[0]

            # 4. Ҳисоб-китоблар сони
            async with db.execute("SELECT COUNT(*) FROM calculations") as cur:
                total_calcs = (await cur.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM calculations WHERE calc_type = 'full'") as cur:
                full_calcs = (await cur.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM calculations WHERE calc_type = 'gfr'") as cur:
                gfr_calcs = (await cur.fetchone())[0]

            async with db.execute("SELECT COUNT(*) FROM calculations WHERE calc_type = 'acr'") as cur:
                acr_calcs = (await cur.fetchone())[0]

            # 5. Энг кўп учраган СБК босқичлари
            async with db.execute("""
                SELECT stage, COUNT(*) as cnt 
                FROM calculations 
                WHERE stage IS NOT NULL AND stage != ''
                GROUP BY stage 
                ORDER BY cnt DESC 
                LIMIT 5
            """) as cur:
                top_stages = await cur.fetchall()

            # 6. Хавф тоифалари тақсимоти
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
        """Фойдаланувчилар рўйхатини Excel/CSV учун UTF-8-SIG форматида экспорт қилади."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, username, first_name, last_name, joined_at, last_active_at, calc_count
                FROM users
                ORDER BY joined_at DESC
            """) as cur:
                rows = await cur.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "User ID", "Username", "First Name", "Last Name",
            "Joined At", "Last Active", "Total Calculations"
        ])
        for row in rows:
            writer.writerow(row)

        # Excel да UTF-8 белгиларини тўғри кўрсатиш учун UTF-8-SIG (BOM) билан қайтариш
        bytes_io = io.BytesIO(output.getvalue().encode("utf-8-sig"))
        bytes_io.seek(0)
        return bytes_io

    async def get_all_user_ids(self) -> List[int]:
        """Оммавий хабар юбориш учун барча фойдаланувчилар ID рўйхатини олади."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cur:
                rows = await cur.fetchall()
                return [r[0] for r in rows]


db = Database()
