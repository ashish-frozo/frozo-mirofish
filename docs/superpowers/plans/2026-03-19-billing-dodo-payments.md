# Billing & Plans (Dodo Payments) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Dodo Payments for subscription billing — users on expired trials can upgrade to Starter ($19/mo) or Pro ($49/mo) via hosted checkout, with webhook-based status sync and plan limit enforcement.

**Architecture:** Backend billing blueprint handles checkout session creation (redirect to Dodo), webhook receiver (updates user plan in DB), customer portal (for self-serve management). Frontend adds upgrade prompts on dashboard and billing API wrapper. All Dodo config via env vars set in Railway.

**Tech Stack:** `dodopayments` Python SDK, Dodo hosted checkout, webhooks

**Spec:** `docs/superpowers/specs/2026-03-19-billing-dodo-payments-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `backend/app/api/billing.py` | Billing blueprint: checkout, portal, webhook, status |
| `frontend/src/api/billing.js` | Billing API wrapper |

### Modified Files

| File | Change |
|------|--------|
| `backend/pyproject.toml` | Add `dodopayments` dependency |
| `backend/app/config.py` | Add DODO_* config vars |
| `backend/app/models/db_models.py` | Add 4 billing columns to UserModel |
| `backend/app/api/__init__.py` | Export billing_bp |
| `backend/app/__init__.py` | Register billing blueprint |
| `backend/app/middleware/auth.py` | Update require_active_plan with subscription logic |
| `frontend/src/views/Dashboard.vue` | Add upgrade prompts, payment success handling |
| `frontend/src/store/auth.js` | Add billing computed properties |

---

## Task 1: Add Dodo Payments Dependency & Config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add dodopayments to pyproject.toml dependencies**

Add to the dependencies list:
```toml
    # Billing
    "dodopayments>=1.0",
```

- [ ] **Step 2: Add Dodo config vars to Config class**

Add to `backend/app/config.py` after the Google OAuth section:

```python
    # Dodo Payments
    DODO_API_KEY = os.environ.get('DODO_API_KEY', '')
    DODO_WEBHOOK_SECRET = os.environ.get('DODO_WEBHOOK_SECRET', '')
    DODO_STARTER_PRODUCT_ID = os.environ.get('DODO_STARTER_PRODUCT_ID', '')
    DODO_PRO_PRODUCT_ID = os.environ.get('DODO_PRO_PRODUCT_ID', '')
    DODO_ENVIRONMENT = os.environ.get('DODO_ENVIRONMENT', 'test_mode')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://frozo-mirofish-production.up.railway.app')
```

- [ ] **Step 3: Install dependency**

Run: `cd /Users/ashishdhiman/WORK/miro-fish/MiroFish/backend && uv sync`

- [ ] **Step 4: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add backend/pyproject.toml backend/uv.lock backend/app/config.py && git commit -m "deps: add dodopayments SDK and billing config vars

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Add Billing Columns to UserModel

**Files:**
- Modify: `backend/app/models/db_models.py`

- [ ] **Step 1: Add 4 billing fields to UserModel**

Read `backend/app/models/db_models.py`. Add these fields to the `UserModel` class after `stripe_customer_id`:

```python
    dodo_customer_id: Mapped[str | None] = mapped_column(String(255))
    dodo_subscription_id: Mapped[str | None] = mapped_column(String(255))
    subscription_status: Mapped[str | None] = mapped_column(String(50))  # active | on_hold | cancelled | expired
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 2: Verify model imports clean**

Run: `cd /Users/ashishdhiman/WORK/miro-fish/MiroFish/backend && uv run python -c "from app.models.db_models import UserModel; print(f'{len(UserModel.__table__.columns)} columns')"`

- [ ] **Step 3: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add backend/app/models/db_models.py && git commit -m "feat: add Dodo billing columns to UserModel

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Billing API Blueprint

**Files:**
- Create: `backend/app/api/billing.py`
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Create billing blueprint**

Create `backend/app/api/billing.py`:

