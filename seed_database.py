#!/usr/bin/env python3
"""
Database Seeding Script for Quodsi API

This script seeds the database with sample data for testing and development.
It creates tenants, users, organizations, and memberships using the application's
Services and Repositories to ensure data integrity and proper business logic.

Usage:
    python seed_database.py

Requirements:
    - Database must be migrated (alembic upgrade head)
    - Environment variables must be configured
"""

import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add the project root to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.db.session import engine
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_membership_repository import (
    OrganizationMembershipRepository,
)
from app.repositories.model_repository import ModelRepository
from app.repositories.model_permission_repository import ModelPermissionRepository
from app.services.organization_service import OrganizationService
from app.schemas.tenant import TenantCreate
from app.schemas.user import UserCreate
from app.schemas.organization import OrganizationCreate
from app.schemas.organization_membership import OrganizationMembershipCreate
from app.schemas.simulation_model import ModelCreate
from app.schemas.model_permission import PermissionLevel

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_session():
    """Create a database session"""
    return SessionLocal()


def seed_tenants(db):
    """Create 3 sample tenants"""
    tenant_repo = TenantRepository()
    tenants = []

    tenant_data = [
        {
            "name": "Acme Corporation",
            "subdomain": "acme",
            "slug": "acme-corp",
            "plan_type": "professional",
            "status": "active",
            "max_users": 50,
            "max_models": 100,
            "max_scenarios_per_month": 10000,
            "max_storage_gb": 100.00,
            "billing_email": "billing@acme.com",
            "stripe_customer_id": "cus_acme_123456789",
        },
        {
            "name": "TechStart Solutions",
            "subdomain": "techstart",
            "slug": "techstart-solutions",
            "plan_type": "starter",
            "status": "active",
            "max_users": 10,
            "max_models": 25,
            "max_scenarios_per_month": 1000,
            "max_storage_gb": 25.00,
            "billing_email": "admin@techstart.io",
            "stripe_customer_id": "cus_techstart_987654321",
        },
        {
            "name": "Enterprise Dynamics",
            "subdomain": "entdyn",
            "slug": "enterprise-dynamics",
            "plan_type": "enterprise",
            "status": "active",
            "max_users": 200,
            "max_models": 500,
            "max_scenarios_per_month": 50000,
            "max_storage_gb": 500.00,
            "billing_email": "finance@entdyn.com",
            "stripe_customer_id": "cus_entdyn_555666777",
        },
    ]

    print("Creating tenants...")
    for data in tenant_data:
        tenant_create = TenantCreate(**data)
        tenant = tenant_repo.create(db=db, obj_in=tenant_create)
        tenants.append(tenant)
        print(f"  ✓ Created tenant: {tenant.name} ({tenant.slug})")

    db.commit()
    return tenants


