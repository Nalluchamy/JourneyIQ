import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_action import AgentAction


class PlannerModule:
    """Translates analyzed storefront issues into multiple alternative actionable plans in the database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def construct_plans(self, issues: list[dict[str, Any]]) -> list[AgentAction]:
        """
        Processes detected issues, generates multiple plans, saves them as PENDING AgentActions.
        """
        actions = []
        today_str = datetime.date.today().isoformat()

        for idx, issue in enumerate(issues):
            issue_type = issue["issue_type"]
            priority = issue["priority"]
            affected = ", ".join(issue["affected_objects"])
            source_id = f"{issue_type}-{today_str}"

            if issue_type == "REVENUE_DROP":
                # Option 1: Discount Coupon
                actions.append(AgentAction(
                    action_type="COUPON",
                    title="Trigger FLASH15 discount campaign",
                    description="Generate store-wide coupon FLASH15 offering 15% off to stimulate customer purchase velocity.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.92,
                    reasoning="Discount coupons create immediate purchasing incentive to counteract sales drop-offs.",
                    created_by="Agent"
                ))
                # Option 2: Marketing Ads Campaign
                actions.append(AgentAction(
                    action_type="AD_CAMPAIGN",
                    title="Launch targeted advertising on socials",
                    description="Proposes allocating ad budget to retarget users in At-Risk segment to drive storefront traffic.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.85,
                    reasoning="Social retargeting drives high-intent visitors back to storefront to capture missed conversions.",
                    created_by="Agent"
                ))
                # Option 3: Email Campaign
                actions.append(AgentAction(
                    action_type="EMAIL_CAMPAIGN",
                    title="Send promotional newsletter blast",
                    description="Draft and dispatch an email blast showcasing trending items to all registered shoppers.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.80,
                    reasoning="Email blasts have low operational costs and high conversion rates when promoting trending catalogs.",
                    created_by="Agent"
                ))

            elif issue_type == "OUT_OF_STOCK":
                actions.append(AgentAction(
                    action_type="RESTOCK",
                    title=f"Emergency supplier purchase order request",
                    description=f"Create a purchase order request to suppliers to restock out-of-stock items: {affected}.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.95,
                    reasoning="Sourcing inventory immediately prevents lost revenue opportunities on popular out-of-stock items.",
                    created_by="Agent"
                ))

            elif issue_type == "PAYMENT_FAILURE":
                actions.append(AgentAction(
                    action_type="NOTIFICATION",
                    title="Alert technical operations of gateway failures",
                    description=f"Send an instant notification alert to engineering team to inspect webhook responses and failed logs: {affected}.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.98,
                    reasoning="High checkout drop-off rates due to gateway failures require urgent technical troubleshooting.",
                    created_by="Agent"
                ))

            elif issue_type == "LOW_STOCK":
                actions.append(AgentAction(
                    action_type="RESTOCK",
                    title=f"Create supplier replenishment request",
                    description=f"Draft purchase order requests for restocking low stock products: {affected}.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.90,
                    reasoning="Restocking items prior to complete depletion avoids stockouts and maintains catalog completeness.",
                    created_by="Agent"
                ))

            elif issue_type == "DECLINING_SENTIMENT":
                actions.append(AgentAction(
                    action_type="CAMPAIGN_SUPPORT",
                    title="Launch customer feedback outreach campaign",
                    description="Email dissatisfied customers who reviewed negatively to offer direct support resolution.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.85,
                    reasoning="Outreach to disgruntled buyers resolves issues early, boosting user retention and reviews score.",
                    created_by="Agent"
                ))

            elif issue_type == "CART_ABANDONMENT":
                # Option 1: Coupon
                actions.append(AgentAction(
                    action_type="COUPON",
                    title="Generate winback cart coupon WINBACK10",
                    description="Create a cart-recovery coupon WINBACK10 (10% off) and email it to users with abandoned carts.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.88,
                    reasoning="Incentivizing price-sensitive checkout drop-offs with single-use coupons increases conversion rate.",
                    created_by="Agent"
                ))
                # Option 2: Reminder push notification
                actions.append(AgentAction(
                    action_type="NOTIFICATION",
                    title="Trigger cart reminder notifications",
                    description="Dispatch push reminder alerts to customers with pending cart items to finish checkout.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.80,
                    reasoning="Gentle reminders nudge visitors who got distracted or left checkout pages open without checking out.",
                    created_by="Agent"
                ))

            elif issue_type == "SLOW_PRODUCT":
                actions.append(AgentAction(
                    action_type="COUPON",
                    title="Trigger slow product bundle discount BUNDLE20",
                    description=f"Generate BUNDLE20 (20% off) applicable when buying a slow-selling item ({affected}) with a trending product.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.82,
                    reasoning="Pairing slow-moving stock items as bundle deals with high-traffic products clears warehousing inventory fast.",
                    created_by="Agent"
                ))

            elif issue_type == "MODEL_DEGRADATION":
                actions.append(AgentAction(
                    action_type="RETRAIN_MODEL",
                    title="Trigger PyTorch recommendation retraining pipeline",
                    description="Initiate async recommendation engine model training loop with fresh user interaction matrices.",
                    priority=priority,
                    status="PENDING",
                    source_issue=source_id,
                    confidence=0.92,
                    reasoning="Updating latent matrix embeddings ensures NCF parameters fit current storefront trends.",
                    created_by="Agent"
                ))

        # Save all actions to the database
        for action in actions:
            self.db.add(action)
        await self.db.commit()

        return actions
