**Phase 2: First Login and Onboarding**

5.  **User Signs In:**
    * The user returns to `www.quodsi.com` (or is redirected after verification) and clicks a "Sign In" or "Login" button.
    * They enter their email and password or use the federated login option.
    * Upon successful authentication:
        * A new record is created in the `user_sessions` table, capturing `user_id`, `tenant_id` (their primary tenant), `session_start_time` (`created_at` [cite: 1219]), `client_info`, and `ip_address`. [cite: 1212, 1218, 1222, 1235, 1238]
        * The `users` table is updated: `last_login_at` is set to the current time, `login_count` is incremented. [cite: 1190, 1193] `last_session_start` and `last_active_at` are also updated. [cite: 1200, 1202]

6.  **Dashboard & Initial Experience:**
    * The user is redirected to their Quodsi dashboard.
    * They might be presented with a welcome message or an interactive onboarding tour.
    * During the trial period, they can explore features like:
        * Creating models (populating `models`[cite: 365], `entities`[cite: 446], `resources`[cite: 471], `activities`[cite: 501], etc., all linked via `tenant_id` [cite: 372, 453, 478, 508]).
        * Running analyses and scenarios (populating `analyses`[cite: 1039], `scenarios` [cite: 1067]).
    * Their activity contributes to `user_usage_stats` which would be aggregated periodically. [cite: 1242]

