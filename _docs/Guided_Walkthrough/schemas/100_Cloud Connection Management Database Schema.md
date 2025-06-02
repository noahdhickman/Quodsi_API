# Quodsi Cloud Connection Management Database Schema (Multi-Tenant with BaseEntity)

This document outlines the database schema design for Quodsi's cloud storage integration system, supporting OAuth connections to cloud storage providers like OneDrive, Google Drive, and configured folder management. All primary data tables derive from a `BaseEntity` structure.

**BaseEntity Standard Fields**:
Each table listed below, unless otherwise specified, includes the following fields from `BaseEntity`:
* `id` (UNIQUEIDENTIFIER, PK NONCLUSTERED, DEFAULT NEWID())
* `index_id` (BIGINT, IDENTITY(1,1) NOT NULL, CLUSTERED INDEX)
* `tenant_id` (UNIQUEIDENTIFIER, NOT NULL, FK to `tenants.id`)
* `created_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `updated_at` (DATETIME2, NOT NULL, DEFAULT GETDATE())
* `is_deleted` (BIT, NOT NULL, DEFAULT 0)

## Cloud Storage Connections

### `cloud_connections`
Stores OAuth connections to cloud storage providers.

| Column                    | Type              | Constraints                               | Description                                             |
| :------------------------ | :---------------- | :---------------------------------------- | :------------------------------------------------------ |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Connection identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the connection (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When connection was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `user_id`                 | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | Reference to user                                       |
| `provider_type`           | VARCHAR(50)       | NOT NULL                                  | Provider type (onedrive, gdrive, dropbox, box)          |
| `provider_user_id`        | VARCHAR(255)      | NOT NULL                                  | User ID in the provider                                 |
| `provider_user_email`     | VARCHAR(255)      | NULL                                      | User's email in the provider                           |
| `encrypted_access_token`  | VARBINARY(MAX)    | NOT NULL                                  | Encrypted access token                                  |
| `encrypted_refresh_token` | VARBINARY(MAX)    | NULL                                      | Encrypted refresh token                                 |
| `token_expiry`            | DATETIME2         | NOT NULL                                  | Token expiration timestamp                              |
| `scope`                   | NVARCHAR(MAX)     | NOT NULL                                  | OAuth scopes granted                                    |
| `last_used_at`            | DATETIME2         | NULL                                      | Last connection usage                                   |
| `last_sync_at`            | DATETIME2         | NULL                                      | Last successful sync operation                          |
| `status`                  | VARCHAR(20)       | NOT NULL, DEFAULT 'active'                | Status (active, revoked, expired, error)                |
| `display_name`            | NVARCHAR(255)     | NULL                                      | User-friendly name for the connection                   |
| `connection_metadata`     | NVARCHAR(MAX)     | NULL                                      | Provider-specific metadata (JSON)                       |

**Indexes:**
* `ix_cloud_connections_index_id` CLUSTERED on `index_id`
* `ix_cloud_connections_id` UNIQUE NONCLUSTERED on `id`
* `ix_cloud_connections_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_cloud_connections_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_cloud_connections_tenant_user_provider` UNIQUE NONCLUSTERED on (`tenant_id`, `user_id`, `provider_type`, `provider_user_id`) WHERE `is_deleted` = 0
* `ix_cloud_connections_status` NONCLUSTERED on (`tenant_id`, `status`) WHERE `is_deleted` = 0
* `ix_cloud_connections_token_expiry` NONCLUSTERED on (`token_expiry`) WHERE `status` = 'active'

**Constraints:**
* `fk_cloud_connections_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_cloud_connections_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
* `ck_cloud_connections_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `users` WHERE `id` = `user_id`))
* `ck_cloud_connections_provider_type` CHECK (`provider_type` IN ('onedrive', 'gdrive', 'dropbox', 'box', 'sharepoint'))

## Folder Configuration

### `cloud_folders`
Configured folders in cloud storage services.

| Column                     | Type              | Constraints                               | Description                                          |
| :------------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Folder configuration identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the folder config (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When folder was configured (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `connection_id`            | UNIQUEIDENTIFIER  | NOT NULL, FK to `cloud_connections.id`    | Reference to cloud connection                        |
| `folder_name`              | VARCHAR(255)      | NOT NULL                                  | Display name for folder                              |
| `provider_folder_id`       | VARCHAR(255)      | NOT NULL                                  | Folder ID in cloud provider                          |
| `folder_path`              | NVARCHAR(MAX)     | NULL                                      | Full path to folder                                  |
| `folder_type`              | VARCHAR(50)       | NOT NULL                                  | Purpose (export, import, archive, models)            |
| `is_default_export_folder` | BIT               | NOT NULL, DEFAULT 0                       | Whether this is the default for exports              |
| `is_default_import_folder` | BIT               | NOT NULL, DEFAULT 0                       | Whether this is the default for imports              |
| `auto_sync_enabled`        | BIT               | NOT NULL, DEFAULT 0                       | Whether auto-sync is enabled for this folder        |
| `last_sync_at`             | DATETIME2         | NULL                                      | Last successful sync operation                       |
| `sync_frequency_minutes`   | INT               | NULL                                      | Auto-sync frequency in minutes                       |
| `folder_permissions`       | VARCHAR(50)       | NOT NULL, DEFAULT 'read_write'            | Permissions (read_only, read_write, write_only)      |

**Indexes:**
* `ix_cloud_folders_index_id` CLUSTERED on `index_id`
* `ix_cloud_folders_id` UNIQUE NONCLUSTERED on `id`
* `ix_cloud_folders_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_cloud_folders_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_cloud_folders_tenant_connection` NONCLUSTERED on (`tenant_id`, `connection_id`) WHERE `is_deleted` = 0
* `ix_cloud_folders_provider_folder` UNIQUE NONCLUSTERED on (`connection_id`, `provider_folder_id`) WHERE `is_deleted` = 0
* `ix_cloud_folders_default_export` NONCLUSTERED on (`tenant_id`, `connection_id`) WHERE `is_default_export_folder` = 1 AND `is_deleted` = 0
* `ix_cloud_folders_auto_sync` NONCLUSTERED on (`auto_sync_enabled`, `sync_frequency_minutes`) WHERE `auto_sync_enabled` = 1 AND `is_deleted` = 0

**Constraints:**
* `fk_cloud_folders_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_cloud_folders_connection` FOREIGN KEY (`connection_id`) REFERENCES `cloud_connections`(`id`)
* `ck_cloud_folders_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `cloud_connections` WHERE `id` = `connection_id`))
* `ck_cloud_folders_folder_type` CHECK (`folder_type` IN ('export', 'import', 'archive', 'models', 'results', 'general'))
* `ck_cloud_folders_permissions` CHECK (`folder_permissions` IN ('read_only', 'read_write', 'write_only'))

