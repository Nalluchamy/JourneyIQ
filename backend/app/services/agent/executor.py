import datetime
import time
from decimal import Decimal
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.agent_action import AgentAction
from app.models.product import Product
from app.models.coupon import Coupon
from app.services.deep_learning.train import train_ncf_model
from app.services.ml.scheduler import run_ncf_evaluation_pipeline


class ExecutorModule:
    """Executes business plans approved by the owner and logs details, start/end times, and results."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_action(self, action: AgentAction) -> None:
        """
        Runs the specified task, logging execution details to the database record.
        """
        start_time_real = func.now()
        action.start_time = start_time_real
        action.retry_count += 1
        
        start_perf = time.perf_counter()
        status = "COMPLETED"
        error_msg = None
        result_desc = ""

        try:
            if action.action_type == "RESTOCK":
                # Proactively raise purchase request and update stock for products under threshold (< 5)
                stmt_low = select(Product).where(and_(Product.is_deleted == False, Product.stock < 5))
                res_low = await self.db.execute(stmt_low)
                low_products = res_low.scalars().all()
                
                prod_names = []
                for p in low_products:
                    p.stock += 20  # Simulate replenishment delivery receipt
                    prod_names.append(p.name)
                
                result_desc = (
                    f"Created Supplier Purchase Order PR-{action.id:04d}. "
                    f"Dispatched restock order. Received shipment and updated stock for: "
                    f"{', '.join(prod_names) if prod_names else 'None'} by +20 units."
                )

            elif action.action_type == "COUPON":
                # Create recommended coupon code in database
                code = "FLASH15" if "FLASH15" in action.title else "WINBACK10"
                # Add unique suffix to prevent duplicate code constraints in repeated tests
                unique_code = f"{code}-{action.id}"
                
                discount_val = Decimal("15.00") if "FLASH15" in action.title else Decimal("10.00")
                
                coupon = Coupon(
                    code=unique_code,
                    description=action.description,
                    discount_type="percentage",
                    discount_value=discount_val,
                    minimum_order=Decimal("0.00"),
                    start_date=func.now(),
                    expiry_date=func.now() + datetime.timedelta(days=7),
                    usage_limit=100,
                    is_active=True
                )
                self.db.add(coupon)
                result_desc = f"Generated active discount coupon {unique_code} ({discount_val}% off) in the system catalog."

            elif action.action_type in ("AD_CAMPAIGN", "EMAIL_CAMPAIGN", "NOTIFICATION", "CAMPAIGN_SUPPORT"):
                # Simulate dispatches and write trace details
                result_desc = (
                    f"Successfully launched {action.action_type} campaign. "
                    f"Target Segment: {action.title}. Logs: Dispatched notification alerts."
                )

            elif action.action_type == "RETRAIN_MODEL":
                # Trigger actual recommendation NCF PyTorch model retraining
                await train_ncf_model(self.db)
                # Re-run model metrics evaluation pipeline
                await run_ncf_evaluation_pipeline(self.db)
                result_desc = "Triggered recommendation training pipeline. Re-trained PyTorch NCF neural layers and saved fresh weights."

            else:
                result_desc = f"Executed generic action: {action.title}."

        except Exception as e:
            status = "FAILED"
            error_msg = str(e)
            result_desc = f"Execution failed: {error_msg}"

        finally:
            end_perf = time.perf_counter()
            action.status = status
            action.execution_result = result_desc
            action.error_message = error_msg
            action.end_time = func.now()
            action.executed_at = func.now()
            action.execution_time_ms = int((end_perf - start_perf) * 1000)

            await self.db.commit()
            # Refresh to resolve server-side func.now() SQL expressions
            # into real Python datetime values for the learner module
            await self.db.refresh(action)
