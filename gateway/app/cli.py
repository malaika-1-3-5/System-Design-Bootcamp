"""CLI for admin tasks — run with: python -m app.cli <command>

Commands:
    seed    — Insert initial market price data (idempotent)
"""

import asyncio
import sys
import uuid
from datetime import date

from sqlalchemy import text
from app.db import AsyncSessionLocal


MARKET_PRICES = [
    # Rice
    ("Rice",      "Karnataka",      "Bangalore",  2450, date(2026, 2, 13)),
    ("Rice",      "Karnataka",      "Mysore",     2380, date(2026, 2, 13)),
    ("Rice",      "Karnataka",      "Hubli",      2410, date(2026, 2, 13)),
    ("Rice",      "Andhra Pradesh", "Vijayawada", 2500, date(2026, 2, 13)),
    ("Rice",      "Andhra Pradesh", "Guntur",     2470, date(2026, 2, 13)),
    ("Rice",      "Tamil Nadu",     "Chennai",    2520, date(2026, 2, 13)),
    ("Rice",      "Tamil Nadu",     "Coimbatore", 2490, date(2026, 2, 13)),
    # Wheat
    ("Wheat",     "Madhya Pradesh", "Bhopal",     2275, date(2026, 2, 13)),
    ("Wheat",     "Madhya Pradesh", "Indore",     2250, date(2026, 2, 13)),
    ("Wheat",     "Punjab",         "Ludhiana",   2300, date(2026, 2, 13)),
    ("Wheat",     "Punjab",         "Amritsar",   2280, date(2026, 2, 13)),
    ("Wheat",     "Haryana",        "Karnal",     2310, date(2026, 2, 13)),
    # Tomato
    ("Tomato",    "Karnataka",      "Bangalore",  1800, date(2026, 2, 13)),
    ("Tomato",    "Karnataka",      "Mysore",     1750, date(2026, 2, 13)),
    ("Tomato",    "Maharashtra",    "Pune",       2100, date(2026, 2, 13)),
    ("Tomato",    "Maharashtra",    "Nashik",     1950, date(2026, 2, 13)),
    ("Tomato",    "Andhra Pradesh", "Kurnool",    1680, date(2026, 2, 13)),
    # Potato
    ("Potato",    "Uttar Pradesh",  "Agra",       1200, date(2026, 2, 13)),
    ("Potato",    "Uttar Pradesh",  "Lucknow",    1250, date(2026, 2, 13)),
    ("Potato",    "West Bengal",    "Kolkata",    1350, date(2026, 2, 13)),
    ("Potato",    "Punjab",         "Jalandhar",  1180, date(2026, 2, 13)),
    # Onion
    ("Onion",     "Maharashtra",    "Nashik",     2800, date(2026, 2, 13)),
    ("Onion",     "Maharashtra",    "Pune",       2750, date(2026, 2, 13)),
    ("Onion",     "Karnataka",      "Bangalore",  2900, date(2026, 2, 13)),
    ("Onion",     "Madhya Pradesh", "Indore",     2650, date(2026, 2, 13)),
    # Cotton
    ("Cotton",    "Gujarat",        "Ahmedabad",  6200, date(2026, 2, 13)),
    ("Cotton",    "Gujarat",        "Rajkot",     6150, date(2026, 2, 13)),
    ("Cotton",    "Maharashtra",    "Nagpur",     6050, date(2026, 2, 13)),
    # Sugarcane
    ("Sugarcane", "Uttar Pradesh",  "Lucknow",    350,  date(2026, 2, 13)),
    ("Sugarcane", "Maharashtra",    "Kolhapur",   380,  date(2026, 2, 13)),
    ("Sugarcane", "Karnataka",      "Belgaum",    365,  date(2026, 2, 13)),
]


async def seed():
    """Insert market prices — skips rows that already exist (idempotent)."""
    async with AsyncSessionLocal() as session:
        inserted = 0
        for crop, state, mandi, price, price_date in MARKET_PRICES:
            exists = await session.execute(
                text(
                    "SELECT 1 FROM market_prices "
                    "WHERE crop=:crop AND state=:state AND mandi=:mandi"
                ),
                {"crop": crop, "state": state, "mandi": mandi},
            )
            if not exists.scalar():
                await session.execute(
                    text(
                        "INSERT INTO market_prices (id, crop, state, mandi, price_per_quintal, price_date) "
                        "VALUES (:id, :crop, :state, :mandi, :price, :price_date)"
                    ),
                    {"id": uuid.uuid4(), "crop": crop, "state": state, "mandi": mandi,
                     "price": price, "price_date": price_date},
                )
                inserted += 1
        await session.commit()
    print(f"Seeding complete — {inserted} rows inserted, {len(MARKET_PRICES) - inserted} already existed.")


COMMANDS = {
    "seed": lambda: asyncio.run(seed()),
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python -m app.cli <command>")
        print(f"Commands: {', '.join(COMMANDS)}")
        sys.exit(1)

    COMMANDS[sys.argv[1]]()
