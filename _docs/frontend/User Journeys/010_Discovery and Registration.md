# Quodsi New User Journey: Registration to Subscription

Here's a breakdown of a typical user flow:

**Phase 1: Discovery and Registration**

1.  **User Visits Website:**
    * The user opens their browser and navigates to `www.quodsi.com`.
    * They explore the homepage, learning about Quodsi's features (Model Analysis, 2D Animation Viewer).
    * They find a "Sign Up," "Register," or "Start Free Trial" call-to-action button.

2.  **Initiates Registration:**
    * The user clicks the registration button.
    * They are presented with a registration form.

3.  **Account Creation:**
    * The user provides necessary information:
        * Full Name
        * Email Address (this will be a key identifier).
        * Password (securely hashed and stored).
    * Alternatively, Quodsi might offer federated identity options like "Sign up with Microsoft Entra ID" or "Sign up with Google." In this case, Quodsi would retrieve the email and name from the identity provider.
    * Upon submission:
        * A new record is created in the `users` table.
            * `identity_provider` and `identity_provider_id` are populated. [cite: 1179, 1181]
            * `email` and `display_name` are stored. [cite: 1184, 1187]
            * `status` might initially be 'invited' or 'pending_verification' if email verification is used, or 'active' if registration is immediate. [cite: 1206]
        * A new tenant is created in the `tenants` table.
            * A unique `name`, `subdomain`, and `slug` might be auto-generated or based on user input (e.g., company name). [cite: 703, 706, 709]
            * The `plan_type` defaults to 'trial'. [cite: 223, 712]
            * Default limits like `max_users`, `max_models`, `max_scenarios_per_month`, `max_storage_gb` for the trial plan are set. [cite: 223, 224, 714, 718, 722, 725]
            * `status` is set to 'trial'. [cite: 224, 728]
            * `trial_expires_at` (or `trial_expires` [cite: 224]) is populated with a future date. [cite: 731]
        * The `tenant_id` in the new `users` record is set to the ID of the newly created tenant. [cite: 175, 62]
        * An initial record in `tenant_settings` is created, linked to the new `tenant_id`. [cite: 227, 751] This might include default `company_name` and `features` JSON. [cite: 228, 755, 770]
        * An initial record in `tenant_usage` for the current month/year is created for the new tenant, with usage metrics set to zero. [cite: 232, 244, 788, 798, 801, 804, 807, 810, 814]
        * A record in `tenant_user_roles` is created, assigning the new user a default high-privilege role (e.g., 'owner' or 'admin') for this new tenant. [cite: 195, 236, 821] This grant includes associated permissions like `can_invite_users`, `can_manage_settings`, etc. [cite: 237, 837, 843]

4.  **Email Verification (Recommended):**
    * The system sends a verification email to the user's provided email address.
    * The user clicks a link in the email to verify their account.
    * The `users.status` might be updated from 'pending_verification' to 'active'. [cite: 1206] (This step is a common SaaS practice, though not explicitly detailed as a table field change in the provided docs).

