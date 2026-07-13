import asyncio
import datetime
import random
import uuid
import os
from decimal import Decimal
from faker import Faker
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine
from app.db.base_class import BaseModel
from app.models import (
    Category,
    Event,
    InventoryHistory,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductVariant,
    ProductImage,
    Recommendation,
    Review,
    Segment,
    User,
)

fake = Faker()

# Category mapping
CATEGORIES_MAPPING = {
    "Mobiles": "Smartphones and mobile devices",
    "Laptops": "Notebooks, ultrabooks and laptops",
    "Audio": "Headphones, earphones and speakers",
    "Wearables": "Smartwatches and fitness trackers",
    "Fashion": "Apparel, clothing, shoes and bags",
    "Home & Kitchen": "Cookware, appliances and home decor",
    "Sports": "Fitness gear, activewear and equipment",
    "Gaming": "Consoles, accessories and video games",
    "Books": "Fiction, non-fiction and educational books"
}

# Real-world brands and model templates (Prices are in USD)
BRANDS_CATALOG = {
    "Mobiles": [
        ("Apple", "iPhone 16 Pro", ["Black", "White", "Titanium"], ["128GB", "256GB", "512GB"], ["8GB"], 999.00, "Best Seller"),
        ("Apple", "iPhone 15 Plus", ["Blue", "Black", "Yellow"], ["128GB", "256GB"], ["6GB"], 799.00, "New Arrival"),
        ("Samsung", "Galaxy S25 Ultra", ["Titanium Grey", "Titanium Black"], ["256GB", "512GB"], ["12GB"], 1299.00, "Top Rated"),
        ("Samsung", "Galaxy A55 5G", ["Awesome Navy", "Awesome Ice"], ["128GB", "256GB"], ["8GB"], 399.00, "Trending"),
        ("OnePlus", "OnePlus 12", ["Flowy Emerald", "Silky Black"], ["256GB", "512GB"], ["16GB"], 699.00, "Editor's Choice"),
        ("OnePlus", "Nord CE 4", ["Celadon Marble", "Dark Chrome"], ["128GB"], ["8GB"], 249.00, "Fast Selling"),
        ("Nothing", "Phone (2a)", ["White", "Black"], ["128GB", "256GB"], ["8GB", "12GB"], 299.00, "New Arrival"),
        ("Samsung", "Galaxy Z Flip 6", ["Blue", "Mint", "Yellow"], ["256GB"], ["12GB"], 1099.00, "Limited Offer")
    ],
    "Laptops": [
        ("Apple", "MacBook Air M3", ["Space Grey", "Silver"], ["256GB", "512GB"], ["8GB", "16GB"], 1099.00, "Best Seller"),
        ("Apple", "MacBook Pro M3 Pro", ["Space Black", "Silver"], ["512GB", "1TB"], ["18GB", "36GB"], 1999.00, "Top Rated"),
        ("Dell", "XPS 13 OLED", ["Platinum Silver"], ["512GB", "1TB"], ["16GB"], 1399.00, "Editor's Choice"),
        ("HP", "Spectre x360", ["Nightfall Black"], ["1TB"], ["16GB"], 1499.00, "Trending"),
        ("Lenovo", "ThinkPad X1 Carbon Gen 12", ["Deep Black"], ["512GB", "1TB"], ["32GB"], 1799.00, "Best Seller"),
        ("ASUS", "Vivobook 15 OLED", ["Quiet Blue", "Indie Black"], ["512GB"], ["8GB", "16GB"], 599.00, "Fast Selling"),
        ("ASUS", "ROG Zephyrus G16", ["Eclipse Grey"], ["1TB"], ["16GB", "32GB"], 1899.00, "Limited Offer"),
        ("Lenovo", "IdeaPad Slim 3", ["Arctic Grey"], ["512GB"], ["8GB"], 379.00, "New Arrival")
    ],
    "Audio": [
        ("Sony", "WH-1000XM5 Headphones", ["Black", "Silver"], None, None, 299.90, "Best Seller"),
        ("Sony", "WH-CH720N Wireless Headphones", ["Black", "Blue", "White"], None, None, 99.90, "Trending"),
        ("Apple", "AirPods Pro (2nd Gen)", ["White"], None, None, 249.00, "Best Seller"),
        ("Boat", "Airdopes 141", ["Active Black", "Bold Blue"], None, None, 19.99, "Fast Selling"),
        ("Boat", "Stone 350 Speaker", ["Black", "Blue", "Red"], None, None, 24.99, "New Arrival"),
        ("Sony", "WF-C700N Earbuds", ["Black", "Sage Green"], None, None, 79.90, "Editor's Choice"),
        ("JBL", "Flip 6 Bluetooth Speaker", ["Black", "Blue", "Squad"], None, None, 119.99, "Top Rated")
    ],
    "Wearables": [
        ("Apple", "Watch Series 9 GPS", ["Midnight", "Starlight"], ["41mm", "45mm"], None, 399.00, "Best Seller"),
        ("Samsung", "Galaxy Watch 6", ["Graphite", "Silver"], ["40mm", "44mm"], None, 299.00, "Trending"),
        ("Titan", "Smart Watch Touch", ["Black", "Rose Gold"], ["Classic"], None, 79.95, "New Arrival"),
        ("Fastrack", "Limitless FS1", ["Black", "Blue"], ["Sporty"], None, 24.99, "Fast Selling"),
        ("OnePlus", "Watch 2", ["Radiant Steel", "Black Steel"], ["46mm"], None, 249.99, "Editor's Choice"),
        ("Apple", "Watch Ultra 2", ["Titanium"], ["49mm"], None, 799.00, "Top Rated")
    ],
    "Fashion": [
        ("Nike", "Air Zoom Pegasus 41 Shoes", ["White/Blue", "Black/Grey"], ["7", "8", "9", "10"], None, 129.99, "Best Seller"),
        ("Adidas", "Ultraboost Light Shoes", ["Core Black", "Cloud White"], ["8", "9", "10"], None, 189.99, "Top Rated"),
        ("Puma", "Velocity Nitro 2 Shoes", ["Red Blast", "Black"], ["7", "8", "9", "10"], None, 109.99, "Trending"),
        ("Levi's", "511 Slim Fit Jeans", ["Dark Blue", "Mid Blue", "Black"], ["30", "32", "34", "36"], None, 59.99, "Best Seller"),
        ("Nike", "Classic Dri-FIT Polo", ["Black", "White", "Navy"], ["M", "L", "XL"], None, 34.99, "New Arrival"),
        ("Puma", "Classic Logo Hoodie", ["Black", "Grey"], ["S", "M", "L"], None, 49.99, "Trending"),
        ("Titan", "Neo Analog Watch", ["Silver Blue", "Classic Black"], ["Leather", "Metal"], None, 79.95, "Editor's Choice"),
        ("Fastrack", "Vibe Casual Bag", ["Black", "Olive"], ["Standard"], None, 29.99, "New Arrival")
    ],
    "Home & Kitchen": [
        ("Philips", "Air Fryer HD9252", ["Black"], None, None, 99.99, "Best Seller"),
        ("Bosch", "TrueMixx Pro Mixer", ["Black Chrome"], None, None, 89.99, "Top Rated"),
        ("Prestige", "Omega Select Plus Cookware", ["Black/Grey"], None, None, 39.99, "Best Seller"),
        ("Milton", "Thermosteel Duo Bottle", ["Silver", "Red", "Black"], ["500ml", "1000ml"], None, 14.99, "Fast Selling"),
        ("LG", "28L Convection Microwave", ["Black"], None, None, 149.99, "Trending"),
        ("Bosch", "Dishwasher SMS66GI01I", ["Silver"], None, None, 499.00, "Editor's Choice"),
        ("Prestige", "Picasso Induction Cooktop", ["Black"], None, None, 49.99, "New Arrival")
    ],
    "Sports": [
        ("Adidas", "Tiro Track Jacket", ["Black/White", "Navy/White"], ["M", "L", "XL"], None, 49.99, "Best Seller"),
        ("Nike", "Gym Elemental Backpack", ["Black", "Pink"], None, None, 24.99, "New Arrival"),
        ("Puma", "Core Yoga Mat", ["Purple", "Grey"], None, None, 19.99, "Trending"),
        ("Adidas", "Sports Duffle Bag", ["Black"], None, None, 29.99, "Fast Selling"),
        ("Nike", "Air Zoom Structure Shoes", ["Black"], ["8", "9", "10"], None, 119.99, "Top Rated")
    ],
    "Gaming": [
        ("Sony", "PlayStation 5 Console", ["White"], ["Standard Edition", "Digital Edition"], None, 499.99, "Best Seller"),
        ("Sony", "DualSense Controller PS5", ["White", "Midnight Black", "Cosmic Red"], None, None, 69.99, "Trending"),
        ("ASUS", "ROG Ally Gaming Handheld", ["White"], ["512GB"], None, 599.99, "Editor's Choice"),
        ("Lenovo", "Legion M300 RGB Mouse", ["Black"], None, None, 19.99, "New Arrival")
    ],
    "Books": [
        ("Penguin Books", "Atomic Habits (James Clear)", ["Paperback"], None, None, 16.20, "Best Seller"),
        ("Penguin Books", "The Psychology of Money", ["Paperback"], None, None, 14.99, "Top Rated"),
        ("Crown Business", "The Lean Startup (Eric Ries)", ["Hardcover", "Paperback"], None, None, 17.99, "Trending"),
        ("Penguin Books", "Deep Work (Cal Newport)", ["Paperback"], None, None, 15.99, "Editor's Choice")
    ]
}

