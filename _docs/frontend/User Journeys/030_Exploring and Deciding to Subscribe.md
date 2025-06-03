**Phase 3: Exploring and Deciding to Subscribe**

7.  **Trial Usage & Limitations:**
    * The user utilizes Quodsi within the limits of the 'trial' plan (e.g., number of models, scenarios). [cite: 223, 712]
    * The system might display reminders about the trial period ending (`tenants.trial_expires_at` [cite: 731] or `tenants.trial_expires` [cite: 224]) or usage approaching limits (`tenant_usage` [cite: 232, 788] vs `tenants` plan limits [cite: 223, 224, 714, 718, 722, 725]).

8.  **Decision to Subscribe:**
    * The user decides to upgrade to a paid plan, possibly by clicking an "Upgrade," "Subscribe," or "Manage Subscription" button. This could be due to:
        * Approaching trial expiration.
        * Hitting usage limits.
        * Needing features not available in the trial (defined in `tenant_settings.features` [cite: 228, 770] or implicitly by plan).