## File Synchronization

### `cloud_sync_jobs`
Tracks synchronization jobs between Quodsi and cloud storage.

| Column                     | Type              | Constraints                               | Description                                          |
| :------------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Sync job identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the sync job (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When sync job was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `folder_id`                | UNIQUEIDENTIFIER  | NOT NULL, FK to `cloud_folders.id`        | Reference to cloud folder                            |
| `initiated_by_user_id`     | UNIQUEIDENTIFIER  | NULL, FK to `users.id`                    | User who initiated the sync (null for auto-sync)     |
| `job_type`                 | VARCHAR(50)       | NOT NULL                                  | Type (upload, download, bidirectional)               |
| `status`                   | VARCHAR(50)       | NOT NULL, DEFAULT 'pending'               | Status (pending, running, completed, failed)         |
| `started_at`               | DATETIME2         | NULL                                      | When sync job actually started                       |
| `completed_at`             | DATETIME2         | NULL                                      | When sync job completed                              |
| `progress_percentage`      | DECIMAL(5,2)      | NOT NULL, DEFAULT 0                       | Job progress (0-100)                                 |
| `files_processed`          | INT               | NOT NULL, DEFAULT 0                       | Number of files processed                            |
| `files_total`              | INT               | NULL                                      | Total number of files to process                     |
| `bytes_transferred`        | BIGINT            | NOT NULL, DEFAULT 0                       | Total bytes transferred                              |
| `error_message`            | NVARCHAR(MAX)     | NULL                                      | Error message if job failed                          |
| `job_metadata`             | NVARCHAR(MAX)     | NULL                                      | Additional job details (JSON)                        |

**Indexes:**
* `ix_cloud_sync_jobs_index_id` CLUSTERED on `index_id`
* `ix_cloud_sync_jobs_id` UNIQUE NONCLUSTERED on `id`
* `ix_cloud_sync_jobs_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_cloud_sync_jobs_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_cloud_sync_jobs_folder_status` NONCLUSTERED on (`tenant_id`, `folder_id`, `status`, `created_at` DESC)
* `ix_cloud_sync_jobs_status_created` NONCLUSTERED on (`status`, `created_at` DESC)
* `ix_cloud_sync_jobs_running` NONCLUSTERED on (`status`) WHERE `status` IN ('pending', 'running')

**Constraints:**
* `fk_cloud_sync_jobs_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_cloud_sync_jobs_folder` FOREIGN KEY (`folder_id`) REFERENCES `cloud_folders`(`id`)
* `fk_cloud_sync_jobs_initiated_by` FOREIGN KEY (`initiated_by_user_id`) REFERENCES `users`(`id`)
* `ck_cloud_sync_jobs_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `cloud_folders` WHERE `id` = `folder_id`))
* `ck_cloud_sync_jobs_job_type` CHECK (`job_type` IN ('upload', 'download', 'bidirectional', 'export', 'import'))
* `ck_cloud_sync_jobs_status` CHECK (`status` IN ('pending', 'running', 'completed', 'failed', 'cancelled'))

### `cloud_files`
Tracks files that have been synchronized with cloud storage.

| Column                     | Type              | Constraints                               | Description                                          |
| :------------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *File record identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the file (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When file record was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `folder_id`                | UNIQUEIDENTIFIER  | NOT NULL, FK to `cloud_folders.id`        | Reference to cloud folder                            |
| `quodsi_file_type`         | VARCHAR(50)       | NOT NULL                                  | Type (model, result, animation, export)              |
| `quodsi_entity_id`         | UNIQUEIDENTIFIER  | NULL                                      | Related Quodsi entity (model_id, scenario_id, etc.)  |
| `provider_file_id`         | VARCHAR(255)      | NOT NULL                                  | File ID in cloud provider                            |
| `file_name`                | NVARCHAR(255)     | NOT NULL                                  | Name of the file                                     |
| `file_path`                | NVARCHAR(MAX)     | NULL                                      | Full path to file in cloud storage                   |
| `file_size_bytes`          | BIGINT            | NOT NULL                                  | File size in bytes                                   |
| `content_hash`             | VARCHAR(64)       | NULL                                      | Hash of file content for change detection            |
| `mime_type`                | VARCHAR(255)      | NULL                                      | MIME type of the file                                |
| `cloud_created_at`         | DATETIME2         | NULL                                      | When file was created in cloud storage               |
| `cloud_modified_at`        | DATETIME2         | NULL                                      | When file was last modified in cloud storage         |
| `last_synced_at`           | DATETIME2         | NULL                                      | When file was last synchronized                      |
| `sync_status`              | VARCHAR(50)       | NOT NULL, DEFAULT 'synced'                | Status (synced, needs_upload, needs_download, conflict) |
| `upload_url`               | NVARCHAR(MAX)     | NULL                                      | Temporary upload URL if applicable                    |
| `download_url`             | NVARCHAR(MAX)     | NULL                                      | Temporary download URL if applicable                  |
| `file_metadata`            | NVARCHAR(MAX)     | NULL                                      | Additional file metadata (JSON)                       |

**Indexes:**
* `ix_cloud_files_index_id` CLUSTERED on `index_id`
* `ix_cloud_files_id` UNIQUE NONCLUSTERED on `id`
* `ix_cloud_files_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_cloud_files_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_cloud_files_folder_type` NONCLUSTERED on (`tenant_id`, `folder_id`, `quodsi_file_type`)
* `ix_cloud_files_provider_file` UNIQUE NONCLUSTERED on (`folder_id`, `provider_file_id`) WHERE `is_deleted` = 0
* `ix_cloud_files_entity` NONCLUSTERED on (`tenant_id`, `quodsi_entity_id`, `quodsi_file_type`) WHERE `quodsi_entity_id` IS NOT NULL
* `ix_cloud_files_sync_status` NONCLUSTERED on (`sync_status`, `last_synced_at`) WHERE `sync_status` <> 'synced'
* `ix_cloud_files_content_hash` NONCLUSTERED on (`content_hash`) WHERE `content_hash` IS NOT NULL

**Constraints:**
* `fk_cloud_files_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_cloud_files_folder` FOREIGN KEY (`folder_id`) REFERENCES `cloud_folders`(`id`)
* `ck_cloud_files_tenant_consistency` CHECK (`tenant_id` = (SELECT `tenant_id` FROM `cloud_folders` WHERE `id` = `folder_id`))
* `ck_cloud_files_file_type` CHECK (`quodsi_file_type` IN ('model', 'result', 'animation', 'export', 'import', 'document', 'image'))
* `ck_cloud_files_sync_status` CHECK (`sync_status` IN ('synced', 'needs_upload', 'needs_download', 'conflict', 'error'))

## Access Control and Sharing

### `cloud_shared_links`
Manages shared links for cloud files and folders.

| Column                     | Type              | Constraints                               | Description                                          |
| :------------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Shared link identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the shared link (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When shared link was created (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `created_by_user_id`       | UNIQUEIDENTIFIER  | NOT NULL, FK to `users.id`                | User who created the shared link                     |
| `resource_type`            | VARCHAR(20)       | NOT NULL                                  | Type (file, folder)                                  |
| `file_id`                  | UNIQUEIDENTIFIER  | NULL, FK to `cloud_files.id`             | Reference to file (if resource_type = 'file')        |
| `folder_id`                | UNIQUEIDENTIFIER  | NULL, FK to `cloud_folders.id`           | Reference to folder (if resource_type = 'folder')    |
| `provider_share_id`        | VARCHAR(255)      | NULL                                      | Share ID from cloud provider                         |
| `share_url`                | NVARCHAR(MAX)     | NOT NULL                                  | The actual shared URL                                |
| `share_type`               | VARCHAR(50)       | NOT NULL                                  | Type (view, edit, download)                          |
| `password_protected`       | BIT               | NOT NULL, DEFAULT 0                       | Whether link is password protected                   |
| `expires_at`               | DATETIME2         | NULL                                      | When shared link expires                             |
| `access_count`             | INT               | NOT NULL, DEFAULT 0                       | Number of times link has been accessed               |
| `last_accessed_at`         | DATETIME2         | NULL                                      | When link was last accessed                          |
| `is_active`                | BIT               | NOT NULL, DEFAULT 1                       | Whether link is currently active                     |

**Indexes:**
* `ix_cloud_shared_links_index_id` CLUSTERED on `index_id`
* `ix_cloud_shared_links_id` UNIQUE NONCLUSTERED on `id`
* `ix_cloud_shared_links_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_cloud_shared_links_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_cloud_shared_links_file` NONCLUSTERED on (`tenant_id`, `file_id`) WHERE `file_id` IS NOT NULL AND `is_deleted` = 0
* `ix_cloud_shared_links_folder` NONCLUSTERED on (`tenant_id`, `folder_id`) WHERE `folder_id` IS NOT NULL AND `is_deleted` = 0
* `ix_cloud_shared_links_expires` NONCLUSTERED on (`expires_at`) WHERE `expires_at` IS NOT NULL AND `is_active` = 1

**Constraints:**
* `fk_cloud_shared_links_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_cloud_shared_links_created_by` FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)
* `fk_cloud_shared_links_file` FOREIGN KEY (`file_id`) REFERENCES `cloud_files`(`id`)
* `fk_cloud_shared_links_folder` FOREIGN KEY (`folder_id`) REFERENCES `cloud_folders`(`id`)
* `ck_cloud_shared_links_resource` CHECK ((`resource_type` = 'file' AND `file_id` IS NOT NULL AND `folder_id` IS NULL) OR (`resource_type` = 'folder' AND `folder_id` IS NOT NULL AND `file_id` IS NULL))
* `ck_cloud_shared_links_share_type` CHECK (`share_type` IN ('view', 'edit', 'download', 'comment'))

## Error Tracking and Logging

### `cloud_sync_errors`
Tracks synchronization errors for troubleshooting.

| Column                     | Type              | Constraints                               | Description                                          |
| :------------------------- | :---------------- | :---------------------------------------- | :--------------------------------------------------- |
| *`id`* | *UNIQUEIDENTIFIER*| *PK NONCLUSTERED, DEFAULT NEWID()* | *Error record identifier (BaseEntity)* |
| *`index_id`* | *BIGINT* | *IDENTITY(1,1), NOT NULL, CLUSTERED INDEX*| *Physical ordering key (BaseEntity)* |
| *`tenant_id`* | *UNIQUEIDENTIFIER*| *NOT NULL, FK to `tenants.id`* | *Tenant context of the error (BaseEntity)* |
| *`created_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *When error occurred (BaseEntity)* |
| *`updated_at`* | *DATETIME2* | *NOT NULL, DEFAULT GETDATE()* | *Last update timestamp (BaseEntity)* |
| *`is_deleted`* | *BIT* | *NOT NULL, DEFAULT 0* | *Soft delete flag (BaseEntity)* |
| `sync_job_id`              | UNIQUEIDENTIFIER  | NULL, FK to `cloud_sync_jobs.id`          | Related sync job (if applicable)                     |
| `connection_id`            | UNIQUEIDENTIFIER  | NOT NULL, FK to `cloud_connections.id`    | Related cloud connection                             |
| `file_id`                  | UNIQUEIDENTIFIER  | NULL, FK to `cloud_files.id`             | Related file (if applicable)                         |
| `error_type`               | VARCHAR(50)       | NOT NULL                                  | Type (auth, network, quota, permission, api)         |
| `error_code`               | VARCHAR(100)      | NULL                                      | Provider-specific error code                         |
| `error_message`            | NVARCHAR(MAX)     | NOT NULL                                  | Human-readable error message                         |
| `stack_trace`              | NVARCHAR(MAX)     | NULL                                      | Technical stack trace                                |
| `retry_count`              | INT               | NOT NULL, DEFAULT 0                       | Number of retry attempts                             |
| `resolved_at`              | DATETIME2         | NULL                                      | When error was resolved                              |
| `resolution_notes`         | NVARCHAR(MAX)     | NULL                                      | Notes about error resolution                         |
| `error_metadata`           | NVARCHAR(MAX)     | NULL                                      | Additional error context (JSON)                      |

**Indexes:**
* `ix_cloud_sync_errors_index_id` CLUSTERED on `index_id`
* `ix_cloud_sync_errors_id` UNIQUE NONCLUSTERED on `id`
* `ix_cloud_sync_errors_tenant_active` NONCLUSTERED on (`tenant_id`, `index_id`) WHERE `is_deleted` = 0
* `ix_cloud_sync_errors_tenant_id_lookup` NONCLUSTERED on (`tenant_id`, `id`)
* `ix_cloud_sync_errors_connection_type` NONCLUSTERED on (`tenant_id`, `connection_id`, `error_type`, `created_at` DESC)
* `ix_cloud_sync_errors_unresolved` NONCLUSTERED on (`error_type`, `created_at` DESC) WHERE `resolved_at` IS NULL
* `ix_cloud_sync_errors_sync_job` NONCLUSTERED on (`sync_job_id`) WHERE `sync_job_id` IS NOT NULL

**Constraints:**
* `fk_cloud_sync_errors_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants`(`id`)
* `fk_cloud_sync_errors_sync_job` FOREIGN KEY (`sync_job_id`) REFERENCES `cloud_sync_jobs`(`id`)
* `fk_cloud_sync_errors_connection` FOREIGN KEY (`connection_id`) REFERENCES `cloud_connections`(`id`)
* `fk_cloud_sync_errors_file` FOREIGN KEY (`file_id`) REFERENCES `cloud_files`(`id`)
* `ck_cloud_sync_errors_error_type` CHECK (`error_type` IN ('auth', 'network', 'quota', 'permission', 'api', 'validation', 'timeout'))

## Related Schema Files

This Cloud Connection Management schema works in conjunction with:

- **User Management**: `User Management Database Schema.md` - Contains `users` table
- **Multi-Tenant Management**: `Multi-Tenant Management Tables.md` - Contains the `tenants` table and tenant-specific configurations
- **Subscription Management**: `Subscription Management Database Schema.md` - Contains subscription details that may affect cloud storage quotas

## Notes

- All tables follow the multi-tenant BaseEntity pattern for consistency and performance
- Supports multiple cloud storage providers with OAuth 2.0 authentication
- Comprehensive file synchronization tracking with conflict resolution
- Shared link management for collaboration features
- Detailed error tracking and logging for troubleshooting
- Foreign key relationships maintain tenant consistency through check constraints
- Indexes optimized for tenant-scoped queries and sync operations
- Security considerations include encrypted token storage and access logging
- Auto-sync capabilities with configurable frequencies
- Support for different folder types and permissions levels