def seed_users(db, tenants):
    """Create 3 users for each tenant"""
    user_repo = UserRepository()
    all_users = {}

    # User templates for each tenant
    users_data = {
        0: [  # Acme Corporation
            {
                "identity_provider": "entra_id",
                "identity_provider_id": "acme_001",
                "email": "john.doe@acme.com",
                "display_name": "John Doe",
                "status": "active",
                "login_count": 25,
                "total_usage_minutes": 1200,
                "user_metadata": '{"department": "Engineering", "role": "Senior Developer", "timezone": "America/New_York"}',
            },
            {
                "identity_provider": "entra_id",
                "identity_provider_id": "acme_002",
                "email": "sarah.smith@acme.com",
                "display_name": "Sarah Smith",
                "status": "active",
                "login_count": 18,
                "total_usage_minutes": 890,
                "user_metadata": '{"department": "Product", "role": "Product Manager", "timezone": "America/New_York"}',
            },
            {
                "identity_provider": "entra_id",
                "identity_provider_id": "acme_003",
                "email": "mike.johnson@acme.com",
                "display_name": "Mike Johnson",
                "status": "active",
                "login_count": 32,
                "total_usage_minutes": 1850,
                "user_metadata": '{"department": "Engineering", "role": "Tech Lead", "timezone": "America/New_York"}',
            },
        ],
        1: [  # TechStart Solutions
            {
                "identity_provider": "google",
                "identity_provider_id": "techstart_001",
                "email": "alex.chen@techstart.io",
                "display_name": "Alex Chen",
                "status": "active",
                "login_count": 42,
                "total_usage_minutes": 2100,
                "user_metadata": '{"department": "Development", "role": "Full Stack Developer", "timezone": "America/Los_Angeles"}',
            },
            {
                "identity_provider": "google",
                "identity_provider_id": "techstart_002",
                "email": "maria.garcia@techstart.io",
                "display_name": "Maria Garcia",
                "status": "active",
                "login_count": 28,
                "total_usage_minutes": 1340,
                "user_metadata": '{"department": "Design", "role": "UX Designer", "timezone": "America/Los_Angeles"}',
            },
            {
                "identity_provider": "google",
                "identity_provider_id": "techstart_003",
                "email": "david.kim@techstart.io",
                "display_name": "David Kim",
                "status": "active",
                "login_count": 15,
                "total_usage_minutes": 720,
                "user_metadata": '{"department": "Development", "role": "Backend Developer", "timezone": "America/Los_Angeles"}',
            },
        ],
        2: [  # Enterprise Dynamics
            {
                "identity_provider": "entra_id",
                "identity_provider_id": "entdyn_001",
                "email": "jennifer.williams@entdyn.com",
                "display_name": "Jennifer Williams",
                "status": "active",
                "login_count": 55,
                "total_usage_minutes": 3200,
                "user_metadata": '{"department": "Architecture", "role": "Solutions Architect", "timezone": "America/Chicago"}',
            },
            {
                "identity_provider": "entra_id",
                "identity_provider_id": "entdyn_002",
                "email": "robert.brown@entdyn.com",
                "display_name": "Robert Brown",
                "status": "active",
                "login_count": 38,
                "total_usage_minutes": 2050,
                "user_metadata": '{"department": "Operations", "role": "DevOps Engineer", "timezone": "America/Chicago"}',
            },
            {
                "identity_provider": "entra_id",
                "identity_provider_id": "entdyn_003",
                "email": "lisa.davis@entdyn.com",
                "display_name": "Lisa Davis",
                "status": "active",
                "login_count": 47,
                "total_usage_minutes": 2890,
                "user_metadata": '{"department": "Architecture", "role": "Enterprise Architect", "timezone": "America/Chicago"}',
            },
        ],
    }

    print("Creating users...")
    for tenant_idx, tenant in enumerate(tenants):
        tenant_users = []
        for user_data in users_data[tenant_idx]:
            # Prepare all data before creating UserCreate object
            create_data = {
                **user_data,
                "tenant_id": tenant.id
            }
            
            user_create = UserCreate(**create_data)
            user = user_repo.create_user_for_tenant(db=db, obj_in=user_create)
            tenant_users.append(user)
            print(
                f"  ✓ Created user: {user.display_name} ({user.email}) for {tenant.name}"
            )

        all_users[tenant.id] = tenant_users

    db.commit()
    return all_users


def seed_organizations(db, tenants, all_users):
    """Create 2 organizations for each tenant"""
    org_service = OrganizationService(db)
    all_organizations = {}

    # Organization templates for each tenant
    orgs_data = {
        0: [  # Acme Corporation
            {
                "name": "Engineering Division",
                "domain": "acme.com",
                "billing_email": "eng-billing@acme.com",
                "billing_address": "123 Tech Street, Suite 400, San Francisco, CA 94105",
                "org_metadata": '{"department": "Engineering", "cost_center": "ENG001", "budget": 500000}',
            },
            {
                "name": "Product Division",
                "domain": "acme.com",
                "billing_email": "product-billing@acme.com",
                "billing_address": "123 Tech Street, Suite 500, San Francisco, CA 94105",
                "org_metadata": '{"department": "Product", "cost_center": "PRD001", "budget": 300000}',
            },
        ],
        1: [  # TechStart Solutions
            {
                "name": "Development Team",
                "domain": "techstart.io",
                "billing_email": "dev-ops@techstart.io",
                "billing_address": "456 Startup Ave, Austin, TX 78701",
                "org_metadata": '{"team_type": "development", "focus": "web_applications", "size": "small"}',
            },
            {
                "name": "Creative Team",
                "domain": "techstart.io",
                "billing_email": "creative@techstart.io",
                "billing_address": "456 Startup Ave, Austin, TX 78701",
                "org_metadata": '{"team_type": "design", "focus": "user_experience", "size": "small"}',
            },
        ],
        2: [  # Enterprise Dynamics
            {
                "name": "Platform Architecture",
                "domain": "entdyn.com",
                "billing_email": "platform-finance@entdyn.com",
                "billing_address": "789 Enterprise Blvd, Chicago, IL 60601",
                "org_metadata": '{"division": "Platform", "focus": "infrastructure", "compliance": "SOX"}',
            },
            {
                "name": "Operations Center",
                "domain": "entdyn.com",
                "billing_email": "ops-finance@entdyn.com",
                "billing_address": "789 Enterprise Blvd, Chicago, IL 60601",
                "org_metadata": '{"division": "Operations", "focus": "monitoring", "compliance": "SOX"}',
            },
        ],
    }

    print("Creating organizations...")
    for tenant_idx, tenant in enumerate(tenants):
        tenant_orgs = []
        tenant_users = all_users[tenant.id]

        for org_idx, org_data in enumerate(orgs_data[tenant_idx]):
            # Create organization with first user as owner
            owner_user = tenant_users[0]  # First user becomes owner

            org_create = OrganizationCreate(**org_data)
            organization = org_service.create_organization_with_owner(
                tenant_id=tenant.id,
                organization_data=org_create,
                owner_user_id=owner_user.id,
            )

            tenant_orgs.append(organization)
            print(f"  ✓ Created organization: {organization.name} for {tenant.name}")
            print(f"    → Owner: {owner_user.display_name}")

        all_organizations[tenant.id] = tenant_orgs

    return all_organizations


