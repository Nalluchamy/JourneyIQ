from typing import Any


# Comprehensive JourneyIQ project knowledge base
PROJECT_KNOWLEDGE = {
    "what_is": (
        "**JourneyIQ** is an AI-powered Personalized Retail Storefront platform built as a Data Science capstone project. "
        "It combines **Deep Learning (PyTorch NCF)**, **NLP Sentiment Analysis**, **Agentic AI Automation**, and a full-stack "
        "e-commerce experience to deliver hyper-personalized product recommendations to every customer.\n\n"
        "🔬 **Core AI/ML Features:**\n"
        "- Neural Collaborative Filtering (NCF) recommendation engine built with PyTorch\n"
        "- NLP-powered review sentiment analysis using VADER + TextBlob\n"
        "- Agentic AI Loop for autonomous dashboard monitoring and self-healing\n"
        "- Real-time behavioral event tracking and customer journey analytics\n\n"
        "🛒 **E-Commerce Features:**\n"
        "- Product catalog with advanced search, filtering, and sorting\n"
        "- Shopping cart, wishlist, and secure checkout with coupon support\n"
        "- Order management with invoice generation\n"
        "- AI Shopping Assistant chatbot (that's me! 🤖)\n\n"
        "📊 **Owner Dashboard:**\n"
        "- Real-time sales analytics and revenue tracking\n"
        "- Customer segmentation and churn prediction\n"
        "- Model performance monitoring with precision, recall, NDCG metrics\n"
        "- Sentiment intelligence with weekly trend analysis"
    ),
    "tech_stack": (
        "**JourneyIQ Tech Stack:**\n\n"
        "🔧 **Backend:** Python 3.13, FastAPI, SQLAlchemy (async), Uvicorn, Pydantic v2\n"
        "🎨 **Frontend:** React 18, TypeScript, Vite, TailwindCSS, React Query, Recharts\n"
        "🧠 **AI/ML:** PyTorch (NCF Model), VADER Sentiment, TextBlob NLP, Scikit-learn\n"
        "🗄️ **Database:** SQLite (dev) / PostgreSQL (prod), Alembic migrations\n"
        "🔐 **Auth:** JWT tokens with bcrypt password hashing, email verification flow\n"
        "📦 **DevOps:** Docker, Docker Compose, GitHub Actions CI/CD, NGINX reverse proxy\n"
        "📊 **Monitoring:** Structlog JSON logging, Prometheus metrics, health check endpoints\n"
        "🤖 **AI Providers:** NVIDIA NIM (Llama 3.1), OpenAI GPT-4o, Google Gemini (fallback chain)"
    ),
    "recommendation": (
        "**How JourneyIQ Recommendations Work:**\n\n"
        "The recommendation engine uses a **Neural Collaborative Filtering (NCF)** model built with PyTorch:\n\n"
        "1. **Data Collection** — User interactions (views, cart adds, purchases, reviews) are tracked as behavioral events\n"
        "2. **Feature Engineering** — User-item interaction matrices are built from event history\n"
        "3. **NCF Training** — A deep neural network learns latent user/item embeddings through matrix factorization + MLP layers\n"
        "4. **Hybrid Scoring** — Combines NCF scores with content-based similarity and popularity metrics\n"
        "5. **Cold-Start Fallback** — New users get trending/popular products until enough interaction data is collected\n\n"
        "📈 **Evaluation Metrics:** Precision@10, Recall@10, Hit Rate, NDCG, Coverage\n"
        "🔄 **Retraining:** Automated daily via APScheduler with model versioning and rollback support"
    ),
    "chatbot": (
        "**About the AI Shopping Assistant (Me! 🤖):**\n\n"
        "I am the JourneyIQ AI Shopping Assistant powered by the NLP pipeline. Here's what I can do:\n\n"
        "💬 **Conversational Shopping** — Ask me to recommend products, compare items, or find deals\n"
        "🔍 **Smart Search** — I search the real product database using intent classification and keyword extraction\n"
        "💰 **Budget Filtering** — Tell me your budget (e.g., 'laptops under ₹50,000') and I'll filter results\n"
        "📦 **Order Tracking** — I can guide you to check your order status\n"
        "🔥 **Trending Products** — Ask me what's popular right now\n"
        "❤️ **Wishlist Recommendations** — I can suggest products based on your saved wishlist\n"
        "⭐ **Review Insights** — I can summarize what customers think about products\n\n"
        "**Architecture:** Intent Classifier → Product Retriever → AI Provider Chain (NVIDIA → OpenAI → Local) → Response"
    ),
    "dashboard": (
        "**Owner Dashboard Features:**\n\n"
        "The admin dashboard provides a comprehensive business intelligence view:\n\n"
        "📊 **Analytics Tabs:**\n"
        "- **Overview** — KPI cards showing total revenue, orders, users, products\n"
        "- **Products** — Catalog management with inventory tracking and category distribution\n"
        "- **AI Models** — NCF model performance metrics, training history, inference stats\n"
        "- **Sentiment** — NLP-powered review analysis with weekly trend charts\n"
        "- **Customers** — Segment status (Active VIPs, At-Risk, New, Dormant)\n"
        "- **Sales** — Revenue operations with detailed transaction logs\n"
        "- **Agent Loop** — Agentic AI autonomous monitoring with self-healing actions\n"
        "- **Settings** — Platform configuration and ML pipeline controls\n\n"
        "🤖 **Agentic AI Loop:** Autonomously monitors system health, detects anomalies, "
        "triggers model retraining, and generates action reports — all without human intervention!"
    ),
    "sentiment": (
        "**NLP Sentiment Analysis:**\n\n"
        "JourneyIQ analyzes customer reviews using a dual-engine NLP pipeline:\n\n"
        "1. **VADER** (Valence Aware Dictionary) — Rule-based sentiment scoring optimized for social media text\n"
        "2. **TextBlob** — Pattern-based NLP for polarity and subjectivity analysis\n\n"
        "📊 **Outputs:**\n"
        "- Positive / Neutral / Negative percentage breakdown\n"
        "- Weekly and monthly sentiment trend tracking\n"
        "- Top customer praises and complaints extraction\n"
        "- Trending keyword cloud from review text\n"
        "- Average sentiment score per product for ranking"
    ),
    "agentic": (
        "**Agentic AI Loop:**\n\n"
        "The Agentic AI is an autonomous monitoring system that runs inside the Owner Dashboard:\n\n"
        "🔄 **How it works:**\n"
        "1. **Observe** — Continuously monitors system health, model metrics, and business KPIs\n"
        "2. **Analyze** — Detects anomalies like degraded model accuracy, low stock, or unusual traffic patterns\n"
        "3. **Decide** — Determines the best corrective action (retrain model, alert owner, adjust cache)\n"
        "4. **Act** — Executes the action autonomously and logs the result\n\n"
        "This is a key differentiator of JourneyIQ — it's not just a dashboard, it's a self-managing AI system!"
    ),
    "ml_dl": (
        "🔬 **Machine Learning & Deep Learning in JourneyIQ:**\n\n"
        "JourneyIQ uses Machine Learning (ML) and Deep Learning (DL) to drive its core features:\n\n"
        "1. **Deep Learning (PyTorch NCF):**\n"
        "   - **Model:** Neural Collaborative Filtering (NCF) built with PyTorch.\n"
        "   - **Function:** Learns user-item interaction embeddings to deliver highly personalized recommendation lists.\n"
        "   - **Training:** Runs an automated pipeline triggered daily or manually via the dashboard.\n\n"
        "2. **Natural Language Processing (NLP):**\n"
        "   - **Models:** VADER Sentiment Analysis and TextBlob.\n"
        "   - **Function:** Processes product reviews to calculate sentiment scores (polarity, subjectivity) and extracts top praises/complaints.\n\n"
        "3. **Agentic Automation:**\n"
        "   - **Function:** Monitors ML metrics (Precision, Recall, NDCG) and triggers autonomous self-healing retraining tasks."
    ),
}


