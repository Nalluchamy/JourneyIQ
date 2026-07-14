import asyncio
import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order
from app.models.agent_action import AgentAction
from app.models.agent_learning import AgentLearning
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.observer import ObserverModule
from app.services.agent.approval import ApprovalModule
from app.services.agent.learner import LearnerModule


async def run_scenario_verification():
    print("==================================================")
    print("STARTING JOURNEYIQ PHASE 13 BUSINESS SCENARIO TESTS")
    print("==================================================")
    
    async with AsyncSessionLocal() as db:
        # Check if Category exists, create if not
        cat_stmt = select(Category).limit(1)
        res_cat = await db.execute(cat_stmt)
        cat = res_cat.scalar_one_or_none()
        if not cat:
            cat = Category(name="Electronics", slug="electronics")
            db.add(cat)
            await db.commit()
            await db.refresh(cat)
            print(f"Created category: {cat.name}")

        # Check if a product exists, create if not
        prod_stmt = select(Product).limit(1)
        res_prod = await db.execute(prod_stmt)
        product = res_prod.scalar_one_or_none()
        if not product:
            product = Product(
                category_id=cat.id,
                name="Voyager Power Cell",
                slug="voyager-power-cell",
                price=1500.0,
                stock=50,
                is_active=True
            )
            db.add(product)
            await db.commit()
            await db.refresh(product)
            print(f"Created product: {product.name}")

        # Clean existing pending actions to keep test clear
        await db.execute(update(AgentAction).where(AgentAction.status == "PENDING").values(status="REJECTED"))
        await db.commit()

        # ==========================================
        # TEST 1 & 2: Low Stock & Revenue Drop
        # ==========================================
        print("\n--- TEST 1 & 2: Triggering Anomalies ---")
        
        # 1. Update product stock to 2
        print(f"Changing {product.name} stock to 2...")
        product.stock = 2
        db.add(product)
        await db.commit()

        # 2. Simulate Revenue Drop by making yesterday's revenue high and today's low
        is_sqlite = db.bind.dialect.name == "sqlite"
        now_val = datetime.datetime.now(datetime.timezone.utc)
        if is_sqlite:
            now_val = now_val.replace(tzinfo=None)

        yesterday_val = now_val - datetime.timedelta(hours=36)
        today_val = now_val - datetime.timedelta(hours=6)

        # Yesterday's order
        order_yesterday = Order(
            user_id=1,
            subtotal=500000.0,
            total=500000.0,
            status="confirmed",
            created_at=yesterday_val
        )
        # Today's order
        order_today = Order(
            user_id=1,
            subtotal=1000.0,
            total=1000.0,
            status="confirmed",
            created_at=today_val
        )
        db.add(order_yesterday)
        db.add(order_today)
        await db.commit()
        print("Created order history to trigger a 90% revenue drop.")

        # 3. Trigger Autonomous Run Loop
        print("Running Orchestrator Loop...")
        orch = AgentOrchestrator(db)
        # Run observer manually first to debug
        observer = ObserverModule(db)
        obs = await observer.observe_environment()
        print("Observed Revenue details:", obs.get("revenue"))
        
        actions = await orch.run_orchestrator_loop()
        print(f"Generated {len(actions)} PENDING plan proposals.")

        # Fetch proposed actions
        stmt = select(AgentAction).where(AgentAction.status == "PENDING")
        res_actions = await db.execute(stmt)
        pending_actions = res_actions.scalars().all()

        print("\nActive Pending Proposals in Safety Buffer Queue:")
        for a in pending_actions:
            print(f"- ID: {a.id} | Issue: {a.source_issue} | Type: {a.action_type} | Title: {a.title} | Priority: {a.priority}")

        # Check that Low Stock triggered RESTOCK
        low_stock_proposals = [a for a in pending_actions if "LOW_STOCK" in a.source_issue and a.action_type == "RESTOCK"]
        assert len(low_stock_proposals) > 0, "Failed: RESTOCK proposal was not created for LOW_STOCK issue."
        print("[SUCCESS] Test 1 Passed: RESTOCK Proposal is in queue.")

        # Check that Revenue Drop triggered 3 alternatives
        rev_drop_proposals = [a for a in pending_actions if "REVENUE_DROP" in a.source_issue]
        assert len(rev_drop_proposals) >= 3, f"Failed: Expected at least 3 alternatives for REVENUE_DROP, got {len(rev_drop_proposals)}."
        print("[SUCCESS] Test 2 Passed: Three alternatives (Coupon, Ads, Newsletter) generated for REVENUE_DROP.")

        # ==========================================
        # TEST 3: Approval
        # ==========================================
        print("\n--- TEST 3: Approving Plan Proposal ---")
        # Let's approve the low stock RESTOCK plan
        restock_action = low_stock_proposals[0]
        print(f"Approving Action ID {restock_action.id}: '{restock_action.title}'...")
        
        approval = ApprovalModule(db)
        executed_action = await approval.approve_action(restock_action.id)
        
        # Verify status updates
        await db.refresh(restock_action)
        await db.refresh(product)
        
        assert restock_action.status == "COMPLETED", f"Expected COMPLETED status, got {restock_action.status}"
        assert product.stock == 22, f"Expected product stock to be updated to 22 (2 + 20), got {product.stock}"
        print("[SUCCESS] Test 3 Passed: Action executed successfully, stock count updated to 22.")

        # ==========================================
        # TEST 4: Learner Evaluation
        # ==========================================
        print("\n--- TEST 4: Learner Evaluation & ROI Logging ---")
        learner = LearnerModule(db)
        learning = await learner.evaluate_action_outcome(restock_action)
        
        # Query learning entry
        stmt_learn = select(AgentLearning).where(AgentLearning.action_id == restock_action.id)
        res_learn = await db.execute(stmt_learn)
        db_learn = res_learn.scalar_one_or_none()
        
        assert db_learn is not None, "Failed: AgentLearning record was not written to database."
        print("[SUCCESS] Test 4 Passed: Learning metrics logged successfully.")
        print(f"  - Revenue Before: INR {db_learn.revenue_before:.2f}")
        print(f"  - Revenue After:  INR {db_learn.revenue_after:.2f}")
        print(f"  - ROI Delta:      {db_learn.roi}%")
        print(f"  - Execution Time: {db_learn.execution_time_ms} ms")
        print(f"  - Success status: {db_learn.success}")

        # ==========================================
        # TEST 5: Timeline Status Logs
        # ==========================================
        print("\n--- TEST 5: Timeline Visual Flow ---")
        status_res = await orch.get_orchestrator_status()
        history = status_res.get("execution_history", [])
        print("Timeline Decision & Action Logs:")
        for log in history:
            print(f"- {log['timestamp']} | Action: {log['action']} | Status: {log['status']} | Impact: {log['impact']}")
        
        assert len(history) > 0, "Failed: Execution history log timeline is empty."
        print("[SUCCESS] Test 5 Passed: Dynamic timeline flow shows execution phases.")

        print("\n==================================================")
        print("ALL SCENARIO VERIFICATIONS COMPLETED SUCCESSFULLY!")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_scenario_verification())
