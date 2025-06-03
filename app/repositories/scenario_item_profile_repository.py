# app/repositories/scenario_item_profile_repository.py
"""
Repository for ScenarioItemProfile data access operations.

Provides data access methods for scenario parameter override management with
proper tenant isolation and efficient querying patterns.
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.db.models.scenario_item_profile import ScenarioItemProfile
from app.schemas.scenario_item_profile import TargetObjectType


class ScenarioItemProfileRepository(BaseRepository[ScenarioItemProfile]):
    """Repository for scenario item profile data access with tenant isolation"""

    def __init__(self):
        super().__init__(ScenarioItemProfile)

    def get_profiles_for_scenario(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID
    ) -> List[ScenarioItemProfile]:
        """
        Get all profiles for a specific scenario.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to get profiles for
            
        Returns:
            List of profiles belonging to the scenario
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.scenario_id == scenario_id,
                    self.model.is_deleted == False
                )
            )
            .order_by(
                self.model.target_object_type,
                self.model.target_object_id,
                self.model.property_name
            )
            .all()
        )

    def get_profile_for_target_property(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        target_object_id: UUID,
        property_name: str
    ) -> Optional[ScenarioItemProfile]:
        """
        Get a specific profile for a target object property.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID
            target_object_id: Target object ID
            property_name: Property name to find
            
        Returns:
            Profile if found, None otherwise
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.scenario_id == scenario_id,
                    self.model.target_object_id == target_object_id,
                    self.model.property_name == property_name,
                    self.model.is_deleted == False
                )
            )
            .first()
        )

    def get_profiles_by_target_object(
        self,
        db: Session,
        tenant_id: UUID,
        target_object_id: UUID,
        target_object_type: Optional[str] = None
    ) -> List[ScenarioItemProfile]:
        """
        Get all profiles for a specific target object across all scenarios.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            target_object_id: Target object ID
            target_object_type: Optional object type filter
            
        Returns:
            List of profiles for the target object
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.target_object_id == target_object_id,
                self.model.is_deleted == False
            )
        )

        if target_object_type:
            query = query.filter(self.model.target_object_type == target_object_type)

        return query.order_by(self.model.scenario_id, self.model.property_name).all()

    def get_profiles_by_target_type(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        target_object_type: str
    ) -> List[ScenarioItemProfile]:
        """
        Get all profiles for a specific object type in a scenario.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID
            target_object_type: Type of objects to get profiles for
            
        Returns:
            List of profiles for the object type
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.scenario_id == scenario_id,
                    self.model.target_object_type == target_object_type,
                    self.model.is_deleted == False
                )
            )
            .order_by(self.model.target_object_id, self.model.property_name)
            .all()
        )

    def search_profiles_by_property_name(
        self,
        db: Session,
        tenant_id: UUID,
        property_pattern: str,
        scenario_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScenarioItemProfile]:
        """
        Search profiles by property name pattern.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            property_pattern: Pattern to search for in property names
            scenario_id: Optional scenario ID filter
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of profiles matching the property pattern
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.property_name.ilike(f"%{property_pattern}%"),
                self.model.is_deleted == False
            )
        )

        if scenario_id:
            query = query.filter(self.model.scenario_id == scenario_id)

        return (
            query
            .order_by(self.model.property_name, self.model.scenario_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_profiles_for_scenario(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID
    ) -> int:
        """
        Delete all profiles for a scenario.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID to delete profiles for
            
        Returns:
            Number of profiles deleted
        """
        # Get count before deletion
        profiles_count = (
            db.query(func.count(self.model.id))
            .filter(
                and_(
                    self.model.tenant_id == tenant_id,
                    self.model.scenario_id == scenario_id,
                    self.model.is_deleted == False
                )
            )
            .scalar()
        )

        # Soft delete all profiles
        db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.scenario_id == scenario_id,
                self.model.is_deleted == False
            )
        ).update({"is_deleted": True})

        db.commit()
        return profiles_count

    def check_profile_exists(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID,
        target_object_id: UUID,
        property_name: str,
        exclude_profile_id: Optional[UUID] = None
    ) -> bool:
        """
        Check if a profile already exists for a specific property.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID
            target_object_id: Target object ID
            property_name: Property name
            exclude_profile_id: Profile ID to exclude from check (for updates)
            
        Returns:
            True if profile exists, False otherwise
        """
        query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.scenario_id == scenario_id,
                self.model.target_object_id == target_object_id,
                self.model.property_name == property_name,
                self.model.is_deleted == False
            )
        )

        if exclude_profile_id:
            query = query.filter(self.model.id != exclude_profile_id)

        return query.first() is not None

    def get_profile_statistics(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get statistical information about profiles.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Optional scenario ID to filter statistics
            
        Returns:
            Dictionary with profile statistics
        """
        base_query = db.query(self.model).filter(
            and_(
                self.model.tenant_id == tenant_id,
                self.model.is_deleted == False
            )
        )

        if scenario_id:
            base_query = base_query.filter(self.model.scenario_id == scenario_id)

        # Total profiles
        total_profiles = base_query.count()

        # Profiles by object type
        type_counts = (
            base_query
            .with_entities(self.model.target_object_type, func.count(self.model.id))
            .group_by(self.model.target_object_type)
            .all()
        )
        profiles_by_type = {obj_type: count for obj_type, count in type_counts}

        # Most overridden properties
        property_counts = (
            base_query
            .with_entities(self.model.property_name, func.count(self.model.id))
            .group_by(self.model.property_name)
            .order_by(desc(func.count(self.model.id)))
            .limit(10)
            .all()
        )
        most_overridden_properties = [
            {"property_name": prop, "count": count}
            for prop, count in property_counts
        ]

        # Scenarios with most overrides (if not filtered by scenario)
        scenario_counts = {}
        if not scenario_id:
            scenario_count_results = (
                base_query
                .with_entities(self.model.scenario_id, func.count(self.model.id))
                .group_by(self.model.scenario_id)
                .order_by(desc(func.count(self.model.id)))
                .limit(10)
                .all()
            )
            scenario_counts = {str(scen_id): count for scen_id, count in scenario_count_results}

        # Objects with most overrides
        object_counts = (
            base_query
            .with_entities(
                self.model.target_object_id,
                self.model.target_object_type,
                func.count(self.model.id)
            )
            .group_by(self.model.target_object_id, self.model.target_object_type)
            .order_by(desc(func.count(self.model.id)))
            .limit(10)
            .all()
        )
        most_overridden_objects = [
            {
                "object_id": str(obj_id),
                "object_type": obj_type,
                "override_count": count
            }
            for obj_id, obj_type, count in object_counts
        ]

        return {
            "total_profiles": total_profiles,
            "profiles_by_type": profiles_by_type,
            "most_overridden_properties": most_overridden_properties,
            "scenarios_with_most_overrides": scenario_counts,
            "most_overridden_objects": most_overridden_objects
        }

    def get_profiles_grouped_by_target(
        self,
        db: Session,
        tenant_id: UUID,
        scenario_id: UUID
    ) -> Dict[Tuple[UUID, str], List[ScenarioItemProfile]]:
        """
        Get profiles grouped by their target objects.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            scenario_id: Scenario ID
            
        Returns:
            Dictionary mapping (object_id, object_type) to list of profiles
        """
        profiles = self.get_profiles_for_scenario(db, tenant_id, scenario_id)
        
        grouped = {}
        for profile in profiles:
            key = (profile.target_object_id, profile.target_object_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(profile)
        
        return grouped

    def copy_profiles_between_scenarios(
        self,
        db: Session,
        tenant_id: UUID,
        source_scenario_id: UUID,
        target_scenario_id: UUID,
        overwrite_existing: bool = False
    ) -> int:
        """
        Copy all profiles from one scenario to another.
        
        Args:
            db: Database session
            tenant_id: Tenant ID for isolation
            source_scenario_id: Source scenario ID
            target_scenario_id: Target scenario ID
            overwrite_existing: Whether to overwrite existing profiles
            
        Returns:
            Number of profiles copied
        """
        # Get source profiles
        source_profiles = self.get_profiles_for_scenario(
            db, tenant_id, source_scenario_id
        )

        copied_count = 0
        for source_profile in source_profiles:
            # Check if profile already exists in target
            existing = self.get_profile_for_target_property(
                db,
                tenant_id,
                target_scenario_id,
                source_profile.target_object_id,
                source_profile.property_name
            )

            if existing and not overwrite_existing:
                continue

            if existing and overwrite_existing:
                # Update existing profile
                existing.property_value = source_profile.property_value
                existing.original_value = source_profile.original_value
                existing.description = source_profile.description
                existing.change_reason = source_profile.change_reason
                copied_count += 1
            else:
                # Create new profile
                new_profile = ScenarioItemProfile(
                    tenant_id=tenant_id,
                    scenario_id=target_scenario_id,
                    target_object_id=source_profile.target_object_id,
                    target_object_type=source_profile.target_object_type,
                    property_name=source_profile.property_name,
                    property_value=source_profile.property_value,
                    original_value=source_profile.original_value,
                    description=source_profile.description,
                    change_reason=source_profile.change_reason
                )
                db.add(new_profile)
                copied_count += 1

        db.commit()
        return copied_count