```python
"""
Billing API — Dodo Payments integration.
Handles checkout sessions, customer portal, webhooks, and billing status.
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, g
from dodopayments import DodoPayments

from ..config import Config
from ..db import get_db
from ..middleware.auth import require_auth
from ..repositories.user_repo import UserRepository
from ..utils.logger import get_logger

logger = get_logger('mirofish.billing')

billing_bp = Blueprint('billing', __name__)

# Plan config
PLAN_PRODUCTS = {
    'starter': lambda: Config.DODO_STARTER_PRODUCT_ID,
    'pro': lambda: Config.DODO_PRO_PRODUCT_ID,
}

PLAN_LIMITS = {
    'trial': {'simulations_per_month': 3, 'max_agents': 20, 'max_rounds': 10},
    'starter': {'simulations_per_month': 5, 'max_agents': 20, 'max_rounds': 10},
    'pro': {'simulations_per_month': 20, 'max_agents': 50, 'max_rounds': 40},
    'enterprise': {'simulations_per_month': 999, 'max_agents': 200, 'max_rounds': 100},
}


def _get_dodo_client():
    """Create Dodo Payments client."""
    return DodoPayments(
        bearer_token=Config.DODO_API_KEY,
        environment=Config.DODO_ENVIRONMENT,
    )


def _product_id_to_plan(product_id: str) -> str:
    """Map a Dodo product ID to a plan name."""
    if product_id == Config.DODO_STARTER_PRODUCT_ID:
        return 'starter'
    elif product_id == Config.DODO_PRO_PRODUCT_ID:
        return 'pro'
    return 'unknown'


@billing_bp.route('/checkout', methods=['POST'])
@require_auth
def create_checkout():
    """Create a Dodo checkout session and return the redirect URL."""
    data = request.get_json() or {}
    plan = data.get('plan')

    if plan not in PLAN_PRODUCTS:
        return jsonify({"success": False, "error": f"Invalid plan: {plan}. Choose 'starter' or 'pro'."}), 422

    product_id = PLAN_PRODUCTS[plan]()
    if not product_id:
        return jsonify({"success": False, "error": "Billing not configured. Please contact support."}), 503

    user = g.current_user

    try:
        client = _get_dodo_client()
        session = client.checkout_sessions.create(
            product_cart=[{"product_id": product_id, "quantity": 1}],
            customer={
                "email": user.email,
                "name": user.name,
            },
            metadata={"user_id": str(user.id), "plan": plan},
            return_url=f"{Config.FRONTEND_URL}/dashboard?payment=success",
        )

        logger.info(f"Checkout session created for user {user.id}, plan={plan}")
        return jsonify({"success": True, "checkout_url": session.checkout_url}), 200

    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        return jsonify({"success": False, "error": "Failed to create checkout session"}), 500


@billing_bp.route('/portal', methods=['POST'])
@require_auth
def create_portal():
    """Create a Dodo customer portal session for subscription management."""
    user = g.current_user

    if not user.dodo_customer_id:
        return jsonify({"success": False, "error": "No active subscription found"}), 404

    try:
        client = _get_dodo_client()
        portal = client.customers.create_customer_portal_session(
            customer_id=user.dodo_customer_id,
        )

        logger.info(f"Portal session created for user {user.id}")
        return jsonify({"success": True, "portal_url": portal.url}), 200

    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        return jsonify({"success": False, "error": "Failed to create portal session"}), 500


@billing_bp.route('/webhook', methods=['POST'])
def handle_webhook():
    """Receive and process Dodo Payments webhook events. No auth — verified by signature."""
    payload = request.get_data(as_text=True)

    # Verify webhook signature
    signature = request.headers.get('X-Dodo-Signature') or request.headers.get('Webhook-Signature') or ''
    if Config.DODO_WEBHOOK_SECRET and signature:
        expected = hmac.new(
            Config.DODO_WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning("Webhook signature verification failed")
            return jsonify({"error": "Invalid signature"}), 401

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    event_type = event.get('type', '')
    data = event.get('data', {})

    logger.info(f"Webhook received: {event_type}")

    # Extract user_id from metadata
    metadata = data.get('metadata', {})
    user_id = metadata.get('user_id')

    if not user_id:
        # Try to find user by subscription_id or customer_id
        logger.warning(f"Webhook {event_type} missing user_id in metadata")
        return jsonify({"received": True}), 200

    with get_db() as session:
        repo = UserRepository(session)
        user = repo.get_by_id(user_id)
        if not user:
            logger.warning(f"Webhook user not found: {user_id}")
            return jsonify({"received": True}), 200

        subscription_id = data.get('subscription_id') or data.get('id')
        customer_id = data.get('customer_id') or data.get('customer', {}).get('id')

        # Update customer/subscription IDs if present
        if customer_id and not user.dodo_customer_id:
            user.dodo_customer_id = customer_id
        if subscription_id:
            user.dodo_subscription_id = subscription_id

        # Handle event types
        if event_type == 'subscription.active':
            product_id = data.get('product_id', '')
            plan = _product_id_to_plan(product_id)
            if plan != 'unknown':
                user.plan = plan
            user.subscription_status = 'active'
            next_billing = data.get('next_billing_date') or data.get('current_period_end')
            if next_billing:
                try:
                    user.current_period_end = datetime.fromisoformat(next_billing.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            logger.info(f"Subscription activated: user={user_id}, plan={user.plan}")

        elif event_type == 'subscription.renewed':
            user.subscription_status = 'active'
            next_billing = data.get('next_billing_date') or data.get('current_period_end')
            if next_billing:
                try:
                    user.current_period_end = datetime.fromisoformat(next_billing.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            logger.info(f"Subscription renewed: user={user_id}")

        elif event_type == 'subscription.on_hold':
            user.subscription_status = 'on_hold'
            logger.info(f"Subscription on hold: user={user_id}")

        elif event_type == 'subscription.cancelled':
            user.subscription_status = 'cancelled'
            logger.info(f"Subscription cancelled: user={user_id} (active until {user.current_period_end})")

        elif event_type == 'subscription.expired':
            user.plan = 'expired'
            user.subscription_status = 'expired'
            logger.info(f"Subscription expired: user={user_id}")

        elif event_type == 'subscription.failed':
            user.subscription_status = 'failed'
            logger.warning(f"Subscription failed: user={user_id}")

        elif event_type == 'subscription.plan_changed':
            product_id = data.get('product_id', '')
            plan = _product_id_to_plan(product_id)
            if plan != 'unknown':
                user.plan = plan
            logger.info(f"Plan changed: user={user_id}, new_plan={user.plan}")

        else:
            logger.info(f"Unhandled webhook event: {event_type}")

    return jsonify({"received": True}), 200


@billing_bp.route('/status', methods=['GET'])
@require_auth
def get_billing_status():
    """Get current user's billing and plan status."""
    user = g.current_user
    now = datetime.now(timezone.utc)

    trial_expired = user.plan == 'trial' and now > user.trial_ends_at
    trial_days_left = max(0, (user.trial_ends_at - now).days) if user.plan == 'trial' else None

    # Determine if user can create projects
    can_create = False
    if user.plan in ('starter', 'pro', 'enterprise') and user.subscription_status == 'active':
        can_create = True
    elif user.plan in ('starter', 'pro') and user.subscription_status == 'cancelled':
        can_create = user.current_period_end and now < user.current_period_end
    elif user.plan == 'trial' and not trial_expired:
        can_create = True

    plan_limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS['trial'])

    return jsonify({
        "success": True,
        "plan": user.plan,
        "subscription_status": user.subscription_status,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "trial_expired": trial_expired,
        "trial_days_left": trial_days_left,
        "current_period_end": user.current_period_end.isoformat() if user.current_period_end else None,
        "can_create_projects": can_create,
        "limits": plan_limits,
    }), 200
```

