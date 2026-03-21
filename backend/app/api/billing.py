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
    'trial': {'simulations_per_month': 3, 'max_agents': 20, 'max_rounds': 5, 'sim_hours': 24, 'agents_per_hour_max': 15, 'minutes_per_round': 120},
    'starter': {'simulations_per_month': 5, 'max_agents': 20, 'max_rounds': 5, 'sim_hours': 24, 'agents_per_hour_max': 15, 'minutes_per_round': 120},
    'pro': {'simulations_per_month': 20, 'max_agents': 50, 'max_rounds': 10, 'sim_hours': 72, 'agents_per_hour_max': 30, 'minutes_per_round': 60},
    'enterprise': {'simulations_per_month': 999, 'max_agents': 200, 'max_rounds': 20, 'sim_hours': 168, 'agents_per_hour_max': 50, 'minutes_per_round': 30},
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
