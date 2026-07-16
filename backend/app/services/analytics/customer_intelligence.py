import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.order import Order
from app.models.segment import Segment
from app.models.user import User
from app.services.ml.kmeans_segmentation import KMeansSegmenter


class CustomerIntelligenceService:
    """Computes customer intelligence metrics: RFM Analysis, ML K-Means Segments, Churn risk, and CLV."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_rfm_and_segmentation(self) -> list[dict[str, Any]]:
        """
        Calculate RFM metrics, run dynamic K-Means Clustering for segmentation, update the Segments table, 
        and return a dictionary of customer states.
        """
        # Fetch all customers
        users_stmt = select(User).where(User.is_deleted == False, User.role == "customer")
        users = (await self.db.execute(users_stmt)).scalars().all()

        # Fetch all orders grouped by user
        orders_stmt = select(Order).where(Order.status == "confirmed")
        orders_res = await self.db.execute(orders_stmt)
        orders = orders_res.scalars().all()

        user_orders: dict[int, list[Order]] = {u.id: [] for u in users}
        for o in orders:
            if o.user_id in user_orders:
                user_orders[o.user_id].append(o)

        now = datetime.datetime.now(datetime.UTC)
        results = []

        # Wipe existing segments to rewrite
        await self.db.execute(delete(Segment))

        # 1. Collect RFM Data for all users
        rfm_data = []
        user_metrics_map = {}

        for user in users:
            orders_list = user_orders.get(user.id, [])
            total_spend = sum(float(o.total) for o in orders_list)
            order_count = len(orders_list)

            # Recency
            recency_days = 999
            if orders_list:
                latest_order = max(orders_list, key=lambda o: o.created_at)
                created_at = latest_order.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=datetime.UTC)
                recency_days = (now - created_at).days

            rfm_data.append({
                "user_id": user.id,
                "recency": recency_days,
                "frequency": order_count,
                "monetary": total_spend
            })

            user_metrics_map[user.id] = {
                "user": user,
                "recency_days": recency_days,
                "order_count": order_count,
                "total_spend": total_spend
            }

        # 2. Run K-Means Clustering if we have enough users
        user_segments = {}
        segmenter = KMeansSegmenter(n_clusters=4)
        if len(rfm_data) >= 4:
            try:
                user_segments = segmenter.cluster_users(rfm_data)
            except Exception as e:
                import structlog
                logger = structlog.get_logger()
                logger.error("K-Means clustering failed, falling back to rules.", error=str(e))

        # 3. Final Evaluation Loop
        for metrics in rfm_data:
            u_id = metrics["user_id"]
            user = user_metrics_map[u_id]["user"]
            recency_days = user_metrics_map[u_id]["recency_days"]
            order_count = user_metrics_map[u_id]["order_count"]
            total_spend = user_metrics_map[u_id]["total_spend"]

            # RFM Scores (1-5 scales for display)
            r_score = 1
            if recency_days <= 7: r_score = 5
            elif recency_days <= 30: r_score = 4
            elif recency_days <= 60: r_score = 3
            elif recency_days <= 90: r_score = 2

            f_score = 1
            if order_count >= 10: f_score = 5
            elif order_count >= 5: f_score = 4
            elif order_count >= 3: f_score = 3
            elif order_count >= 1: f_score = 2

            m_score = 1
            if total_spend >= 1000: m_score = 5
            elif total_spend >= 500: m_score = 4
            elif total_spend >= 200: m_score = 3
            elif total_spend > 0: m_score = 2

            recency_label = "Very Recent" if r_score == 5 else ("Recent" if r_score == 4 else ("Moderate" if r_score == 3 else ("Stale" if r_score == 2 else "Inactive")))
            frequency_label = "Frequent" if f_score == 5 else ("Regular" if f_score >= 3 else ("Occasional" if f_score == 2 else "Inactive"))
            monetary_label = "High Spender" if m_score == 5 else ("Medium Spender" if m_score >= 3 else ("Low Spender" if m_score == 2 else "Non-Spender"))

            # Assign Dynamic K-Means Segment or Fallback to Rules
            segment_name = user_segments.get(u_id)
            if not segment_name:
                if order_count == 0: segment_name = "Window Shoppers"
                elif order_count == 1 and r_score >= 4: segment_name = "New Customers"
                elif f_score >= 4 and r_score >= 4: segment_name = "Loyal Customers"
                elif m_score >= 4: segment_name = "Big Spenders"
                elif f_score >= 4: segment_name = "Frequent Buyers"
                elif r_score == 1: segment_name = "Lost Customers"
                elif r_score <= 3: segment_name = "At-Risk Customers"
                else: segment_name = "New Customers"

            # Write segment to DB
            seg = Segment(user_id=user.id, segment_name=segment_name, confidence=1.0)
            self.db.add(seg)

            # Churn Prediction
            churn_risk = "Low"
            churn_explanation = "Active customer with recent purchase activity."
            if order_count > 0:
                if recency_days > 90:
                    churn_risk = "High"
                    churn_explanation = f"Customer has not purchased anything in over 90 days (last order was {recency_days} days ago)."
                elif recency_days > 45:
                    churn_risk = "Medium"
                    churn_explanation = f"Customer has not purchased in 45 days (last order was {recency_days} days ago)."
            else:
                # New / Window shopper check session events
                event_stmt = select(func.count(Event.id)).where(Event.user_id == user.id)
                event_count = (await self.db.execute(event_stmt)).scalar() or 0
                if event_count > 0:
                    churn_risk = "Medium"
                    churn_explanation = "Window shopper with view activity but zero purchases."
                else:
                    churn_risk = "High"
                    churn_explanation = "Inactive user with zero session activity."

            # CLV calculation
            aov = total_spend / order_count if order_count > 0 else 0.0
            expected_clv = total_spend + (aov * 2.0) if order_count > 0 else 0.0

            results.append({
                "user_id": user.id,
                "customer_name": user.full_name,
                "email": user.email,
                "recency_days": recency_days,
                "order_count": order_count,
                "total_spend": round(total_spend, 2),
                "rfm": {
                    "recency": recency_label,
                    "frequency": frequency_label,
                    "monetary": monetary_label,
                    "r_score": r_score,
                    "f_score": f_score,
                    "m_score": m_score,
                },
                "segment": segment_name,
                "churn": {
                    "risk_level": churn_risk,
                    "explanation": churn_explanation,
                },
                "clv": {
                    "expected_value": round(expected_clv, 2),
                }
            })

        await self.db.commit()
        return results
