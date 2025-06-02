# tests/unit/services/test_model_service.py
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.model_service import ModelService
from app.schemas.simulation_model import ModelCreate, ModelUpdate
from app.db.models.simulation_model import Model


class TestModelService:
    """Unit tests for ModelService"""

    def setup_method(self):
        """Set up test dependencies"""
        self.model_service = ModelService()
        self.mock_db = Mock(spec=Session)
        self.tenant_id = uuid4()
        self.user_id = uuid4()

    def test_create_model_success(self):
        """Test successful model creation"""
        # Arrange
        mock_repo = Mock()

        # Mock that no existing model is found
        mock_repo.get_latest_version_by_name.return_value = None

        # Create expected model
        expected_model = Model(
            id=uuid4(),
            name="Test Model",
            source="manual",
            tenant_id=self.tenant_id,
            created_by_user_id=self.user_id,
        )
        mock_repo.create.return_value = expected_model

        # Replace the repository instance in the service
        self.model_service.model_repository = mock_repo

        model_create = ModelCreate(
            name="Test Model", source="manual", description="Test description"
        )

        # Act
        result = self.model_service.create_model(
            db=self.mock_db,
            tenant_id=self.tenant_id,
            model_create=model_create,
            current_user_id=self.user_id,
        )

        # Assert
        assert result == expected_model
        mock_repo.get_latest_version_by_name.assert_called_once_with(
            self.mock_db, self.tenant_id, "Test Model"
        )
        mock_repo.create.assert_called_once()

        # Check that create was called with correct data
        create_call_args = mock_repo.create.call_args[1]
        assert create_call_args["name"] == "Test Model"
        assert create_call_args["source"] == "manual"
        assert create_call_args["tenant_id"] == self.tenant_id
        assert create_call_args["created_by_user_id"] == self.user_id
        assert create_call_args["version"] == 1

    def test_create_model_duplicate_name(self):
        """Test model creation with duplicate name raises exception"""
        # Arrange
        mock_repo = Mock()

        # Mock that an existing model IS found
        existing_model = Model(id=uuid4(), name="Test Model")
        mock_repo.get_latest_version_by_name.return_value = existing_model

        # Replace the repository instance in the service
        self.model_service.model_repository = mock_repo

        model_create = ModelCreate(name="Test Model", source="manual")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.model_service.create_model(
                db=self.mock_db,
                tenant_id=self.tenant_id,
                model_create=model_create,
                current_user_id=self.user_id,
            )

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    def test_update_model_success(self):
        """Test successful model update"""
        # Arrange
        mock_repo = Mock()

        model_id = uuid4()

        # Use the SAME user_id for both the existing model and current user
        existing_model = Model(
            id=model_id,
            name="Old Name",
            created_by_user_id=self.user_id,  # Same as current_user_id
            version=1,
        )
        mock_repo.get_by_id.return_value = existing_model
        mock_repo.get_latest_version_by_name.return_value = None  # No name conflict

        updated_model = Model(
            id=model_id, name="New Name", created_by_user_id=self.user_id, version=1
        )
        mock_repo.update.return_value = updated_model

        # Replace the repository instance in the service
        self.model_service.model_repository = mock_repo

        model_update = ModelUpdate(name="New Name", description="New description")

        # Act
        result = self.model_service.update_model(
            db=self.mock_db,
            tenant_id=self.tenant_id,
            model_id=model_id,
            model_update=model_update,
            current_user_id=self.user_id,  # Same as existing_model.created_by_user_id
        )

        # Assert
        assert result == updated_model
        mock_repo.update.assert_called_once()

    def test_update_model_permission_denied(self):
        """Test model update with insufficient permissions"""
        # Arrange
        mock_repo = Mock()

        other_user_id = uuid4()  # Different user
        existing_model = Model(
            id=uuid4(),
            name="Test Model",
            created_by_user_id=other_user_id,  # Different from self.user_id
        )
        mock_repo.get_by_id.return_value = existing_model

        # Replace the repository instance in the service
        self.model_service.model_repository = mock_repo

        model_update = ModelUpdate(name="New Name")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            self.model_service.update_model(
                db=self.mock_db,
                tenant_id=self.tenant_id,
                model_id=existing_model.id,
                model_update=model_update,
                current_user_id=self.user_id,  # Different from existing_model.created_by_user_id
            )

        assert exc_info.value.status_code == 403
        assert "Only the model creator" in str(exc_info.value.detail)

    def test_delete_model_success(self):
        """Test successful model deletion"""
        # Arrange
        mock_repo = Mock()

        model_id = uuid4()

        # Use the SAME user_id
        existing_model = Model(
            id=model_id,
            name="Test Model",
            created_by_user_id=self.user_id,  # Same as current_user_id
        )
        mock_repo.get_by_id.return_value = existing_model
        mock_repo.delete.return_value = True

        # Replace the repository instance in the service
        self.model_service.model_repository = mock_repo

        # Act
        result = self.model_service.delete_model(
            db=self.mock_db,
            tenant_id=self.tenant_id,
            model_id=model_id,
            current_user_id=self.user_id,  # Same as existing_model.created_by_user_id
        )

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(self.mock_db, self.tenant_id, model_id)

    def test_get_model_by_id(self):
        """Test getting model by ID"""
        # Arrange
        mock_repo = Mock()

        model_id = uuid4()
        expected_model = Model(id=model_id, name="Test Model")

        # Mock the repository method directly
        mock_repo.get_by_id.return_value = expected_model

        # Replace the repository instance in the service
        self.model_service.model_repository = mock_repo

        # Act
        result = self.model_service.get_model_by_id(
            db=self.mock_db,
            tenant_id=self.tenant_id,
            model_id=model_id,
            load_relationships=False,
        )

        # Assert
        assert result == expected_model
        mock_repo.get_by_id.assert_called_once_with(
            self.mock_db, self.tenant_id, model_id
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
