import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "data/bot.db")

class Database:
    def __init__(self):
        self.db = None

    async def init(self):
        os.makedirs("data", exist_ok=True)
        self.db = await aiosqlite.connect(DB_PATH)
        await self._create_tables()

    async def _create_tables(self):
        await self.db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                reputation INTEGER DEFAULT 0,
                vouches INTEGER DEFAULT 0,
                deals_completed INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS hiring_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT CHECK(type IN ('hiring', 'for_hire')),
                title TEXT,
                description TEXT,
                budget TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by INTEGER,
                approved_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vouches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER,
                to_user INTEGER,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER,
                seller_id INTEGER,
                description TEXT,
                amount TEXT,
                status TEXT DEFAULT 'pending',
                buyer_confirmed INTEGER DEFAULT 0,
                seller_confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                reported_id INTEGER,
                reason TEXT,
                evidence TEXT,
                status TEXT DEFAULT 'open',
                handled_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                user_id INTEGER,
                moderator_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await self.db.commit()

    async def get_user(self, user_id: int):
        async with self.db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as c:
            return await c.fetchone()

    async def ensure_user(self, user_id: int, username: str):
        await self.db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await self.db.commit()

    async def add_reputation(self, user_id: int, amount: int):
        await self.db.execute(
            "UPDATE users SET reputation = reputation + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await self.db.commit()

    async def add_vouch(self, from_id: int, to_id: int, comment: str):
        await self.db.execute(
            "INSERT INTO vouches (from_user, to_user, comment) VALUES (?, ?, ?)",
            (from_id, to_id, comment)
        )
        await self.db.execute(
            "UPDATE users SET vouches = vouches + 1 WHERE user_id = ?", (to_id,)
        )
        await self.db.commit()

    async def get_vouches(self, user_id: int):
        async with self.db.execute(
            "SELECT from_user, comment, created_at FROM vouches WHERE to_user = ? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        ) as c:
            return await c.fetchall()

    async def create_hiring_post(self, user_id, type_, title, description, budget):
        async with self.db.execute(
            "INSERT INTO hiring_posts (user_id, type, title, description, budget) VALUES (?,?,?,?,?)",
            (user_id, type_, title, description, budget)
        ) as c:
            await self.db.commit()
            return c.lastrowid

    async def get_pending_posts(self):
        async with self.db.execute(
            "SELECT * FROM hiring_posts WHERE status = 'pending' ORDER BY created_at ASC"
        ) as c:
            return await c.fetchall()

    async def approve_post(self, post_id: int, mod_id: int):
        await self.db.execute(
            "UPDATE hiring_posts SET status='approved', approved_by=?, approved_at=CURRENT_TIMESTAMP WHERE id=?",
            (mod_id, post_id)
        )
        await self.db.commit()

    async def reject_post(self, post_id: int, mod_id: int):
        await self.db.execute(
            "UPDATE hiring_posts SET status='rejected', approved_by=? WHERE id=?",
            (mod_id, post_id)
        )
        await self.db.commit()

    async def create_deal(self, buyer_id, seller_id, description, amount):
        async with self.db.execute(
            "INSERT INTO deals (buyer_id, seller_id, description, amount) VALUES (?,?,?,?)",
            (buyer_id, seller_id, description, amount)
        ) as c:
            await self.db.commit()
            return c.lastrowid

    async def confirm_deal(self, deal_id: int, user_id: int, role: str):
        col = "buyer_confirmed" if role == "buyer" else "seller_confirmed"
        await self.db.execute(f"UPDATE deals SET {col} = 1 WHERE id = ?", (deal_id,))
        async with self.db.execute("SELECT buyer_confirmed, seller_confirmed FROM deals WHERE id = ?", (deal_id,)) as c:
            row = await c.fetchone()
        if row and row[0] == 1 and row[1] == 1:
            await self.db.execute(
                "UPDATE deals SET status='completed', completed_at=CURRENT_TIMESTAMP WHERE id=?", (deal_id,)
            )
            async with self.db.execute("SELECT buyer_id, seller_id FROM deals WHERE id=?", (deal_id,)) as c:
                deal = await c.fetchone()
            await self.db.execute("UPDATE users SET deals_completed = deals_completed + 1 WHERE user_id IN (?,?)",
                                  (deal[0], deal[1]))
        await self.db.commit()

    async def create_report(self, reporter_id, reported_id, reason, evidence):
        async with self.db.execute(
            "INSERT INTO reports (reporter_id, reported_id, reason, evidence) VALUES (?,?,?,?)",
            (reporter_id, reported_id, reason, evidence)
        ) as c:
            await self.db.commit()
            return c.lastrowid

    async def log_action(self, action, user_id, moderator_id, details):
        await self.db.execute(
            "INSERT INTO audit_logs (action, user_id, moderator_id, details) VALUES (?,?,?,?)",
            (action, user_id, moderator_id, details)
        )
        await self.db.commit()
