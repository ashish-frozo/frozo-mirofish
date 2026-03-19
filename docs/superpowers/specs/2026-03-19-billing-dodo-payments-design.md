# MiroFish Billing & Plans — Dodo Payments Integration

**Date:** 2026-03-19
**Status:** Approved
**Scope:** Sub-project #4 — Billing & subscription management via Dodo Payments

## 1. Overview

Integrate Dodo Payments as the billing provider for MiroFish. Users on expired trials are prompted to subscribe. Subscription management happens via Dodo's hosted checkout and customer portal. Backend tracks plan status via webhooks.

### Goals
- Users can subscribe to Starter ($19/mo) or Pro ($49/mo) plans via Dodo hosted checkout
- Enterprise users contact sales (no self-serve checkout)
- Trial expiry blocks new project creation, shows upgrade prompt
- Webhook updates plan status in real-time (active, cancelled, on_hold, expired)
- Users can manage their subscription (cancel, change plan) via Dodo customer portal

### Non-Goals
- Usage-based billing (deferred)
- In-app checkout embed (using redirect instead)
- Annual billing (deferred — monthly only for launch)

## 2. Technical Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Payment provider | Dodo Payments (MoR) | Handles tax, compliance, global payments |
| SDK | `dodopayments` Python SDK | Official, well-documented |
| Checkout flow | Redirect to Dodo hosted checkout | Simplest, PCI compliant, handles all payment methods |
| Plan management | Dodo customer portal | No need to build billing UI |
| Status sync | Webhooks | Real-time, no polling |
| Trial | 14-day, already in user model | `users.trial_ends_at` field exists |

### Flow

```
User clicks "Upgrade" on dashboard
    → Backend creates Dodo checkout session (POST /checkouts)
    → User redirected to Dodo hosted checkout
    → User pays
    → Dodo sends webhook (subscription.active)
    → Backend updates users.plan = 'starter' or 'pro'
    → User redirected back to /dashboard?payment=success
```

## 3. Dodo Payments Setup (Manual — in Dodo Dashboard)

Before code, create these in the Dodo dashboard:

### Products to Create
1. **MiroFish Starter** — $19/month subscription
   - Product ID: note as `DODO_STARTER_PRODUCT_ID`
2. **MiroFish Pro** — $49/month subscription
   - Product ID: note as `DODO_PRO_PRODUCT_ID`

### Webhook to Configure
- URL: `https://frozo-mirofish-production.up.railway.app/api/billing/webhook`
- Events: `subscription.active`, `subscription.updated`, `subscription.on_hold`, `subscription.renewed`, `subscription.cancelled`, `subscription.expired`, `subscription.failed`
- Note the **webhook signing key** as `DODO_WEBHOOK_SECRET`

## 4. Environment Variables

```env
# Dodo Payments
DODO_API_KEY=<your-api-key>
DODO_WEBHOOK_SECRET=<webhook-signing-key>
DODO_STARTER_PRODUCT_ID=<product-id-from-dashboard>
DODO_PRO_PRODUCT_ID=<product-id-from-dashboard>
DODO_ENVIRONMENT=test_mode        # 'test_mode' or 'live_mode'
```

## 5. Database Changes

### Modify `users` table (add columns via Alembic migration)

```sql
ALTER TABLE users ADD COLUMN dodo_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN dodo_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50);  -- active | on_hold | cancelled | expired | null
ALTER TABLE users ADD COLUMN current_period_end TIMESTAMP;     -- when current billing period ends
```

### Update `UserModel` in db_models.py

Add 4 new fields:
```python
dodo_customer_id: Mapped[str | None] = mapped_column(String(255))
dodo_subscription_id: Mapped[str | None] = mapped_column(String(255))
subscription_status: Mapped[str | None] = mapped_column(String(50))
current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

## 6. Backend API Endpoints

### New Blueprint: `backend/app/api/billing.py`

```
POST /api/billing/checkout          # Create Dodo checkout session, return redirect URL
POST /api/billing/portal            # Create Dodo customer portal session, return URL
POST /api/billing/webhook           # Dodo webhook receiver (no auth — verified by signature)
GET  /api/billing/status            # Get current user's billing status
```

### 6.1 POST /api/billing/checkout

**Auth:** `@require_auth`

**Request:**
```json
{
    "plan": "starter" | "pro"
}
```

**Logic:**
1. Map plan to Dodo product ID (`starter` → `DODO_STARTER_PRODUCT_ID`, `pro` → `DODO_PRO_PRODUCT_ID`)
2. Create Dodo checkout session via Python SDK:
```python
from dodopayments import DodoPayments

client = DodoPayments(
    bearer_token=Config.DODO_API_KEY,
    environment=Config.DODO_ENVIRONMENT,
)

