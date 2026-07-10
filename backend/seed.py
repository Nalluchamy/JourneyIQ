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

            product = Product(
                category_id=cat.id,
                name=display_name,
                slug=f"{display_name.lower().replace(' ', '-').replace('\"', '')}-{i}",
                description=fake.paragraph(),
                brand=brand_name,
                image_url=f"https://picsum.photos/seed/product{i}/400/300",
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
