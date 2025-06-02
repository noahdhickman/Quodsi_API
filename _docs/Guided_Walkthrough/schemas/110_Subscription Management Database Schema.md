# Quodsi Subscription Management Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's subscription management system, supporting both individual user subscriptions and organization-level subscriptions with Stripe integration. All primary data tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

## Subscription Tier Management

### `subscription_tiers`
Defines available subscription plans. (Assumed globally defined or managed under a system tenant context).

| Column             | Type              | Constraints                               | Description                                          |
| :----------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Tier identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NULL, FK to `tenants.id`* | *NULL or system tenant_id; Tiers are global (BaseEntity)*|
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Creation timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Marks if tier is discontinued (BaseEntity `is_deleted`)*|
| `name`             | VARCHAR(100)      | NOT NULL, UNIQUE                          | Plan name (Basic, Pro, Enterprise)                   |
| `description`      | NVARCHAR(MAX)     | NULL                                      | Plan description                                     |
| `tier_type`        | VARCHAR(50)       | NOT NULL                                  | Type (individual, team, enterprise)                  |
| `monthly_price`    | DECIMAL(10,2)     | NOT NULL                                  | Monthly price in USD                                 |
| `annual_price`     | DECIMAL(10,2)     | NOT NULL                                  | Annual price in USD                                  |
| `min_seats`        | INT               | NOT NULL, DEFAULT 1                       | Minimum number of seats                              |
| `max_seats`        | INT               | NULL                                      | Maximum number of seats (null = unlimited)           |
| `per_seat_price`   | DECIMAL(10,2)     | NULL                                      | Price per additional seat                            |
| `features`         | NVARCHAR(MAX)     | NOT NULL                                  | Feature flags and limits (JSON data)                 |

**Indexes:**
* `ix_subscription_tiers_index_id` CLUSTERED on `index_id`
* `ix_subscription_tiers_id` UNIQUE NONCLUSTERED on `id`
* `ix_subscription_tiers_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_subscription_tiers_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_subscription_tiers_active_type` NONCLUSTERED on (`tier_type`) WHERE `is_deleted` = 0

**Constraints:**
* `fk_subscription_tiers_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)

## Individual User Subscriptions

### `user_subscriptions`
Individual user subscription details.

| Column                   | Type              | Constraints                               | Description                                          |
| :----------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Subscription identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of subscription (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When subscription was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `user_id`                | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | Reference to user                                    |
| `subscription_tier_id`   | UNIQUEIDENTIFIER  | NOT NULL, FK to `subscription_tiers.id`   | Reference to tier                                    |
| `stripe_customer_id`     | VARCHAR(255)      | NULL                                      | Stripe customer ID                                   |
| `stripe_subscription_id` | VARCHAR(255)      | NULL, UNIQUE                              | Stripe subscription ID                               |
| `status`                 | VARCHAR(50)       | NOT NULL                                  | Status (active, past_due, canceled, trialing)        |
| `current_period_start`   | DATETIME2         | NOT NULL                                  | Current billing period start                         |
| `current_period_end`     | DATETIME2         | NOT NULL                                  | Current billing period end                           |
| `cancel_at_period_end`   | BIT               | NOT NULL, DEFAULT 0                       | Whether canceling at period end                      |
| `trial_ends_at`          | DATETIME2         | NULL                                      | Timestamp when trial period ends                     |

**Indexes:**
* `ix_user_subscriptions_index_id` CLUSTERED on `index_id`
* `ix_user_subscriptions_id` UNIQUE NONCLUSTERED on `id`
* `ix_user_subscriptions_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_user_subscriptions_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_user_subscriptions_tenant_user` UNIQUE NONCLUSTERED on (`tenant_id`, `user_id`) WHERE `is_deleted` = 0 AND `status` <> 'canceled'
* `ix_user_subscriptions_stripe_sub_id` NONCLUSTERED on (`stripe_subscription_id`) WHERE `stripe_subscription_id` IS NOT NULL

**Constraints:**
* `fk_user_subscriptions_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_user_subscriptions_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `fk_user_subscriptions_tier` FOREIGN KEY (`subscription_tier_id`) REFERENCES `subscription_tiers`(`id`)
* `ck_user_subscriptions_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))

## Organization-Level Subscriptions

### `organization_subscriptions`
Organization-level subscription details.

| Column                   | Type              | Constraints                               | Description                                       |
| :----------------------- | :---------------- | :---------------------------------------- | :------------------------------------------------ |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Subscription identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of subscription (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Subscription start date (BaseEntity `created_at`)*|
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `organization_id`        | UNIQUEIDENTIFIER  | NOT NULL, FK to `organizations.id`        | Reference to organization                         |
| `subscription_tier_id`   | UNIQUEIDENTIFIER  | NOT NULL, FK to `subscription_tiers.id`   | Reference to tier                                 |
| `seat_count`             | INT               | NOT NULL, DEFAULT 1                       | Number of seats purchased                         |
| `stripe_subscription_id` | VARCHAR(255)      | NULL, UNIQUE                              | Stripe subscription ID                            |
| `renewal_at`             | DATETIME2         | NULL                                      | Renewal date (current_period_end)                 |
| `status`                 | VARCHAR(50)       | NOT NULL                                  | Status (active, past_due, canceled, trialing)     |
| `payment_method_id`      | VARCHAR(255)      | NULL                                      | Default payment method ID (from Stripe)           |
| `cancel_at_period_end`   | BIT               | NOT NULL, DEFAULT 0                       | Whether canceling at period end                   |
| `trial_ends_at`          | DATETIME2         | NULL                                      | Timestamp when trial period ends                  |

**Indexes:**
* `ix_organization_subscriptions_index_id` CLUSTERED on `index_id`
* `ix_organization_subscriptions_id` UNIQUE NONCLUSTERED on `id`
* `ix_organization_subscriptions_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_organization_subscriptions_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_organization_subscriptions_tenant_org` UNIQUE NONCLUSTERED on (`tenant_id`, `organization_id`) WHERE `is_deleted` = 0 AND `status` <> 'canceled'
* `ix_organization_subscriptions_stripe_sub_id` NONCLUSTERED on (`stripe_subscription_id`) WHERE `stripe_subscription_id` IS NOT NULL

**Constraints:**
* `fk_organization_subscriptions_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_organization_subscriptions_organization` FOREIGN KEY (`organization_id`) REFERENCES `organizations`(`id`)
* `fk_organization_subscriptions_tier` FOREIGN KEY (`subscription_tier_id`) REFERENCES `subscription_tiers`(`id`)
* `ck_org_subscriptions_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `organizations` WHERE `id` = `organization_id`))

