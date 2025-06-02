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
from app.services.organization_service import OrganizationService
from app.schemas.tenant import TenantCreate
from app.schemas.user import UserCreate
from app.schemas.organization import OrganizationCreate
from app.schemas.organization_membership import OrganizationMembershipCreate

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


def print_summary(tenants, all_users, all_organizations):
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

    print(f"\n📊 SUMMARY:")
    print(f"   • {len(tenants)} tenants created")
    print(f"   • {sum(len(users) for users in all_users.values())} users created")
    print(
        f"   • {sum(len(orgs) for orgs in all_organizations.values())} organizations created"
    )
    print(f"   • Organization memberships with owner/admin/member roles")
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

            # Print summary
            print_summary(tenants, all_users, all_organizations)

    except Exception as e:
        print(f"❌ Seeding failed: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