def get_category_image(category, brand):
    """Map each category to its high-quality AI-generated product PNG render."""
    if category == "Mobiles":
        if brand == "Apple":
            return "/images/products/iphone_16_pro.png"
        return "/images/products/galaxy_s25.png"
    elif category == "Laptops":
        return "/images/products/macbook_pro.png"
    elif category == "Audio":
        return "/images/products/wireless_headphones.png"
    elif category == "Wearables":
        return "/images/products/smartwatch.png"
    elif category == "Fashion":
        return "/images/products/running_shoes.png"
    elif category == "Home & Kitchen":
        return "/images/products/air_fryer.png"
    elif category == "Sports":
        return "/images/products/yoga_mat.png"
    elif category == "Gaming":
        return "/images/products/ps5_console.png"
    elif category == "Books":
        return "/images/products/books_stack.png"
    return "/images/products/iphone_16_pro.png"

# Custom specifications generator
def generate_specs(category, name, brand, variant_options):
    color = variant_options.get("color", "N/A")
    storage = variant_options.get("storage", "N/A")
    ram = variant_options.get("ram", "N/A")
    
    if category == "Mobiles":
        return {
            "Display": "6.7-inch Super Retina XDR OLED" if brand == "Apple" else "6.8-inch Dynamic AMOLED 2X",
            "Processor": "Apple A18 Pro" if brand == "Apple" else "Snapdragon 8 Gen 4",
            "RAM": ram if ram != "N/A" else "8 GB",
            "Storage": storage if storage != "N/A" else "128 GB",
            "Battery": "4685 mAh" if brand == "Apple" else "5000 mAh",
            "Camera": "48 MP Main + 12 MP Ultrawide" if brand == "Apple" else "200 MP Main + 50 MP Telephoto",
            "Weight": "199 g",
            "Warranty": "1 Year Brand Warranty",
            "Connectivity": "5G, Wi-Fi 7, Bluetooth 5.4, USB-C"
        }
    elif category == "Laptops":
        return {
            "Display": "13.6-inch Liquid Retina Display" if brand == "Apple" else "15.6-inch Full HD OLED",
            "Processor": "Apple M3 Chip" if brand == "Apple" else "Intel Core Ultra 7",
            "RAM": ram if ram != "N/A" else "16 GB",
            "Storage": storage if storage != "N/A" else "512 GB SSD",
            "Battery": "18 hours battery life" if brand == "Apple" else "75 Whrs Battery",
            "Weight": "1.24 kg" if brand == "Apple" else "1.5 kg",
            "Warranty": "1 Year Limited Warranty",
            "Graphics": "10-core GPU" if brand == "Apple" else "Intel Arc Graphics"
        }
    elif category == "Audio":
        return {
            "Audio Driver": "40 mm Dynamic Driver" if "Headphones" in name else "12 mm Dynamic Driver",
            "Active Noise Cancellation": "Yes, Custom HD Noise Cancelling Processor QN1" if brand == "Sony" else "Yes, Adaptive ANC",
            "Battery Life": "Up to 30 hours" if "Headphones" in name else "Up to 6 hours (24 hours with case)",
            "Bluetooth Version": "Bluetooth 5.2",
            "Water Resistance": "IPX4 sweat resistant",
            "Warranty": "1 Year Manufacturer Warranty"
        }
    elif category == "Wearables":
        return {
            "Display": "Always-On Retina LTPO OLED",
            "Case Size": variant_options.get("storage", "45 mm"),
            "Sensors": "Heart Rate, ECG, Blood Oxygen, Temperature",
            "Battery Life": "Up to 36 hours" if "Ultra" in name else "Up to 18 hours",
            "Water Resistance": "Swimproof, WR50",
            "Warranty": "1 Year Brand Warranty"
        }
    elif category == "Fashion":
        return {
            "Material": "100% Breathable Mesh" if "Shoes" in name else ("100% Cotton" if "Polo" in name or "Hoodie" in name else "Premium Denim"),
            "Size": variant_options.get("storage", "M"),
            "Color": color,
            "Wash Care": "Machine wash cold" if "Jeans" in name or "Polo" in name else "Clean with soft damp cloth",
            "Warranty": "3 Months Brand Warranty"
        }
    elif category == "Home & Kitchen":
        return {
            "Power Consumption": "1400 W" if "Fryer" in name else "1000 W",
            "Capacity": "4.1 L" if "Fryer" in name else "28 L" if "Microwave" in name else "1000 ml",
            "Material": "Food Grade Stainless Steel" if "Bottle" in name else "Premium Thermoplastic",
            "Weight": "4.5 kg" if "Fryer" in name else "15 kg",
            "Warranty": "2 Years Manufacturer Warranty"
        }
    elif category == "Sports":
        return {
            "Material": "100% Recycled Polyester" if "Jacket" in name else "TPE Eco-Friendly Material",
            "Size": variant_options.get("storage", "L"),
            "Color": color,
            "Warranty": "1 Month Brand Warranty"
        }
    elif category == "Gaming":
        return {
            "Platform": "PlayStation 5" if "Controller" in name or "PS5" in name else "Windows 11 Home",
            "Storage": variant_options.get("storage", "825GB Custom SSD") if "Console" in name else "512GB SSD",
            "Connectivity": "Wireless, Bluetooth 5.1",
            "Warranty": "1 Year Sony Warranty"
        }
    elif category == "Books":
        return {
            "Format": color,
            "Author": "James Clear" if "Atomic" in name else "Morgan Housel" if "Psychology" in name else "Eric Ries" if "Startup" in name else "Cal Newport",
            "Publisher": "Penguin Random House",
            "Language": "English",
            "Page Count": "320 pages" if "Atomic" in name else "250 pages",
            "ISBN": f"978-{random.randint(1000000000, 9999999999)}"
        }
    return {"Warranty": "1 Year"}