session = client.checkout_sessions.create(
    product_cart=[{"product_id": product_id, "quantity": 1}],
    customer={
        "email": user.email,
        "name": user.name,
    },
    metadata={"user_id": str(user.id)},
    return_url=f"{Config.FRONTEND_URL}/dashboard?payment=success",
)
```
3. Save `dodo_customer_id` on user if not already set
4. Return `{"checkout_url": session.checkout_url}`

**Response:**
```json
{
    "success": true,
    "checkout_url": "https://checkout.dodopayments.com/session/cks_..."
}
```

### 6.2 POST /api/billing/portal

**Auth:** `@require_auth`

**Logic:**
1. Create customer portal session for the user's `dodo_customer_id`
```python
portal = client.customers.create_customer_portal_session(
    customer_id=user.dodo_customer_id
)
```
2. Return portal URL

**Response:**
```json
{
    "success": true,
    "portal_url": "https://portal.dodopayments.com/..."
}
```

### 6.3 POST /api/billing/webhook

**Auth:** NONE (public endpoint, verified by webhook signature)

**Logic:**
1. Read raw request body
2. Verify webhook signature using `DODO_WEBHOOK_SECRET`
3. Parse event type and data
4. Handle events:

| Event | Action |
|-------|--------|
| `subscription.active` | Set `plan` based on product_id, set `subscription_status='active'`, set `current_period_end` |
| `subscription.renewed` | Update `current_period_end` to next billing date |
| `subscription.on_hold` | Set `subscription_status='on_hold'` |
| `subscription.cancelled` | Set `subscription_status='cancelled'` (keep plan active until `current_period_end`) |
| `subscription.expired` | Set `plan='expired'`, `subscription_status='expired'` |
| `subscription.failed` | Log error, set `subscription_status='failed'` |

5. Extract `user_id` from webhook metadata to find the user
6. Return 200 OK

### 6.4 GET /api/billing/status

**Auth:** `@require_auth`

**Response:**
```json
{
    "plan": "trial",
    "subscription_status": null,
    "trial_ends_at": "2026-04-02T...",
    "trial_expired": false,
    "trial_days_left": 12,
    "current_period_end": null,
    "can_create_projects": true
}
```

## 7. Frontend Changes

### 7.1 Dashboard — Upgrade Prompts

In `frontend/src/views/Dashboard.vue`:

**When trial is expired:**
- Show a full-width banner: "Your trial has expired. Upgrade to continue creating predictions."
- "Upgrade Now" button → calls `/api/billing/checkout` → redirects to Dodo checkout

**When trial is active:**
- Show trial days remaining badge (already exists)
- Add subtle "Upgrade" link in nav

**After payment success (`?payment=success` query param):**
- Show success toast: "Payment successful! Your plan is now active."
- Refresh user data from `/api/auth/me`

### 7.2 Pricing Section — Landing Page

Update `landing/index.html` pricing CTAs:
- Starter "Start Free Trial" → links to `/signup`
- Pro "Start Free Trial" → links to `/signup`
- Enterprise "Contact Sales" → `mailto:mirofish@shanda.com`

(Users sign up first, then upgrade from dashboard after trial)

### 7.3 Billing API Wrapper

Create `frontend/src/api/billing.js`:
```javascript
import service from './index'

export const createCheckout = (plan) => service.post('/api/billing/checkout', { plan })
export const createPortal = () => service.post('/api/billing/portal')
export const getBillingStatus = () => service.get('/api/billing/status')
```

### 7.4 Settings/Billing Page (Optional — Can Defer)

A simple `/settings` page showing:
- Current plan
- Subscription status
- "Manage Subscription" button → opens Dodo customer portal
- "Change Plan" button → opens checkout for different tier

## 8. Trial Enforcement Updates

The `@require_active_plan` middleware already checks trial expiry. Update it to also check subscription status:

```python
def require_active_plan(f):
    @functools.wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        user = g.current_user

        # Paid plan with active subscription — always allowed
        if user.plan in ('starter', 'pro', 'enterprise') and user.subscription_status == 'active':
            return f(*args, **kwargs)

        # Paid plan with cancelled subscription — allowed until period ends
        if user.plan in ('starter', 'pro') and user.subscription_status == 'cancelled':
            if user.current_period_end and datetime.now(timezone.utc) < user.current_period_end:
                return f(*args, **kwargs)

        # Trial — allowed if not expired
        if user.plan == 'trial' and datetime.now(timezone.utc) < user.trial_ends_at:
            return f(*args, **kwargs)

        # Everything else — blocked
        return jsonify({
            "error": "Active subscription required",
            "code": "SUBSCRIPTION_REQUIRED",
            "trial_expired": user.plan == 'trial',
        }), 403

    return decorated
```

## 9. Plan Limits (Enforced in Backend)

| Limit | Starter | Pro | Enterprise |
|-------|---------|-----|-----------|
| Simulations/month | 5 | 20 | Unlimited |
| Agents per simulation | 20 | 50 | Custom |
| Rounds per simulation | 10 | 40 | Custom |
| Report generation | Yes | Yes | Yes |
| API access | No | Yes | Yes |

Enforcement: Add a `check_plan_limits()` helper that queries simulation count for current month before allowing new simulation creation. Store limits in a config dict keyed by plan name.

## 10. Files to Create/Modify

### New Files
| File | Responsibility |
|------|---------------|
| `backend/app/api/billing.py` | Billing blueprint: checkout, portal, webhook, status |
| `frontend/src/api/billing.js` | Billing API wrapper |

### Modified Files
| File | Change |
|------|--------|
| `backend/app/models/db_models.py` | Add 4 columns to UserModel |
| `backend/app/middleware/auth.py` | Update `require_active_plan` with subscription logic |
| `backend/app/__init__.py` | Register billing blueprint |
| `backend/app/config.py` | Add DODO_* config vars |
| `backend/pyproject.toml` | Add `dodopayments` dependency |
| `frontend/src/views/Dashboard.vue` | Add upgrade prompts, payment success handling |
| `frontend/src/store/auth.js` | Add billing-related computed properties |
| `landing/index.html` | Update pricing CTA links |

## 11. Success Criteria

- [ ] User on expired trial sees upgrade prompt on dashboard
- [ ] Clicking "Upgrade" creates Dodo checkout and redirects
- [ ] After payment, webhook fires and user plan updates to 'starter' or 'pro'
- [ ] User redirected back to dashboard with success message
- [ ] Plan limits enforced (simulation count per month)
- [ ] Cancelled subscription stays active until period end
- [ ] "Manage Subscription" opens Dodo customer portal
- [ ] Webhook endpoint rejects invalid signatures
