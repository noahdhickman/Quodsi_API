**Phase 4: Subscription Process**

9.  **Selects Subscription Plan:**
    * The user is presented with available subscription plans (e.g., Starter, Professional, Enterprise) sourced from the `subscription_tiers` table. [cite: 1374] This table details `name`, `description`, `monthly_price`, `annual_price`, `features`, and limits like `max_seats`. [cite: 1385, 1388, 1394, 1397, 1404, 1411]
    * The user selects their desired plan.

10. **Payment Information:**
    * The user is prompted to enter billing information. This will likely be handled via an integration with a payment processor like Stripe.
    * The `stripe_customer_id` in the `tenants` table [cite: 225, 738] (or `organizations` table [cite: 1297] if it's an organizational subscription) is created/updated.
    * `billing_email` in the `tenants` table may also be confirmed/updated. [cite: 225, 742]

11. **Subscription Confirmation & Activation:**
    * Upon successful payment:
        * A record is created/updated in the `user_subscriptions` table [cite: 1414] (if it's a per-user subscription model) or more likely the `organization_subscriptions` table [cite: 1451] (if the tenant represents an organization subscribing).
            * This record links the `user_id` (for user subscription) [cite: 1424] or `organization_id` (derived from `tenant_id`) [cite: 1461] to the chosen `subscription_tier_id`. [cite: 1426, 1463]
            * Stripe-specific IDs like `stripe_subscription_id` are stored. [cite: 1432, 1470]
            * `status` is set to 'active'. [cite: 1435, 1477]
            * `current_period_start` and `current_period_end` (or `renewal_at` [cite: 1473]) are set. [cite: 1437, 1441]
        * The `tenants` table for the user's tenant is updated:
            * `plan_type` changes from 'trial' to the selected plan. [cite: 223, 712]
            * `status` changes from 'trial' to 'active'. [cite: 224, 728]
            * `max_users`, `max_models`, `max_scenarios_per_month`, `max_storage_gb` are updated according to the new plan. [cite: 223, 224, 714, 718, 722, 725]
            * `trial_expires_at` (or `trial_expires` [cite: 224]) might be nulled out or ignored. [cite: 731]
            * `activated_at` timestamp is set. [cite: 224, 735]
    * The user receives a confirmation message (in-app and/or via email) about their successful subscription.
    * Access to features and limits are adjusted according to the new subscription tier.

This journey outlines the key steps and how the database schema you've designed would support them. Audit logs (`audit_logs` table [cite: 1554]) would ideally capture many of these events (user registration, login, subscription changes, etc.) for security and analytical purposes, linking them to the `user_id` [cite: 1564] and `tenant_id`[cite: 1560].