- [ ] **Step 2: Register billing blueprint**

Add to `backend/app/api/__init__.py`:
```python
from .billing import billing_bp
```

Add to `backend/app/__init__.py` (after other blueprint registrations):
```python
app.register_blueprint(billing_bp, url_prefix='/api/billing')
```

- [ ] **Step 3: Verify app starts**

Run: `cd /Users/ashishdhiman/WORK/miro-fish/MiroFish/backend && uv run python -c "from app import create_app; app = create_app(); print(f'App OK, {len(list(app.url_map.iter_rules()))} routes')"`

- [ ] **Step 4: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add backend/app/api/billing.py backend/app/api/__init__.py backend/app/__init__.py && git commit -m "feat: add billing API — checkout, portal, webhook, and status endpoints

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Update Auth Middleware for Subscription Logic

**Files:**
- Modify: `backend/app/middleware/auth.py`

- [ ] **Step 1: Update require_active_plan decorator**

Read `backend/app/middleware/auth.py`. Replace the `require_active_plan` function with:

```python
def require_active_plan(f):
    """Decorator: require non-expired trial or active paid subscription."""
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        user = g.current_user
        now = datetime.now(timezone.utc)

        # Paid plan with active subscription — always allowed
        if user.plan in ('starter', 'pro', 'enterprise') and user.subscription_status == 'active':
            return f(*args, **kwargs)

        # Paid plan cancelled — allowed until period ends
        if user.plan in ('starter', 'pro') and user.subscription_status == 'cancelled':
            if user.current_period_end and now < user.current_period_end:
                return f(*args, **kwargs)

        # Trial — allowed if not expired
        if user.plan == 'trial' and now < user.trial_ends_at:
            return f(*args, **kwargs)

        # Everything else — blocked
        return jsonify({
            "error": "Active subscription required",
            "code": "SUBSCRIPTION_REQUIRED",
            "trial_expired": user.plan == 'trial',
        }), 403

    return decorated
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add backend/app/middleware/auth.py && git commit -m "feat: update trial enforcement with subscription status checks

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Frontend — Billing API + Dashboard Upgrade Prompts

**Files:**
- Create: `frontend/src/api/billing.js`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/store/auth.js`

