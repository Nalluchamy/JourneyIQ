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

        # 3. Seed Products (100) with highly specific real-world products and exact matching Unsplash photos
        # Curated catalog: (Category Name, Product Name, Brand Name, Price, Image URL)
        curated_catalog = [
            # Electronics
            ("Electronics", "Sony WH-1000XM4 Wireless Headphones", "Sony", 248.00, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80"),
            ("Electronics", "Apple AirPods Pro (2nd Gen)", "Apple", 199.00, "https://images.unsplash.com/photo-1588449668338-d134ae7f3fda?w=600&auto=format&fit=crop&q=80"),
            ("Electronics", "Samsung 55\" QLED 4K Smart TV", "Samsung", 547.99, "https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=600&auto=format&fit=crop&q=80"),
            ("Electronics", "JBL Flip 6 Portable Bluetooth Speaker", "JBL", 99.95, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&auto=format&fit=crop&q=80"),
            ("Electronics", "Logitech MX Master 3S Wireless Mouse", "Logitech", 99.99, "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop&q=80"),
            ("Electronics", "Keychron K2 Mechanical Keyboard", "Keychron", 79.99, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&auto=format&fit=crop&q=80"),
            ("Electronics", "Anker PowerCore 26800mAh Power Bank", "Anker", 59.99, "https://images.unsplash.com/photo-1609592424109-dd25567b45f4?w=600&auto=format&fit=crop&q=80"),
            # Apparel & Fashion
            ("Apparel & Fashion", "Nike Air Zoom Pegasus 40 Shoes", "Nike", 129.99, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80"),
            ("Apparel & Fashion", "Levi's 511 Slim Fit Denim Jeans", "Levi's", 69.50, "https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&auto=format&fit=crop&q=80"),
            ("Apparel & Fashion", "Ralph Lauren Classic Cotton Polo", "Ralph Lauren", 85.00, "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=600&auto=format&fit=crop&q=80"),
            ("Apparel & Fashion", "Herschel Heritage Canvas Backpack", "Herschel", 59.99, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80"),
            ("Apparel & Fashion", "Ray-Ban Classic Wayfarer Sunglasses", "Ray-Ban", 163.00, "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&auto=format&fit=crop&q=80"),
            # Home & Kitchen
            ("Home & Kitchen", "Bodum Chambord 8-Cup French Press", "Bodum", 39.99, "https://images.unsplash.com/photo-1577968897966-3d4325b36b61?w=600&auto=format&fit=crop&q=80"),
            ("Home & Kitchen", "Cuisinart 14-Cup Drip Coffee Maker", "Cuisinart", 99.95, "https://images.unsplash.com/photo-1517256064527-09c53b2d0bc6?w=600&auto=format&fit=crop&q=80"),
            ("Home & Kitchen", "Lodge 6-Quart Cast Iron Dutch Oven", "Lodge", 79.90, "https://images.unsplash.com/photo-1585238342024-78d387f4a707?w=600&auto=format&fit=crop&q=80"),
            # Books & Media
            ("Books & Media", "Atomic Habits by James Clear", "Penguin Books", 16.20, "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80"),
            ("Books & Media", "The Lean Startup by Eric Ries", "Crown Business", 17.99, "https://images.unsplash.com/photo-1629197520635-16314f7b4946?w=600&auto=format&fit=crop&q=80"),
            # Beauty & Personal Care
            ("Beauty & Personal Care", "The Ordinary Niacinamide Serum", "The Ordinary", 8.90, "https://images.unsplash.com/photo-1608248597481-496100c80836?w=600&auto=format&fit=crop&q=80"),
            ("Beauty & Personal Care", "CeraVe AM Moisturizing Lotion", "CeraVe", 15.99, "https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?w=600&auto=format&fit=crop&q=80"),
            # Sports & Outdoors
            ("Sports & Outdoors", "Hydro Flask 32oz Water Bottle", "Hydro Flask", 44.95, "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&auto=format&fit=crop&q=80"),
            ("Sports & Outdoors", "Bowflex SelectTech 552 Dumbbells", "Bowflex", 429.00, "https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?w=600&auto=format&fit=crop&q=80"),
            # Toys & Games
            ("Toys & Games", "LEGO Star Wars Millennium Falcon", "LEGO", 159.99, "https://images.unsplash.com/photo-1566698627439-c443b192d755?w=600&auto=format&fit=crop&q=80"),
            ("Toys & Games", "DJI Mini 4 Pro Camera Drone", "DJI", 759.00, "https://images.unsplash.com/photo-1527977966376-1c8408f9f108?w=600&auto=format&fit=crop&q=80"),
            # Automotive
            ("Automotive", "Vantrue N4 3-Channel 4K Dash Cam", "Vantrue", 199.99, "https://images.unsplash.com/photo-1508962914676-134849a727f0?w=600&auto=format&fit=crop&q=80"),
            # Grocery & Gourmet
            ("Grocery & Gourmet", "Lindt Excellence Dark Chocolate Bar", "Lindt", 4.29, "https://images.unsplash.com/photo-1548907040-4d42b52125b0?w=600&auto=format&fit=crop&q=80"),
            # Office Products
            ("Office Products", "Herman Miller Aeron Office Chair", "Herman Miller", 995.00, "https://images.unsplash.com/photo-1580481072645-022f9a6dbf27?w=600&auto=format&fit=crop&q=80"),
            # Tools & Home Improvement
            ("Tools & Home Improvement", "DeWalt 20V Cordless Drill Driver", "DeWalt", 99.00, "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=600&auto=format&fit=crop&q=80"),
            ("Tools & Home Improvement", "Nest Learning Smart Thermostat", "Nest", 249.00, "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600&auto=format&fit=crop&q=80"),
            # Baby Care
            ("Baby Care", "Graco 4Ever DLX 4-in-1 Car Seat", "Graco", 329.97, "https://images.unsplash.com/photo-1595152772835-219674b2a8a6?w=600&auto=format&fit=crop&q=80")
        ]

        # Build category name -> category object lookup
        cat_lookup = {c.name: c for c in categories}

        products = []
        for i in range(100):
            entry = curated_catalog[i % len(curated_catalog)]
            cat_name, prod_name, brand_name, base_price, img_url = entry
            cat = cat_lookup.get(cat_name, random.choice(categories))

            is_deleted = i < 10  # 10% soft deleted
            deleted_at = datetime.datetime.now(datetime.UTC) if is_deleted else None
            is_active = i >= 10

            initial_stock = random.randint(2, 120)
            # Add slight price fluctuation for variants
            fluctuation = random.uniform(-10.0, 10.0) if i >= len(curated_catalog) else 0.0
            price = Decimal(f"{max(2.99, float(base_price) + fluctuation):.2f}")
            display_name = prod_name if i < len(curated_catalog) else f"{prod_name} v{i // len(curated_catalog) + 1}"

            product = Product(
                category_id=cat.id,
                name=display_name,
                slug=f"{display_name.lower().replace(' ', '-').replace('\"', '').replace('(', '').replace(')', '')}-{i}",
                description=fake.paragraph(),
                brand=brand_name,
                image_url=img_url,
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
