import asyncio
import datetime
import random
import uuid
from decimal import Decimal

from faker import Faker
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.models import (
    Category,
    Event,
    InventoryHistory,
    Order,
    OrderItem,
    Payment,
    Product,
    Recommendation,
    Review,
    Segment,
    User,
)

fake = Faker()


async def clear_database(db: AsyncSession) -> None:
    """Clear existing tables in reverse dependency order."""
    print("Clearing existing tables in Supabase...")
    await db.execute(delete(InventoryHistory))
    await db.execute(delete(Payment))
    await db.execute(delete(OrderItem))
    await db.execute(delete(Order))
    await db.execute(delete(Review))
    await db.execute(delete(Event))
    await db.execute(delete(Recommendation))
    await db.execute(delete(Segment))
    await db.execute(delete(Product))
    await db.execute(delete(Category))
    await db.execute(delete(User))
    await db.commit()
    print("Tables cleared successfully.")


async def seed_database() -> None:
    """Async seed script using Faker to generate realistic retail demo data."""
    async with AsyncSessionLocal() as db:
        await clear_database(db)
        print("Starting seeding process...")

        # 1. Seed Users (100)
        users = []
        for i in range(100):
            # 10% soft deleted, 10% inactive
            is_deleted = i < 10
            is_active = i >= 10 and i < 90
            deleted_at = datetime.datetime.now(datetime.UTC) if is_deleted else None
            role = "admin" if i == 0 else ("manager" if i == 1 else "customer")

            user = User(
                full_name=fake.name(),
                email=f"user_{i}_{fake.unique.email()}",
                password_hash="pbkdf2:sha256:600000$mock_hash$abcdef1234567890",
                phone=fake.phone_number()[:20],
                role=role,
                is_active=is_active,
                is_deleted=is_deleted,
                deleted_at=deleted_at,
            )
            db.add(user)
            users.append(user)
        await db.commit()
        print(f"Seeded {len(users)} users.")

        # 2. Seed Categories (15)
        category_names = [
            "Electronics",
            "Apparel & Fashion",
            "Home & Kitchen",
            "Books & Media",
            "Beauty & Personal Care",
            "Sports & Outdoors",
            "Toys & Games",
            "Automotive",
            "Grocery & Gourmet",
            "Pet Supplies",
            "Health & Wellness",
            "Garden & Outdoor",
            "Office Products",
            "Tools & Home Improvement",
            "Baby Care",
        ]
        categories = []
        for idx, name in enumerate(category_names):
            is_deleted = idx < 2  # 2 soft deleted categories
            deleted_at = datetime.datetime.now(datetime.UTC) if is_deleted else None
            category = Category(
                name=name,
                slug=name.lower()
                .replace(" & ", "-")
                .replace(" ", "-")
                .replace("&", "-"),
                description=fake.sentence(),
                is_deleted=is_deleted,
                deleted_at=deleted_at,
            )
            db.add(category)
            categories.append(category)
        await db.commit()
        print(f"Seeded {len(categories)} categories.")

        # 3. Seed Products (100) with realistic names per category
        # Category-aware product catalog: {category_name: [(name, brand, price_min, price_max), ...]}
        product_catalog: dict[str, list[tuple[str, str, float, float]]] = {
            "Electronics": [
                ("Wireless Noise-Cancelling Headphones", "Sony", 149.99, 349.99),
                ("4K Ultra HD Smart TV 55\"", "Samsung", 399.99, 799.99),
                ("Portable Bluetooth Speaker", "JBL", 29.99, 149.99),
                ("USB-C Fast Charging Hub", "Anker", 24.99, 59.99),
                ("Mechanical Gaming Keyboard", "Corsair", 79.99, 179.99),
                ("Wireless Gaming Mouse", "Logitech", 39.99, 99.99),
                ("True Wireless Earbuds Pro", "Apple", 129.99, 249.99),
                ("Portable Power Bank 20000mAh", "Anker", 29.99, 69.99),
            ],
            "Apparel & Fashion": [
                ("Classic Fit Cotton Polo Shirt", "Ralph Lauren", 49.99, 89.99),
                ("Slim Fit Stretch Jeans", "Levi's", 39.99, 79.99),
                ("Lightweight Running Sneakers", "Nike", 69.99, 159.99),
                ("Premium Leather Belt", "Tommy Hilfiger", 29.99, 69.99),
                ("Wool Blend Overcoat", "Zara", 99.99, 249.99),
                ("Athletic Performance T-Shirt", "Under Armour", 24.99, 49.99),
                ("Canvas Casual Backpack", "Herschel", 49.99, 89.99),
                ("UV Protection Sunglasses", "Ray-Ban", 89.99, 199.99),
            ],
            "Home & Kitchen": [
                ("Stainless Steel French Press", "Bodum", 19.99, 49.99),
                ("Non-Stick Ceramic Cookware Set", "GreenPan", 89.99, 199.99),
                ("Programmable Coffee Maker 12-Cup", "Cuisinart", 49.99, 129.99),
                ("Bamboo Cutting Board Set", "Royal Craft", 14.99, 34.99),
                ("Cast Iron Dutch Oven 6-Qt", "Lodge", 39.99, 79.99),
                ("Electric Kettle Temperature Control", "Fellow", 69.99, 149.99),
                ("Silicone Kitchen Utensil Set", "OXO", 19.99, 44.99),
            ],
            "Books & Media": [
                ("The Art of Clear Thinking", "Penguin Books", 12.99, 24.99),
                ("JavaScript: The Definitive Guide", "O'Reilly Media", 29.99, 49.99),
                ("Atomic Habits Hardcover", "Avery Publishing", 14.99, 27.99),
                ("World Atlas 2026 Edition", "National Geographic", 19.99, 39.99),
                ("Creative Photography Masterclass", "DK Publishing", 24.99, 44.99),
                ("The Lean Startup", "Crown Business", 14.99, 29.99),
            ],
            "Beauty & Personal Care": [
                ("Vitamin C Brightening Serum", "The Ordinary", 9.99, 29.99),
                ("Hydrating Face Moisturizer SPF 30", "CeraVe", 12.99, 24.99),
                ("Argan Oil Hair Treatment", "Moroccanoil", 29.99, 49.99),
                ("Charcoal Purifying Face Mask", "Origins", 19.99, 34.99),
                ("Electric Precision Trimmer", "Philips", 24.99, 59.99),
                ("Natural Deodorant Stick", "Native", 9.99, 14.99),
            ],
            "Sports & Outdoors": [
                ("Yoga Mat Extra Thick 6mm", "Manduka", 29.99, 79.99),
                ("Adjustable Dumbbell Set 25lb", "Bowflex", 149.99, 349.99),
                ("Insulated Water Bottle 32oz", "Hydro Flask", 29.99, 49.99),
                ("Camping Tent 4-Person", "Coleman", 89.99, 249.99),
                ("Resistance Bands Set", "TheraBand", 14.99, 34.99),
                ("GPS Running Watch", "Garmin", 149.99, 399.99),
            ],
            "Toys & Games": [
                ("Building Blocks Creative Set 1000pc", "LEGO", 49.99, 99.99),
                ("Strategy Board Game Collection", "Hasbro", 19.99, 49.99),
                ("Remote Control Racing Drone", "DJI", 99.99, 299.99),
                ("Wooden Puzzle Brain Teaser Set", "Melissa & Doug", 14.99, 29.99),
                ("Interactive Learning Tablet Kids", "LeapFrog", 79.99, 149.99),
            ],
            "Automotive": [
                ("Dash Camera 4K Night Vision", "Vantrue", 89.99, 199.99),
                ("Portable Tire Inflator Digital", "AstroAI", 29.99, 59.99),
                ("LED Headlight Bulbs H11 Pair", "Sylvania", 24.99, 49.99),
                ("Car Phone Mount Magnetic", "iOttie", 14.99, 34.99),
                ("All-Weather Floor Mats Set", "WeatherTech", 49.99, 149.99),
            ],
            "Grocery & Gourmet": [
                ("Organic Cold Brew Coffee Concentrate", "Chameleon", 9.99, 16.99),
                ("Dark Chocolate Truffle Collection", "Lindt", 14.99, 34.99),
                ("Extra Virgin Olive Oil 1L", "Bertolli", 9.99, 19.99),
                ("Matcha Green Tea Powder Premium", "Jade Leaf", 19.99, 34.99),
                ("Mixed Nuts Trail Mix 2lb", "Kirkland", 12.99, 24.99),
            ],
            "Pet Supplies": [
                ("Automatic Pet Feeder Smart WiFi", "PetSafe", 79.99, 149.99),
                ("Orthopedic Dog Bed Large", "Furhaven", 29.99, 79.99),
                ("Interactive Cat Toy Laser", "PetFusion", 14.99, 29.99),
                ("Retractable Dog Leash 16ft", "Flexi", 14.99, 29.99),
                ("Grain-Free Dog Treats 1lb", "Blue Buffalo", 9.99, 19.99),
            ],
            "Health & Wellness": [
                ("Digital Blood Pressure Monitor", "Omron", 39.99, 79.99),
                ("Foam Roller Muscle Recovery", "TriggerPoint", 19.99, 44.99),
                ("Vitamin D3 5000 IU 360ct", "NatureWise", 14.99, 24.99),
                ("Meditation Cushion Zafu", "Florensi", 29.99, 59.99),
                ("Pulse Oximeter Fingertip", "Zacurate", 14.99, 29.99),
            ],
            "Garden & Outdoor": [
                ("Solar Pathway Lights 12-Pack", "BEAU JARDIN", 24.99, 49.99),
                ("Stainless Steel Garden Tool Set", "Fiskars", 29.99, 59.99),
                ("Portable Hammock with Stand", "Vivere", 69.99, 149.99),
                ("Self-Watering Planter Large", "Lechuza", 34.99, 79.99),
                ("Outdoor String Lights 48ft", "Brightech", 19.99, 39.99),
            ],
            "Office Products": [
                ("Ergonomic Office Chair Mesh", "Herman Miller", 299.99, 599.99),
                ("Standing Desk Converter 36\"", "FlexiSpot", 149.99, 349.99),
                ("Wireless Presentation Clicker", "Logitech", 24.99, 49.99),
                ("Document Scanner Portable", "Fujitsu", 199.99, 399.99),
                ("Noise Machine White Sound", "LectroFan", 29.99, 59.99),
            ],
            "Tools & Home Improvement": [
                ("Cordless Drill Driver 20V", "DeWalt", 79.99, 149.99),
                ("LED Work Light Rechargeable", "Milwaukee", 29.99, 69.99),
                ("Digital Laser Measure 165ft", "Bosch", 39.99, 89.99),
                ("Smart Thermostat WiFi Enabled", "Nest", 129.99, 249.99),
                ("Multi-Tool Pliers 18-in-1", "Leatherman", 49.99, 99.99),
            ],
            "Baby Care": [
                ("Baby Monitor Camera WiFi 1080p", "VTech", 49.99, 129.99),
                ("Organic Baby Wipes 720ct", "WaterWipes", 19.99, 34.99),
                ("Convertible Car Seat All-in-One", "Graco", 149.99, 349.99),
                ("Baby Carrier Ergonomic Wrap", "Ergobaby", 79.99, 179.99),
                ("Silicone Baby Feeding Set", "Bumkins", 14.99, 29.99),
            ],
        }

        # Build category name -> category object lookup
        cat_lookup = {c.name: c for c in categories}

        products = []
        product_idx = 0
        # Flatten catalog entries across all categories
        all_entries: list[tuple[str, str, str, float, float]] = []
        for cat_name, items in product_catalog.items():
            for name, brand_name, p_min, p_max in items:
                all_entries.append((cat_name, name, brand_name, p_min, p_max))

        for i in range(100):
            entry = all_entries[i % len(all_entries)]
            cat_name, prod_name, brand_name, p_min, p_max = entry
            cat = cat_lookup.get(cat_name, random.choice(categories))

            is_deleted = i < 10  # 10% soft deleted
            deleted_at = datetime.datetime.now(datetime.UTC) if is_deleted else None
            is_active = i >= 10

            initial_stock = random.randint(2, 120)
            price = Decimal(f"{random.uniform(p_min, p_max):.2f}")
            # Append index suffix for uniqueness when catalog wraps around
            display_name = prod_name if i < len(all_entries) else f"{prod_name} v{i // len(all_entries) + 1}"

            # Curated real product image mapping using Unsplash photo IDs
            product_images = {
                "Wireless Noise-Cancelling Headphones": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=70",
                "4K Ultra HD Smart TV 55\"": "https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=500&auto=format&fit=crop&q=70",
                "Portable Bluetooth Speaker": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500&auto=format&fit=crop&q=70",
                "USB-C Fast Charging Hub": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&auto=format&fit=crop&q=70",
                "Mechanical Gaming Keyboard": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&auto=format&fit=crop&q=70",
                "Wireless Gaming Mouse": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop&q=70",
                "True Wireless Earbuds Pro": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&auto=format&fit=crop&q=70",
                "Portable Power Bank 20000mAh": "https://images.unsplash.com/photo-1609592424109-dd25567b45f4?w=500&auto=format&fit=crop&q=70",
                "Classic Fit Cotton Polo Shirt": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=500&auto=format&fit=crop&q=70",
                "Slim Fit Stretch Jeans": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500&auto=format&fit=crop&q=70",
                "Lightweight Running Sneakers": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop&q=70",
                "Premium Leather Belt": "https://images.unsplash.com/photo-1624222247344-550fb8ecfb7d?w=500&auto=format&fit=crop&q=70",
                "Wool Blend Overcoat": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=500&auto=format&fit=crop&q=70",
                "Athletic Performance T-Shirt": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop&q=70",
                "Canvas Casual Backpack": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=70",
                "UV Protection Sunglasses": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500&auto=format&fit=crop&q=70",
                "Stainless Steel French Press": "https://images.unsplash.com/photo-1577968897966-3d4325b36b61?w=500&auto=format&fit=crop&q=70",
                "Non-Stick Ceramic Cookware Set": "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?w=500&auto=format&fit=crop&q=70",
                "Programmable Coffee Maker 12-Cup": "https://images.unsplash.com/photo-1517256064527-09c53b2d0bc6?w=500&auto=format&fit=crop&q=70",
                "Bamboo Cutting Board Set": "https://images.unsplash.com/photo-1589135306090-e82773586bbc?w=500&auto=format&fit=crop&q=70",
                "Cast Iron Dutch Oven 6-Qt": "https://images.unsplash.com/photo-1585238342024-78d387f4a707?w=500&auto=format&fit=crop&q=70",
                "Electric Kettle Temperature Control": "https://images.unsplash.com/photo-1594385208974-2e75f9d3ab28?w=500&auto=format&fit=crop&q=70",
                "Silicone Kitchen Utensil Set": "https://images.unsplash.com/photo-1593113630400-ea4288922497?w=500&auto=format&fit=crop&q=70",
                "The Art of Clear Thinking": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500&auto=format&fit=crop&q=70",
                "JavaScript: The Definitive Guide": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500&auto=format&fit=crop&q=70",
                "Atomic Habits Hardcover": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500&auto=format&fit=crop&q=70",
                "World Atlas 2026 Edition": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=500&auto=format&fit=crop&q=70",
                "Creative Photography Masterclass": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&auto=format&fit=crop&q=70",
                "The Lean Startup": "https://images.unsplash.com/photo-1629197520635-16314f7b4946?w=500&auto=format&fit=crop&q=70",
                "Vitamin C Brightening Serum": "https://images.unsplash.com/photo-1608248597481-496100c80836?w=500&auto=format&fit=crop&q=70",
                "Hydrating Face Moisturizer SPF 30": "https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=500&auto=format&fit=crop&q=70",
                "Argan Oil Hair Treatment": "https://images.unsplash.com/photo-1526947425960-945c6e72858f?w=500&auto=format&fit=crop&q=70",
                "Charcoal Purifying Face Mask": "https://images.unsplash.com/photo-1567894340315-735d7c361db0?w=500&auto=format&fit=crop&q=70",
                "Electric Precision Trimmer": "https://images.unsplash.com/photo-1621607512214-68297480165e?w=500&auto=format&fit=crop&q=70",
                "Natural Deodorant Stick": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop&q=70",
                "Yoga Mat Extra Thick 6mm": "https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=500&auto=format&fit=crop&q=70",
                "Adjustable Dumbbell Set 25lb": "https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?w=500&auto=format&fit=crop&q=70",
                "Insulated Water Bottle 32oz": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=500&auto=format&fit=crop&q=70",
                "Camping Tent 4-Person": "https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?w=500&auto=format&fit=crop&q=70",
                "Resistance Bands Set": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=500&auto=format&fit=crop&q=70",
                "GPS Running Watch": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=500&auto=format&fit=crop&q=70",
                "Building Blocks Creative Set 1000pc": "https://images.unsplash.com/photo-1566698627439-c443b192d755?w=500&auto=format&fit=crop&q=70",
                "Strategy Board Game Collection": "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=500&auto=format&fit=crop&q=70",
                "Remote Control Racing Drone": "https://images.unsplash.com/photo-1527977966376-1c8408f9f108?w=500&auto=format&fit=crop&q=70",
                "Wooden Puzzle Brain Teaser Set": "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=500&auto=format&fit=crop&q=70",
                "Interactive Learning Tablet Kids": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500&auto=format&fit=crop&q=70",
                "Dash Camera 4K Night Vision": "https://images.unsplash.com/photo-1508962914676-134849a727f0?w=500&auto=format&fit=crop&q=70",
                "Portable Tire Inflator Digital": "https://images.unsplash.com/photo-1563720223185-11003d516935?w=500&auto=format&fit=crop&q=70",
                "LED Headlight Bulbs H11 Pair": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=500&auto=format&fit=crop&q=70",
                "Car Phone Mount Magnetic": "https://images.unsplash.com/photo-1522273400909-fd1a8f77637e?w=500&auto=format&fit=crop&q=70",
                "All-Weather Floor Mats Set": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=500&auto=format&fit=crop&q=70",
                "Organic Cold Brew Coffee Concentrate": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=500&auto=format&fit=crop&q=70",
                "Dark Chocolate Truffle Collection": "https://images.unsplash.com/photo-1548907040-4d42b52125b0?w=500&auto=format&fit=crop&q=70",
                "Extra Virgin Olive Oil 1L": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&auto=format&fit=crop&q=70",
                "Matcha Green Tea Powder Premium": "https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=500&auto=format&fit=crop&q=70",
                "Mixed Nuts Trail Mix 2lb": "https://images.unsplash.com/photo-1590080875515-8a3a8dc5735e?w=500&auto=format&fit=crop&q=70",
                "Automatic Pet Feeder Smart WiFi": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=500&auto=format&fit=crop&q=70",
                "Orthopedic Dog Bed Large": "https://images.unsplash.com/photo-1576201836106-db1758fd1c97?w=500&auto=format&fit=crop&q=70",
                "Interactive Cat Toy Laser": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=500&auto=format&fit=crop&q=70",
                "Retractable Dog Leash 16ft": "https://images.unsplash.com/photo-1535930891776-0c2dfb7fda1a?w=500&auto=format&fit=crop&q=70",
                "Grain-Free Dog Treats 1lb": "https://images.unsplash.com/photo-1608454367599-c11394f0a021?w=500&auto=format&fit=crop&q=70",
                "Digital Blood Pressure Monitor": "https://images.unsplash.com/photo-1603398938378-e54eab446dde?w=500&auto=format&fit=crop&q=70",
                "Foam Roller Muscle Recovery": "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=500&auto=format&fit=crop&q=70",
                "Vitamin D3 5000 IU 360ct": "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=500&auto=format&fit=crop&q=70",
                "Meditation Cushion Zafu": "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=500&auto=format&fit=crop&q=70",
                "Pulse Oximeter Fingertip": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=70",
                "Solar Pathway Lights 12-Pack": "https://images.unsplash.com/photo-1508849789987-4e5333c12b78?w=500&auto=format&fit=crop&q=70",
                "Stainless Steel Garden Tool Set": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500&auto=format&fit=crop&q=70",
                "Portable Hammock with Stand": "https://images.unsplash.com/photo-1581579438747-1dc8d17bbce4?w=500&auto=format&fit=crop&q=70",
                "Self-Watering Planter Large": "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=500&auto=format&fit=crop&q=70",
                "Outdoor String Lights 48ft": "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500&auto=format&fit=crop&q=70",
                "Ergonomic Office Chair Mesh": "https://images.unsplash.com/photo-1505797149-43b0069ec26b?w=500&auto=format&fit=crop&q=70",
                "Standing Desk Converter 36\"": "https://images.unsplash.com/photo-1595853035070-59a39fe84de3?w=500&auto=format&fit=crop&q=70",
                "Wireless Presentation Clicker": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&auto=format&fit=crop&q=70",
                "Document Scanner Portable": "https://images.unsplash.com/photo-1618005182384-a83a8bd57ba2?w=500&auto=format&fit=crop&q=70",
                "Noise Machine White Sound": "https://images.unsplash.com/photo-1558089687-f282ffcbd1d5?w=500&auto=format&fit=crop&q=70",
                "Cordless Drill Driver 20V": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=500&auto=format&fit=crop&q=70",
                "LED Work Light Rechargeable": "https://images.unsplash.com/photo-1531844251246-9a1bfaae0d67?w=500&auto=format&fit=crop&q=70",
                "Digital Laser Measure 165ft": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=500&auto=format&fit=crop&q=70",
                "Smart Thermostat WiFi Enabled": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=500&auto=format&fit=crop&q=70",
                "Multi-Tool Pliers 18-in-1": "https://images.unsplash.com/photo-1586864387967-d02ef85d93e8?w=500&auto=format&fit=crop&q=70",
                "Baby Monitor Camera WiFi 1080p": "https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=500&auto=format&fit=crop&q=70",
                "Organic Baby Wipes 720ct": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500&auto=format&fit=crop&q=70",
                "Convertible Car Seat All-in-One": "https://images.unsplash.com/photo-1595152772835-219674b2a8a6?w=500&auto=format&fit=crop&q=70",
                "Baby Carrier Ergonomic Wrap": "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=500&auto=format&fit=crop&q=70",
                "Silicone Baby Feeding Set": "https://images.unsplash.com/photo-1591946614720-90a587da4a36?w=500&auto=format&fit=crop&q=70",
            }

            product = Product(
                category_id=cat.id,
                name=display_name,
                slug=f"{display_name.lower().replace(' ', '-').replace('\"', '')}-{i}",
                description=fake.paragraph(),
                brand=brand_name,
                image_url=product_images.get(prod_name, f"https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=70"),
                price=price,
                stock=initial_stock,
                is_active=is_active,
                is_deleted=is_deleted,
                deleted_at=deleted_at,
            )
            db.add(product)
            products.append(product)
        await db.commit()
        print(f"Seeded {len(products)} products.")

        # Seed initial stock logs for products
        for prod in products:
            hist = InventoryHistory(
                product_id=prod.id,
                old_stock=0,
                new_stock=prod.stock,
                reason="initial_stock_receipt",
            )
            db.add(hist)
        await db.commit()
        print("Seeded product initial stock histories.")

        # 4. Seed Orders (300)
        active_users = [u for u in users if not u.is_deleted]
        active_products = [p for p in products if not p.is_deleted]
        orders = []

        for _ in range(300):
            user = random.choice(active_users)
            order_date = fake.date_time_between(
                start_date="-45d", end_date="now", tzinfo=datetime.UTC
            )
            status = random.choice(["pending", "completed", "shipped", "cancelled"])

            # 1 to 4 items per order
            num_items = random.randint(1, 4)
            selected_prods = random.sample(active_products, num_items)

            subtotal = Decimal("0.00")
            order_items = []

            for prod in selected_prods:
                qty = random.randint(1, 3)
                unit_price = prod.price
                item_subtotal = unit_price * qty
                subtotal += item_subtotal

                order_item = OrderItem(
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=unit_price,
                    subtotal=item_subtotal,
                )
                order_items.append(order_item)

                # Deduct inventory stock
                old_stock = prod.stock
                if prod.stock >= qty:
                    prod.stock -= qty
                else:
                    prod.stock = 0

                # Log inventory history entry
                hist = InventoryHistory(
                    product_id=prod.id,
                    old_stock=old_stock,
                    new_stock=prod.stock,
                    reason="customer_order_sale",
                )
                db.add(hist)

            discount = Decimal(
                f"{random.choice([0.00, 0.00, 0.00, 5.00, 10.00, 15.00]):.2f}"
            )
            tax = Decimal(f"{(subtotal * Decimal('0.08')):.2f}")
            total = subtotal + tax - discount
            if total < 0:
                total = Decimal("0.00")

            order = Order(
                user_id=user.id,
                status=status,
                subtotal=subtotal,
                tax=tax,
                discount=discount,
                total=total,
                created_at=order_date,
                updated_at=order_date,
            )
            # Link items to order
            for item in order_items:
                order.items.append(item)

            db.add(order)
            orders.append(order)
        await db.commit()
        print(f"Seeded {len(orders)} orders.")

        # 5. Seed Payments (One per Order)
        for order in orders:
            if order.status != "cancelled" or random.random() < 0.2:
                status = (
                    "completed"
                    if order.status in ["completed", "shipped"]
                    else random.choice(["pending", "completed", "failed"])
                )
                pay = Payment(
                    order_id=order.id,
                    payment_provider=random.choice(["stripe", "paypal", "google_pay"]),
                    payment_id=f"pay_{fake.md5()[:18]}",
                    status=status,
                    amount=order.total,
                    currency="USD",
                    created_at=order.created_at,
                )
                db.add(pay)
        await db.commit()
        print("Seeded order payments.")

        # 6. Seed Reviews (500)
        reviews = []
        for _ in range(500):
            user = random.choice(active_users)
            prod = random.choice(active_products)
            review = Review(
                user_id=user.id,
                product_id=prod.id,
                rating=random.randint(1, 5),
                review=fake.text(max_nb_chars=180),
            )
            db.add(review)
            reviews.append(review)
        await db.commit()
        print(f"Seeded {len(reviews)} reviews.")

        # 7. Seed Recommendations
        for user in active_users:
            rec_prods = random.sample(active_products, 5)
            for prod in rec_prods:
                rec = Recommendation(
                    user_id=user.id,
                    product_id=prod.id,
                    score=round(random.uniform(0.4, 0.99), 4),
                )
                db.add(rec)
        await db.commit()
        print("Seeded product recommendations.")

        # 8. Seed Segments
        cohorts = [
            "VIP",
            "High Value",
            "Window Shopper",
            "Frequent Buyer",
            "Churn Risk",
        ]
        for user in active_users:
            if random.random() < 0.85:
                seg = Segment(
                    user_id=user.id,
                    segment_name=random.choice(cohorts),
                    confidence=round(random.uniform(0.55, 1.0), 2),
                )
                db.add(seg)
        await db.commit()
        print("Seeded customer segments.")

        # 9. Seed Events (1000)
        session_ids = [uuid.uuid4() for _ in range(120)]
        events = []
        event_types = ["page_view", "view_item", "add_to_cart", "purchase"]
        pages = ["/home", "/search", "/cart", "/checkout", "/products/details"]

        for _ in range(1000):
            event_user: User | None = (
                random.choice(active_users) if random.random() < 0.75 else None
            )
            session_id = random.choice(session_ids)
            event_type = random.choice(event_types)
            page = random.choice(pages)
            event_prod: Product | None = (
                random.choice(active_products)
                if event_type in ["view_item", "add_to_cart"]
                else None
            )

            meta = {}
            if event_prod:
                meta = {
                    "product_slug": event_prod.slug,
                    "product_name": event_prod.name,
                }
            elif event_type == "page_view":
                meta = {"referrer_host": fake.domain_name()}

            timestamp = fake.date_time_between(
                start_date="-30d", end_date="now", tzinfo=datetime.UTC
            )

            event = Event(
                user_id=event_user.id if event_user else None,
                session_id=session_id,
                event_type=event_type,
                page=page,
                product_id=event_prod.id if event_prod else None,
                metadata_=meta,
                timestamp=timestamp,
            )
            db.add(event)
            events.append(event)
        await db.commit()
        print(f"Seeded {len(events)} events.")
        print("Database seeding completed successfully!")


async def main() -> None:
    # Ensure database connections are correctly closed
    await seed_database()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