class LocalAIProvider:
    """Offline template-based generator with full JourneyIQ project knowledge."""

    def generate_response(
        self,
        message: str,
        intent: str,
        products: list[dict[str, Any]],
        context: dict[str, Any]
    ) -> str:
        """
        Generate natural language replies based on query intent and retrieved items.
        Handles project-related questions, greetings, and product queries.
        """
        msg_lower = message.lower().strip()

        # Handle project-related questions
        if intent == "project_info":
            return self._handle_project_question(msg_lower)

        # Handle greetings and casual conversation
        if intent == "greeting":
            return self._handle_greeting(msg_lower)

        # Handle product-based intents
        if not products:
            # Check if it might be a project question that the classifier missed
            project_answer = self._try_project_fallback(msg_lower)
            if project_answer:
                return project_answer
            return (
                "I couldn't find products matching that query, but I can help with lots of things! "
                "Try asking me:\n"
                "- 🔍 **Product search**: 'Show me laptops' or 'Headphones under ₹5000'\n"
                "- 🔥 **Trending**: 'What's popular right now?'\n"
                "- ❓ **About JourneyIQ**: 'What is JourneyIQ?' or 'How does the AI work?'\n"
                "- 📦 **Orders**: 'Track my order'"
            )

        prod_names = [p["name"] for p in products]
        
        if intent == "price_filter":
            budget = context.get("budget")
            budget_str = f" under ₹{budget:,.0f}" if budget else ""
            return (
                f"Great news! I found **{len(products)}** products{budget_str} that fit your budget:\n\n"
                + "\n".join([f"- **{p['name']}** ({p['brand']}) — ₹{p['price']:,.2f} ⭐{p['rating']}" for p in products[:5]])
                + "\n\nClick on any product to view details and add to cart!"
            )
            
        elif intent == "compare_products":
            if len(products) >= 2:
                p1, p2 = products[0], products[1]
                return (
                    f"📊 **Product Comparison:**\n\n"
                    f"| Feature | {p1['name']} | {p2['name']} |\n"
                    f"|---------|-------------|-------------|\n"
                    f"| Brand | {p1['brand']} | {p2['brand']} |\n"
                    f"| Price | ₹{p1['price']:,.2f} | ₹{p2['price']:,.2f} |\n"
                    f"| Rating | {p1['rating']}⭐ | {p2['rating']}⭐ |\n\n"
                    f"💡 **Best Value:** {'**' + p1['name'] + '**' if p1['price'] < p2['price'] else '**' + p2['name'] + '**'} offers the lower price!"
                )
            return f"To compare items, please specify at least two matching products. Here is the closest match I found: **{products[0]['name']}**."
            
        elif intent == "trending_products":
            return (
                "🔥 **Trending Right Now:**\n\n"
                + "\n".join([f"- **{p['name']}** ({p['brand']}) — ₹{p['price']:,.2f} ⭐{p['rating']}" for p in products[:5]])
                + "\n\nThese are the hottest products based on recent customer activity!"
            )
            
        elif intent == "recommend_for_me":
            return (
                "🎯 **Personalized For You:**\n\n"
                "Based on your browsing history and preferences, our AI recommends:\n\n"
                + "\n".join([f"- **{p['name']}** ({p['brand']}) — ₹{p['price']:,.2f} ⭐{p['rating']}" for p in products[:5]])
            )
            
        elif intent == "order_status":
            return (
                "📦 **Order Tracking:**\n\n"
                "To check your order status:\n"
                "1. Click the **Profile** icon in the top navigation bar\n"
                "2. View your **Recent Orders** section\n"
                "3. Each order shows its current status (Confirmed, Shipped, Delivered)\n\n"
                "You can also visit the **Order History** page for complete details!"
            )

        elif intent == "review_summary":
            return (
                f"⭐ **Review Summary for {products[0]['name']}:**\n\n"
                f"This product has a rating of **{products[0]['rating']}⭐** based on customer reviews. "
                f"Visit the product page to read detailed customer reviews and leave your own!"
            )

        # Default general recommendation
        return (
            f"Here are **{len(products)}** products I found for you:\n\n"
            + "\n".join([f"- **{p['name']}** ({p['brand']}) — ₹{p['price']:,.2f} ⭐{p['rating']}" for p in products[:5]])
            + "\n\nWant me to compare any of these, or filter by price? Just ask!"
        )

    def _handle_greeting(self, msg: str) -> str:
        """Handle greetings and casual conversation."""
        if any(kw in msg for kw in ["continue shopping", "keep browsing", "browse more", "shop more"]):
            return (
                "Welcome back! 🛍️ Here's what you can explore:\n\n"
                "- 🔍 **Browse Products** — Check out our full catalog\n"
                "- 🔥 **Trending** — See what's hot right now\n"
                "- ❤️ **Your Wishlist** — Review your saved items\n"
                "- 🛒 **Your Cart** — Complete your pending checkout\n\n"
                "Or just tell me what you're looking for — I'll find it for you!"
            )
        return (
            "Hi there! 👋 I'm the **JourneyIQ AI Shopping Assistant**. I'm here to help you:\n\n"
            "- 🔍 Find and compare products\n"
            "- 🔥 Discover trending items\n"
            "- 💰 Shop within your budget\n"
            "- ❓ Answer questions about JourneyIQ\n\n"
            "What can I help you with today?"
        )

    def _handle_project_question(self, msg: str) -> str:
        """Route project-related questions to the right knowledge base entry."""
        if any(kw in msg for kw in ["tech stack", "technology", "built with", "framework", "language"]):
            return PROJECT_KNOWLEDGE["tech_stack"]
        elif any(kw in msg for kw in ["ml", "dl", "machine learning", "deep learning", "neural network", "model"]):
            return PROJECT_KNOWLEDGE["ml_dl"]
        elif any(kw in msg for kw in ["recommend", "ncf", "collaborative", "neural", "how does recommend", "recommendation"]):
            return PROJECT_KNOWLEDGE["recommendation"]
        elif any(kw in msg for kw in ["chatbot", "assistant", "nlp", "chat", "you do", "capabilities"]):
            return PROJECT_KNOWLEDGE["chatbot"]
        elif any(kw in msg for kw in ["dashboard", "analytics", "admin", "owner"]):
            return PROJECT_KNOWLEDGE["dashboard"]
        elif any(kw in msg for kw in ["sentiment", "review analysis", "vader", "textblob", "nlp analysis"]):
            return PROJECT_KNOWLEDGE["sentiment"]
        elif any(kw in msg for kw in ["agentic", "agent loop", "autonomous", "self-healing", "monitoring"]):
            return PROJECT_KNOWLEDGE["agentic"]
        else:
            return PROJECT_KNOWLEDGE["what_is"]

    def _try_project_fallback(self, msg: str) -> str | None:
        """Check if a message is about the project even if intent classifier missed it."""
        project_keywords = [
            "journeyiq", "journey iq", "this app", "this platform", "this project",
            "this website", "this site", "tech stack", "architecture", "deep learning",
            "machine learning", "ncf", "recommendation engine", "agentic", "agent loop",
            "sentiment", "vader", "who built", "who made", "who created",
            "how does this", "what does this", "tell me about", "ml", "dl", "ai"
        ]
        for kw in project_keywords:
            if kw in msg:
                return self._handle_project_question(msg)
        return None