def seed_organization_memberships(db, tenants, all_users, all_organizations):
    """Create organization memberships for users"""
    membership_repo = OrganizationMembershipRepository()

    # Membership patterns:
    # User 0: Owner of both orgs (already created in seed_organizations)
    # User 1: Admin of org 0, Member of org 1
    # User 2: Member of org 0, Admin of org 1

    print("Creating organization memberships...")
    for tenant in tenants:
        tenant_users = all_users[tenant.id]
        tenant_orgs = all_organizations[tenant.id]

        # User 1 memberships
        user_1 = tenant_users[1]

        # Admin of first org
        membership_repo.add_member(
            db=db,
            tenant_id=tenant.id,
            organization_id=tenant_orgs[0].id,
            user_id=user_1.id,
            role="admin",
            invited_by_user_id=tenant_users[0].id,  # Invited by owner
            status="active",
        )
        print(f"    → {user_1.display_name} is admin of {tenant_orgs[0].name}")

        # Member of second org
        membership_repo.add_member(
            db=db,
            tenant_id=tenant.id,
            organization_id=tenant_orgs[1].id,
            user_id=user_1.id,
            role="member",
            invited_by_user_id=tenant_users[0].id,  # Invited by owner
            status="active",
        )
        print(f"    → {user_1.display_name} is member of {tenant_orgs[1].name}")

        # User 2 memberships
        user_2 = tenant_users[2]

        # Member of first org
        membership_repo.add_member(
            db=db,
            tenant_id=tenant.id,
            organization_id=tenant_orgs[0].id,
            user_id=user_2.id,
            role="member",
            invited_by_user_id=tenant_users[0].id,  # Invited by owner
            status="active",
        )
        print(f"    → {user_2.display_name} is member of {tenant_orgs[0].name}")

        # Admin of second org
        membership_repo.add_member(
            db=db,
            tenant_id=tenant.id,
            organization_id=tenant_orgs[1].id,
            user_id=user_2.id,
            role="admin",
            invited_by_user_id=tenant_users[0].id,  # Invited by owner
            status="active",
        )
        print(f"    → {user_2.display_name} is admin of {tenant_orgs[1].name}")

    db.commit()