- [ ] **Step 1: Create billing API wrapper**

Create `frontend/src/api/billing.js`:

```javascript
import service from './index'

export const createCheckout = (plan) => service.post('/api/billing/checkout', { plan })
export const createPortal = () => service.post('/api/billing/portal')
export const getBillingStatus = () => service.get('/api/billing/status')
```

- [ ] **Step 2: Update auth store with billing properties**

Read `frontend/src/store/auth.js`. Add these computed properties:

```javascript
const canCreateProjects = computed(() => {
  if (!user.value) return false
  const u = user.value
  if (['starter', 'pro', 'enterprise'].includes(u.plan) && u.subscription_status === 'active') return true
  if (['starter', 'pro'].includes(u.plan) && u.subscription_status === 'cancelled' && u.current_period_end) {
    return new Date(u.current_period_end) > new Date()
  }
  if (u.plan === 'trial') return !isTrialExpired.value
  return false
})

const currentPlan = computed(() => user.value?.plan || 'trial')
const subscriptionStatus = computed(() => user.value?.subscription_status || null)
```

Export them from the store return statement.

- [ ] **Step 3: Update Dashboard with upgrade prompts**

Read `frontend/src/views/Dashboard.vue`. Add:

1. **Import billing API:**
```javascript
import { createCheckout, createPortal } from '../api/billing'
```

2. **Upgrade banner when trial expired or subscription needed:**
When `auth.isTrialExpired` is true or `!auth.canCreateProjects`, show:
```html
<div class="bg-red-50 border border-red-200 rounded-xl p-6 mb-8 text-center">
  <h3 class="text-lg font-semibold text-red-900 mb-2">Your trial has expired</h3>
  <p class="text-red-700 mb-4">Upgrade to continue creating predictions.</p>
  <div class="flex gap-3 justify-center">
    <button @click="handleUpgrade('starter')" class="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">
      Starter — $19/mo
    </button>
    <button @click="handleUpgrade('pro')" class="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">
      Pro — $49/mo
    </button>
  </div>
</div>
```

3. **Upgrade handler:**
```javascript
const upgrading = ref(false)
async function handleUpgrade(plan) {
  upgrading.value = true
  try {
    const res = await createCheckout(plan)
    window.location.href = res.checkout_url
  } catch (e) {
    console.error('Checkout failed:', e)
    alert('Failed to start checkout. Please try again.')
  } finally {
    upgrading.value = false
  }
}
```

4. **Payment success detection:**
```javascript
import { useRoute } from 'vue-router'
const route = useRoute()

onMounted(async () => {
  if (route.query.payment === 'success') {
    // Show success message and refresh user data
    await auth.fetchUser()
    // Remove query param
    router.replace({ path: '/dashboard' })
  }
})
```

5. **"Manage Subscription" button** (shown when user has active subscription):
```javascript
async function handleManageSubscription() {
  try {
    const res = await createPortal()
    window.location.href = res.portal_url
  } catch (e) {
    console.error('Portal failed:', e)
  }
}
```

- [ ] **Step 4: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add frontend/src/api/billing.js frontend/src/views/Dashboard.vue frontend/src/store/auth.js && git commit -m "feat: add billing UI — upgrade prompts, checkout redirect, subscription management

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Deploy and Verify

- [ ] **Step 1: Run tests**

Run: `cd /Users/ashishdhiman/WORK/miro-fish/MiroFish/backend && uv run pytest tests/ -v`
Expected: All tests pass (billing endpoints need Dodo keys to fully test, but app should start)

- [ ] **Step 2: Push and deploy**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git push frozo main && railway up --detach
```

- [ ] **Step 3: Verify deployment**

```bash
curl -s https://frozo-mirofish-production.up.railway.app/health
curl -s https://frozo-mirofish-production.up.railway.app/api/billing/status -H "Authorization: Bearer <token>"
```

- [ ] **Step 4: Set env vars in Railway (user does this manually)**

In Railway dashboard, add:
- `DODO_API_KEY`
- `DODO_WEBHOOK_SECRET`
- `DODO_STARTER_PRODUCT_ID`
- `DODO_PRO_PRODUCT_ID`
- `DODO_ENVIRONMENT=test_mode`
- `FRONTEND_URL=https://frozo-mirofish-production.up.railway.app`

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Dodo SDK + config | `pyproject.toml`, `config.py` |
| 2 | UserModel billing columns | `db_models.py` |
| 3 | Billing API blueprint | `api/billing.py`, `__init__.py` |
| 4 | Subscription-aware auth middleware | `middleware/auth.py` |
| 5 | Frontend billing UI | `billing.js`, `Dashboard.vue`, `auth.js` |
| 6 | Deploy and verify | Push + Railway |
