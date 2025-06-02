# Module 3.2: Test Model Creation

**Duration:** 10-15 minutes  
**Objective:** Create a test model to verify BaseEntity functionality works correctly.

**Prerequisites:** Step 1 completed - BaseEntity class implemented

---

## Step 2: Create Test Model to Verify BaseEntity

### 2.1 Create a Simple Test Model
Create `app/db/models/test_model.py`:

```python
"""
Temporary test model to verify BaseEntity functionality.
This file will be deleted after testing.
"""
from sqlalchemy import Column, String
from app.db.models.base_entity import BaseEntity

class TestModel(BaseEntity):
    __tablename__ = "test_models"
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
```

### 2.2 Import Test Model
Update `app/db/models/__init__.py`:

```python
"""
Database models package.
"""

from .base_entity import BaseEntity
from .test_model import TestModel  # Temporary for testing

__all__ = ["BaseEntity", "TestModel"]
```

---

**✅ Checkpoint:** Test model created and imported successfully.

**Next Step:** [032_BaseEntity_Migration_Testing.md](./032_BaseEntity_Migration_Testing.md)