def seed_models(db, tenants, all_users, all_organizations):
    """Create simulation models for each tenant"""
    model_repo = ModelRepository()
    all_models = {}
    
    # Model templates for each tenant
    models_data = {
        0: [  # Acme Corporation
            {
                "name": "Customer Service Process",
                "description": "Simulation model for customer service workflow optimization",
                "source": "lucidchart",
                "source_document_id": "acme_cs_001",
                "source_url": "https://lucid.app/lucidchart/acme_cs_001",
                "reps": 100,
                "forecast_days": 30,
                "time_type": "clock",
                "one_clock_unit": "minutes",
                "run_clock_period": 480.0,  # 8 hours
                "is_template": False,
                "is_public": False
            },
            {
                "name": "Product Development Pipeline",
                "description": "End-to-end product development process model",
                "source": "standalone",
                "reps": 50,
                "forecast_days": 90,
                "time_type": "calendar",
                "is_template": True,
                "is_public": False
            },
            {
                "name": "Manufacturing Line Optimization",
                "description": "Production line efficiency and bottleneck analysis",
                "source": "miro",
                "source_document_id": "acme_mfg_001",
                "source_url": "https://miro.com/app/board/acme_mfg_001/",
                "reps": 200,
                "forecast_days": 7,
                "time_type": "clock",
                "one_clock_unit": "hours",
                "run_clock_period": 24.0,  # 24 hours
                "is_template": False,
                "is_public": False
            }
        ],
        1: [  # TechStart Solutions
            {
                "name": "Software Development Workflow",
                "description": "Agile development process simulation",
                "source": "lucidchart",
                "source_document_id": "techstart_dev_001",
                "reps": 75,
                "forecast_days": 14,
                "time_type": "calendar",
                "is_template": False,
                "is_public": True
            },
            {
                "name": "Customer Onboarding Process",
                "description": "New customer acquisition and onboarding flow",
                "source": "standalone",
                "reps": 25,
                "forecast_days": 30,
                "time_type": "clock",
                "one_clock_unit": "days",
                "run_clock_period": 30.0,
                "is_template": True,
                "is_public": False
            }
        ],
        2: [  # Enterprise Dynamics
            {
                "name": "Enterprise Infrastructure Model",
                "description": "Large-scale system architecture simulation",
                "source": "lucidchart",
                "source_document_id": "entdyn_infra_001",
                "source_url": "https://lucid.app/lucidchart/entdyn_infra_001",
                "reps": 500,
                "forecast_days": 365,
                "time_type": "calendar",
                "random_seed": 12345,
                "is_template": False,
                "is_public": False
            },
            {
                "name": "Risk Assessment Framework",
                "description": "Enterprise risk evaluation and mitigation model",
                "source": "standalone",
                "reps": 150,
                "forecast_days": 180,
                "time_type": "clock",
                "one_clock_unit": "days",
                "run_clock_period": 180.0,
                "is_template": True,
                "is_public": False
            },
            {
                "name": "Supply Chain Management",
                "description": "Global supply chain optimization model",
                "source": "miro",
                "source_document_id": "entdyn_scm_001",
                "reps": 300,
                "forecast_days": 60,
                "time_type": "clock",
                "one_clock_unit": "hours",
                "run_clock_period": 168.0,  # 1 week
                "is_template": False,
                "is_public": False
            }
        ]
    }
    
    print("Creating simulation models...")
    for tenant_idx, tenant in enumerate(tenants):
        tenant_models = []
        tenant_users = all_users[tenant.id]
        tenant_orgs = all_organizations[tenant.id]
        
        for model_idx, model_data in enumerate(models_data[tenant_idx]):
            # Assign models to different users and organizations
            created_by_user = tenant_users[model_idx % len(tenant_users)]
            organization = tenant_orgs[model_idx % len(tenant_orgs)] if model_idx < len(models_data[tenant_idx]) - 1 else None
            
            # Prepare model creation data
            model_create_data = {
                **model_data,
                "organization_id": organization.id if organization else None
            }
            
            # Create the schema object first to validate
            model_create = ModelCreate(**model_create_data)
            
            # Add fields that aren't in the schema but are needed for creation
            create_data = model_create.model_dump()
            create_data["created_by_user_id"] = created_by_user.id
            
            model = model_repo.create(
                db=db, 
                obj_in=create_data, 
                tenant_id=tenant.id
            )
            tenant_models.append(model)
            
            org_name = organization.name if organization else "Personal"
            print(f"  ✓ Created model: {model.name} by {created_by_user.display_name} ({org_name})")
        
        all_models[tenant.id] = tenant_models
    
    db.commit()
    return all_models