## Subscription Events and History

### `subscription_events`
Tracks subscription lifecycle events for auditing and analytics.

| Column                   | Type              | Constraints                               | Description                                       |
| :----------------------- | :---------------- | :---------------------------------------- | :------------------------------------------------ |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Event identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the event (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When event occurred (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `subscription_type`      | VARCHAR(20)       | NOT NULL                                  | Type (user, organization)                         |
| `subscription_id`        | UNIQUEIDENTIFIER  | NOT NULL                                  | Reference to subscription (user or org)           |
| `event_type`             | VARCHAR(50)       | NOT NULL                                  | Event type (created, upgraded, canceled, etc.)    |
| `old_status`             | VARCHAR(50)       | NULL                                      | Previous subscription status                      |
| `new_status`             | VARCHAR(50)       | NOT NULL                                  | New subscription status                           |
| `old_tier_id`            | UNIQUEIDENTIFIER  | NULL, FK to `subscription_tiers.id`       | Previous tier (for upgrades/downgrades)          |
| `new_tier_id`            | UNIQUEIDENTIFIER  | NOT NULL, FK to `subscription_tiers.id`   | New tier                                          |
| `stripe_event_id`        | VARCHAR(255)      | NULL                                      | Corresponding Stripe event ID                     |
| `initiated_by_user_id`   | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | User who initiated the change                     |
| `event_data`             | NVARCHAR(MAX)     | NULL                                      | Additional event details (JSON)                   |

**Indexes:**
* `ix_subscription_events_index_id` CLUSTERED on `index_id`
* `ix_subscription_events_id` UNIQUE NONCLUSTERED on `id`
* `ix_subscription_events_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_subscription_events_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_subscription_events_subscription` NONCLUSTERED on (`tenant_id`, `subscription_type`, `subscription_id`, `created_at` DESC)
* `ix_subscription_events_stripe_event` NONCLUSTERED on (`stripe_event_id`) WHERE `stripe_event_id` IS NOT NULL

**Constraints:**
* `fk_subscription_events_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_subscription_events_old_tier` FOREIGN KEY (`old_tier_id`) REFERENCES `subscription_tiers`(`id`)
* `fk_subscription_events_new_tier` FOREIGN KEY (`new_tier_id`) REFERENCES `subscription_tiers`(`id`)
* `fk_subscription_events_initiated_by` FOREIGN KEY (`initiated_by_user_id`) REFERENCES `users`(`id`)

## Billing and Payment History

### `payment_transactions`
Records of payments and billing transactions.

| Column                   | Type              | Constraints                               | Description                                       |
| :----------------------- | :---------------- | :---------------------------------------- | :------------------------------------------------ |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Transaction identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the transaction (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Transaction timestamp (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `subscription_type`      | VARCHAR(20)       | NOT NULL                                  | Type (user, organization)                         |
| `subscription_id`        | UNIQUEIDENTIFIER  | NOT NULL                                  | Reference to subscription                         |
| `stripe_invoice_id`      | VARCHAR(255)      | NULL                                      | Stripe invoice ID                                 |
| `stripe_payment_intent_id`| VARCHAR(255)     | NULL                                      | Stripe payment intent ID                          |
| `amount`                 | DECIMAL(10,2)     | NOT NULL                                  | Transaction amount                                |
| `currency`               | CHAR(3)           | NOT NULL, DEFAULT 'USD'                   | Currency code                                     |
| `transaction_type`       | VARCHAR(50)       | NOT NULL                                  | Type (payment, refund, adjustment)                |
| `status`                 | VARCHAR(50)       | NOT NULL                                  | Status (succeeded, failed, pending)               |
| `description`            | NVARCHAR(255)     | NULL                                      | Transaction description                           |
| `failure_reason`         | NVARCHAR(MAX)     | NULL                                      | Reason for failed transactions                    |
| `metadata`               | NVARCHAR(MAX)     | NULL                                      | Additional transaction data (JSON)                |

**Indexes:**
* `ix_payment_transactions_index_id` CLUSTERED on `index_id`
* `ix_payment_transactions_id` UNIQUE NONCLUSTERED on `id`
* `ix_payment_transactions_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_payment_transactions_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_payment_transactions_subscription` NONCLUSTERED on (`tenant_id`, `subscription_type`, `subscription_id`, `created_at` DESC)
* `ix_payment_transactions_stripe_invoice` NONCLUSTERED on (`stripe_invoice_id`) WHERE `stripe_invoice_id` IS NOT NULL
* `ix_payment_transactions_status` NONCLUSTERED on (`tenant_id`, `status`, `created_at` DESC)

**Constraints:**
* `fk_payment_transactions_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)

## Usage-Based Billing

### `usage_records`
Tracks usage metrics for usage-based billing components.

| Column                   | Type              | Constraints                               | Description                                       |
| :----------------------- | :---------------- | :---------------------------------------- | :------------------------------------------------ |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Usage record identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of usage (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When usage was recorded (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `subscription_type`      | VARCHAR(20)       | NOT NULL                                  | Type (user, organization)                         |
| `subscription_id`        | UNIQUEIDENTIFIER  | NOT NULL                                  | Reference to subscription                         |
| `usage_type`             | VARCHAR(50)       | NOT NULL                                  | Type (api_calls, storage_gb, scenarios_run)       |
| `usage_period_start`     | DATE              | NOT NULL                                  | Start of usage period                             |
| `usage_period_end`       | DATE              | NOT NULL                                  | End of usage period                               |
| `quantity`               | DECIMAL(15,6)     | NOT NULL                                  | Amount of usage                                   |
| `unit_price`             | DECIMAL(10,6)     | NOT NULL                                  | Price per unit                                    |
| `total_cost`             | DECIMAL(10,2)     | NOT NULL                                  | Total cost for this usage                         |
| `stripe_usage_record_id` | VARCHAR(255)      | NULL                                      | Corresponding Stripe usage record                 |
| `billing_month`          | DATE              | NOT NULL                                  | Month this usage will be billed                   |

**Indexes:**
* `ix_usage_records_index_id` CLUSTERED on `index_id`
* `ix_usage_records_id` UNIQUE NONCLUSTERED on `id`
* `ix_usage_records_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_usage_records_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_usage_records_subscription_period` NONCLUSTERED on (`tenant_id`, `subscription_type`, `subscription_id`, `usage_period_start`, `usage_period_end`)
* `ix_usage_records_billing_month` NONCLUSTERED on (`tenant_id`, `billing_month`, `usage_type`)

**Constraints:**
* `fk_usage_records_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)

## Related Schema Files

This Subscription Management schema works in conjunction with:

- **User Management**: `User Management Database Schema.md` - Contains `users` and `organizations` tables
- **Multi-Tenant Management**: `Multi-Tenant Management Tables.md` - Contains the `tenants` table and tenant-specific configurations
- **Cloud Connection Management**: `Cloud Connection Management Database Schema.md` - Contains cloud storage integrations

## Notes

- All tables follow the multi-tenant BaseEntity pattern for consistency and performance
- Supports both individual user subscriptions and organization-level subscriptions
- Comprehensive Stripe integration for payment processing
- Usage-based billing support for overage charges
- Complete audit trail of all subscription changes and payment events
- Foreign key relationships maintain tenant consistency through check constraints
- Indexes optimized for tenant-scoped queries and billing operations