# Clear Database
async def clear_database(db: AsyncSession) -> None:
    print("Clearing database tables...")
    await db.execute(delete(InventoryHistory))
    await db.execute(delete(Payment))
    await db.execute(delete(OrderItem))
    await db.execute(delete(Order))
    await db.execute(delete(Review))
    await db.execute(delete(Event))
    await db.execute(delete(Recommendation))
    await db.execute(delete(Segment))
    await db.execute(delete(ProductVariant))
    await db.execute(delete(ProductImage))
    await db.execute(delete(Product))
    await db.execute(delete(Category))
    await db.execute(delete(User))
    await db.commit()
    print("Database cleared.")

# Main seeding process
async def seed_database() -> None:
    async with AsyncSessionLocal() as db:
        await clear_database(db)
        print("Starting seeding of premium catalog...")
        
        # 1. Seed Categories
        categories_dict = {}
        for cat_name, cat_desc in CATEGORIES_MAPPING.items():
            category = Category(
                name=cat_name,
                slug=cat_name.lower().replace(" & ", "-").replace(" ", "-"),
                description=cat_desc,
                is_deleted=False
            )
            db.add(category)
            categories_dict[cat_name] = category
        await db.commit()
        print("Seeded categories.")
        
        # 2. Seed Users (100)
        users = []
        for i in range(100):
            role = "admin" if i == 0 else ("manager" if i == 1 else "customer")
            user = User(
                full_name=fake.name(),
                email=f"user_{i}@journeyiq.in" if role != "customer" else f"customer_{i}_{fake.unique.email()}",
                password_hash="pbkdf2:sha256:600000$mock_hash$abcdef1234567890",
                phone=fake.phone_number()[:20],
                role=role,
                is_active=True,
                is_deleted=False
            )
            db.add(user)
            users.append(user)
        await db.commit()
        print(f"Seeded {len(users)} users.")

        # 3. Seed Products (approx 100 products total, covering requested distribution)
        products = []
        target_counts = {
            "Mobiles": 15,
            "Laptops": 10,
            "Audio": 10,
            "Wearables": 8,
            "Fashion": 20,
            "Home & Kitchen": 15,
            "Sports": 10,
            "Gaming": 7,
            "Books": 5
        }
        
        product_counter = 0
        for cat_name, count in target_counts.items():
            category = categories_dict[cat_name]
            templates = BRANDS_CATALOG.get(cat_name, [])
            
            for index in range(count):
                template = templates[index % len(templates)]
                brand, model, colors, storages, rams, base_price, badge = template
                
                # Dynamic variations per model index to ensure 100 distinct products
                if index >= len(templates):
                    model = f"{model} Pro" if "Pro" not in model else f"{model} Max"
                    base_price = base_price * 1.15
                
                # Pricing variations (Convert USD to INR at 83.5 exchange rate)
                inr_base_price = base_price * 83.5
                mrp = Decimal(f"{inr_base_price:.2f}")
                discount_percent = random.choice([5, 8, 10, 12, 15, 0])
                savings = (mrp * Decimal(discount_percent) / Decimal(100)).quantize(Decimal("0.01"))
                selling_price = mrp - savings
                
                # Generate unique slug
                slug = f"{brand.lower()}-{model.lower().replace(' ', '-')}-{product_counter}"
                
                # Specifications
                specs = generate_specs(cat_name, model, brand, {
                    "color": colors[0] if colors else "N/A",
                    "storage": storages[0] if storages else "N/A",
                    "ram": rams[0] if rams else "N/A"
                })
                
                # Product name
                product_name = f"{brand} {model}"
                if colors and len(colors) == 1:
                    product_name += f" ({colors[0]})"
                
                # Category static PNG asset URL
                img_url = get_category_image(cat_name, brand)
                
                # Instantiate base product
                product = Product(
                    category_id=category.id,
                    name=product_name,
                    slug=slug,
                    description=f"Experience the peak of quality with the {brand} {model}. Combining state-of-the-art technology, user-centric engineering, and robust brand reliability, it is designed to fit your professional and daily workflows seamlessly.",
                    brand=brand,
                    image_url=img_url,
                    price=selling_price,
                    stock=random.randint(10, 100),
                    is_active=True,
                    is_deleted=False,
                    
                    # Normalized details
                    sku=f"PRD-{brand[:3].upper()}-{random.randint(100000, 999999)}",
                    barcode=f"89012{random.randint(1000000, 9999999)}",
                    warranty="1 Year Manufacturer Warranty" if cat_name in ["Mobiles", "Laptops", "Audio", "Wearables", "Gaming", "Home & Kitchen"] else "No Warranty",
                    seller="RetailIQ India Pvt Ltd" if random.random() < 0.8 else "SuperCom Retailers",
                    shipping_time=random.choice(["Same Day", "1-2 Days", "3-4 Days"]),
                    specifications=specs,
                    
                    # SEO
                    seo_title=f"Buy {brand} {model} Online - Best Prices & Offers",
                    meta_description=f"Get the brand new {brand} {model} at best retail discount rates. Check specs, reviews, and related variants.",
                    keywords=f"{brand}, {model}, {cat_name}, online shopping, offers",
                    alt_text=f"{brand} {model} primary hero catalog image render",
                    
                    # Badges & Status
                    badge=badge,
                    availability_status="In Stock" if index % 8 != 0 else "Only 3 Left",
                    mrp=mrp,
                    discount_percent=discount_percent,
                    savings=savings,
                    
                    # AI Metadata
                    sentiment_score=round(random.uniform(0.65, 0.95), 2),
                    popularity_score=round(random.uniform(0.70, 0.98), 2),
                    trend_score=round(random.uniform(0.55, 0.92), 2),
                    embedding_vector_id=f"vector_emb_{product_counter}"
                )
                
                db.add(product)
                products.append(product)
                
                # Flush to get product.id
                await db.flush()
                
                # Seed ProductImage table
                img_types = ["hero", "front", "side", "lifestyle", "feature"]
                for o_idx, img_type in enumerate(img_types):
                    p_img = ProductImage(
                        product_id=product.id,
                        image_url=img_url,
                        display_order=o_idx,
                        image_type=img_type,
                        alt_text=f"{brand} {model} {img_type} view render"
                    )
                    db.add(p_img)
                
                # Seed Variants (Colors & Storages) if applicable
                if colors and len(colors) > 1:
                    variant_counter = 0
                    for col in colors:
                        for stg in (storages if storages else ["Standard"]):
                            # Skip primary variant (first color + first storage) to avoid duplicating base product sku
                            if col == colors[0] and stg == (storages[0] if storages else "Standard"):
                                continue
                            
                            v_price = selling_price
                            if stg == "256GB":
                                v_price += Decimal("100.00")
                            elif stg == "512GB":
                                v_price += Decimal("250.00")
                                
                            variant = ProductVariant(
                                product_id=product.id,
                                sku=f"VAR-{brand[:3].upper()}-{random.randint(100000, 999999)}",
                                color=col,
                                storage=stg if stg != "Standard" else None,
                                ram=rams[0] if rams else None,
                                price=v_price,
                                stock=random.randint(5, 50),
                                barcode=f"89012{random.randint(1000000, 9999999)}",
                                is_active=True
                            )
                            db.add(variant)
                            variant_counter += 1
                
                product_counter += 1
                
        await db.commit()
        print(f"Seeded {len(products)} products and variants.")

        # 4. Seed Inventory stock logs
        for prod in products:
            hist = InventoryHistory(
                product_id=prod.id,
                old_stock=0,
                new_stock=prod.stock,
                reason="initial_stock_receipt",
            )
            db.add(hist)
        await db.commit()
        print("Seeded product inventory histories.")

        # 5. Seed Orders (200)
        active_users = [u for u in users if u.role == "customer"]
        orders = []
        for _ in range(200):
            user = random.choice(active_users)
            order_date = fake.date_time_between(start_date="-30d", end_date="now", tzinfo=datetime.UTC)
            status = random.choice(["completed", "shipped", "pending"])
            
            num_items = random.randint(1, 3)
            selected_prods = random.sample(products, num_items)
            
            subtotal = Decimal("0.00")
            order_items = []
            
            for prod in selected_prods:
                qty = random.randint(1, 2)
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
                
                # Adjust stock
                if prod.stock >= qty:
                    prod.stock -= qty
                else:
                    prod.stock = 0
            
            tax = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"))
            total = subtotal + tax
            
            order = Order(
                user_id=user.id,
                status=status,
                subtotal=subtotal,
                tax=tax,
                discount=Decimal("0.00"),
                total=total,
                created_at=order_date,
                updated_at=order_date
            )
            for item in order_items:
                order.items.append(item)
            db.add(order)
            orders.append(order)
        await db.commit()
        print(f"Seeded {len(orders)} orders.")

        # 6. Seed payments
        for order in orders:
            pay = Payment(
                order_id=order.id,
                payment_provider=random.choice(["stripe", "paypal"]),
                payment_id=f"pay_{fake.md5()[:18]}",
                status="completed",
                amount=order.total,
                currency="USD",
                created_at=order.created_at
            )
            db.add(pay)
        await db.commit()
        print("Seeded order payments.")

        # 7. Seed Reviews (500 Reviews with natural distribution & critical comments)
        reviews = []
        positive_comments = [
            "Excellent build quality and snappy performance.",
            "Fast shipping. The camera is absolutely stunning.",
            "Worth every dollar. Battery lasts easily for a full day.",
            "Great fits and comfortable materials.",
            "Sounds crisp and ANC works perfectly. Highly recommended!"
        ]
        constructive_comments = [
            "Good product but delivery took 5 days.",
            "Performance is fine but heats up slightly during charging.",
            "Average sound quality, battery could be better.",
            "The fit is slightly tight. Quality is decent though.",
            "Decent specs for the price but lacks premium finish."
        ]
        critical_comments = [
            "Disappointed. The battery drains too fast.",
            "Defective unit received. Screen has yellow tint. Returning.",
            "Not worth the price. Bluetooth keeps dropping.",
            "Material feels cheap. Did not match description.",
            "Lacks expected features. Returning immediately."
        ]
        
        for _ in range(500):
            user = random.choice(active_users)
            prod = random.choice(products)
            
            # Ratings distribution (approx 70% positive, 20% constructive, 10% critical)
            rand_val = random.random()
            if rand_val < 0.70:
                rating = random.choice([5, 4])
                comment = random.choice(positive_comments)
            elif rand_val < 0.90:
                rating = random.choice([3, 4])
                comment = random.choice(constructive_comments)
            else:
                rating = random.choice([1, 2])
                comment = random.choice(critical_comments)
                
            review = Review(
                user_id=user.id,
                product_id=prod.id,
                rating=rating,
                review=comment,
            )
            db.add(review)
            reviews.append(review)
        await db.commit()
        print(f"Seeded {len(reviews)} reviews with realistic sentiment.")

        # 8. Seed recommendations
        for user in active_users:
            rec_prods = random.sample(products, 5)
            for prod in rec_prods:
                rec = Recommendation(
                    user_id=user.id,
                    product_id=prod.id,
                    score=round(random.uniform(0.4, 0.99), 4),
                )
                db.add(rec)
        await db.commit()
        print("Seeded recommendations.")

        # 9. Seed Events
        session_ids = [uuid.uuid4() for _ in range(100)]
        event_types = ["page_view", "view_item", "add_to_cart", "purchase"]
        pages = ["/home", "/search", "/cart", "/checkout", "/products/details"]
        
        for _ in range(500):
            event_user = random.choice(active_users)
            session_id = random.choice(session_ids)
            event_type = random.choice(event_types)
            page = random.choice(pages)
            event_prod = random.choice(products) if event_type in ["view_item", "add_to_cart"] else None
            
            meta = {}
            if event_prod:
                meta = {
                    "product_slug": event_prod.slug,
                    "product_name": event_prod.name
                }
            timestamp = fake.date_time_between(start_date="-20d", end_date="now", tzinfo=datetime.UTC)
            
            event = Event(
                user_id=event_user.id,
                session_id=session_id,
                event_type=event_type,
                page=page,
                product_id=event_prod.id if event_prod else None,
                metadata_=meta,
                timestamp=timestamp
            )
            db.add(event)
        await db.commit()
        print("Seeded user telemetry events.")
        print("Premium catalog seeding completed successfully!")

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    await seed_database()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