def seed_model_permissions(db, tenants, all_users, all_organizations, all_models):
    """Create model permissions for sharing and collaboration"""
    permission_repo = ModelPermissionRepository()
    
    print("Creating model permissions...")
    for tenant in tenants:
        tenant_users = all_users[tenant.id]
        tenant_orgs = all_organizations[tenant.id]
        tenant_models = all_models[tenant.id]
        
        # Permission scenarios:
        # 1. Model creators have admin access (implicit, but we'll make it explicit)
        # 2. Share models with other users in organization
        # 3. Give organization-level permissions
        # 4. Cross-user sharing
        
        for model_idx, model in enumerate(tenant_models):
            # 1. Explicit admin permission for model creator
            permission_repo.grant_permission(
                db=db,
                tenant_id=tenant.id,
                model_id=model.id,
                permission_level=PermissionLevel.ADMIN,
                granted_by_user_id=model.created_by_user_id,
                user_id=model.created_by_user_id,
                notes="Model creator admin access"
            )
            
            # 2. Share with organization members if model belongs to organization
            if model.organization_id:
                # Give organization read access
                permission_repo.grant_permission(
                    db=db,
                    tenant_id=tenant.id,
                    model_id=model.id,
                    permission_level=PermissionLevel.READ,
                    granted_by_user_id=model.created_by_user_id,
                    organization_id=model.organization_id,
                    notes="Organization-wide read access"
                )
                print(f"    → Granted organization read access to {model.name}")
            
            # 3. Give specific users different permission levels
            for user_idx, user in enumerate(tenant_users):
                if user.id != model.created_by_user_id:  # Don't duplicate creator permissions
                    # Rotate permission levels for variety
                    permission_levels = [PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE]
                    perm_level = permission_levels[(model_idx + user_idx) % len(permission_levels)]
                    
                    # Only grant individual permissions for half the models to create variety
                    if (model_idx + user_idx) % 2 == 0:
                        permission_repo.grant_permission(
                            db=db,
                            tenant_id=tenant.id,
                            model_id=model.id,
                            permission_level=perm_level,
                            granted_by_user_id=model.created_by_user_id,
                            user_id=user.id,
                            notes=f"Individual {perm_level.value} access"
                        )
                        print(f"    → Granted {perm_level.value} access to {user.display_name} for {model.name}")
            
            # 4. Template models get broader access
            if model.is_template:
                # Give all users in tenant read access to templates
                for user in tenant_users:
                    if user.id != model.created_by_user_id:
                        # Check if permission already exists
                        existing_perms = permission_repo.get_user_permissions_for_model(
                            db, tenant.id, user.id, model.id
                        )
                        if not existing_perms:
                            permission_repo.grant_permission(
                                db=db,
                                tenant_id=tenant.id,
                                model_id=model.id,
                                permission_level=PermissionLevel.READ,
                                granted_by_user_id=model.created_by_user_id,
                                user_id=user.id,
                                notes="Template access for all users"
                            )
                print(f"    → Granted template access to all users for {model.name}")
    
    db.commit()


def print_summary(tenants, all_users, all_organizations, all_models=None):
    """Print a summary of created data"""
    print("\n" + "=" * 60)
    print("DATABASE SEEDING COMPLETE!")
    print("=" * 60)

    for tenant in tenants:
        print(f"\n🏢 TENANT: {tenant.name} ({tenant.slug})")
        print(f"   Plan: {tenant.plan_type} | Status: {tenant.status}")

        print(f"\n   👥 USERS ({len(all_users[tenant.id])}):")
        for user in all_users[tenant.id]:
            metadata = eval(user.user_metadata) if user.user_metadata else {}
            dept = metadata.get("department", "N/A")
            role = metadata.get("role", "N/A")
            print(f"      • {user.display_name} ({user.email})")
            print(f"        {dept} - {role} | Logins: {user.login_count}")

        print(f"\n   🏛️  ORGANIZATIONS ({len(all_organizations[tenant.id])}):")
        for org in all_organizations[tenant.id]:
            print(f"      • {org.name} ({org.domain})")
            metadata = eval(org.org_metadata) if org.org_metadata else {}
            if "department" in metadata:
                print(f"        Department: {metadata['department']}")
            elif "team_type" in metadata:
                print(f"        Team Type: {metadata['team_type']}")
            elif "division" in metadata:
                print(f"        Division: {metadata['division']}")

        if all_models and tenant.id in all_models:
            print(f"\n   🔧 SIMULATION MODELS ({len(all_models[tenant.id])}):")
            for model in all_models[tenant.id]:
                print(f"      • {model.name} ({model.source})")
                if model.is_template:
                    print(f"        Template model - {model.time_type} time")
                elif model.is_public:
                    print(f"        Public model - {model.time_type} time")
                else:
                    print(f"        Private model - {model.time_type} time")

    print(f"\n📊 SUMMARY:")
    print(f"   • {len(tenants)} tenants created")
    print(f"   • {sum(len(users) for users in all_users.values())} users created")
    print(
        f"   • {sum(len(orgs) for orgs in all_organizations.values())} organizations created"
    )
    print(f"   • Organization memberships with owner/admin/member roles")
    if all_models:
        print(f"   • {sum(len(models) for models in all_models.values())} simulation models created")
        print(f"   • Model permissions for sharing and collaboration")
    print("\n🎉 Ready for testing!")


def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    print("Using Services and Repositories for proper business logic")

    try:
        with create_session() as db:
            # Seed data in order of dependencies
            tenants = seed_tenants(db)
            all_users = seed_users(db, tenants)
            all_organizations = seed_organizations(db, tenants, all_users)
            seed_organization_memberships(db, tenants, all_users, all_organizations)
            
            # Seed models and permissions
            all_models = seed_models(db, tenants, all_users, all_organizations)
            seed_model_permissions(db, tenants, all_users, all_organizations, all_models)

            # Print summary
            print_summary(tenants, all_users, all_organizations, all_models)

    except Exception as e:
        print(f"❌ Seeding failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
