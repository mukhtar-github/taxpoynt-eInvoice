# PostgreSQL Enum Case Sensitivity Solutions: Comprehensive Debugging Guide

The "invalid input value for enum crm_type: 'HUBSPOT'" error represents a common but complex issue where SQLAlchemy passes uppercase enum values to PostgreSQL, which expects lowercase values. Despite code fixes, the problem persists due to multiple caching layers and SQLAlchemy's default behavior of storing enum **names** rather than **values**.

## Root cause analysis

**The fundamental issue**: SQLAlchemy stores Python enum **names** (typically uppercase like 'HUBSPOT') in the database by default, not their associated **values** (often lowercase like 'hubspot'). This conflicts with PostgreSQL's case-sensitive enum validation, where 'HUBSPOT' ≠ 'hubspot'.

**Why fixes aren't working**: Even after correcting string literals in code, the issue persists because of:
- Python bytecode caching in `__pycache__` directories
- Celery worker processes retaining old enum definitions in memory
- SQLAlchemy connection pooling caching old metadata
- Railway platform Docker layer caching
- Python module import caching in `sys.modules`

## Critical SQLAlchemy configuration fix

The most important solution is configuring SQLAlchemy to store enum **values** instead of **names**:

```python
from sqlalchemy import Column, Enum
from sqlalchemy.dialects.postgresql import ENUM

class CrmType(enum.Enum):
    HUBSPOT = 'hubspot'  # Name: HUBSPOT, Value: hubspot
    SALESFORCE = 'salesforce'

# WRONG (default behavior - stores 'HUBSPOT')
crm_type_column = Column(Enum(CrmType))

# CORRECT (stores 'hubspot')
crm_type_column = Column(
    Enum(CrmType, values_callable=lambda obj: [e.value for e in obj])
)

# Alternative using PostgreSQL-specific ENUM
crm_type_column = Column(
    ENUM('hubspot', 'salesforce', name='crm_type', create_type=False)
)
```

## Systematic debugging approach

### Step 1: Verify actual deployed code

```bash
# SSH into Railway container or check deployed files
railway run bash

# Verify enum definitions in deployed code
grep -r "HUBSPOT\|hubspot" --include="*.py" /app/
cat /app/app/tasks/hubspot_tasks.py | grep -n -A5 -B5 "crm_type"

# Check Python bytecode timestamps
find /app -name "*.pyc" -exec ls -la {} \;
```

### Step 2: Clear all caching layers

```bash
# Clear Python bytecode cache
find /app -name "*.pyc" -delete
find /app -name "__pycache__" -type d -exec rm -rf {} +

# Set environment variable to prevent bytecode caching
railway vars set PYTHONDONTWRITEBYTECODE=1

# Restart Celery workers completely
pkill -f 'celery worker'
# Then redeploy to start fresh workers
```

### Step 3: Enable comprehensive logging

```python
# Add to your application startup
import logging
import os

if os.getenv('DEBUG_ENUMS', 'false').lower() == 'true':
    # Enable SQLAlchemy query logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Custom enum debugging
    import traceback
    from sqlalchemy import TypeDecorator, String
    
    class DebuggingEnum(TypeDecorator):
        impl = String
        
        def process_bind_param(self, value, dialect):
            if value is not None:
                print(f"ENUM DEBUG: Binding value '{value}' (type: {type(value)})")
                traceback.print_stack(limit=3)
            return value

# Set in Railway dashboard:
# DEBUG_ENUMS=true
```

### Step 4: Database-level verification

```sql
-- Check current enum definition
SELECT unnest(enum_range(NULL::crm_type)) AS valid_values;

-- Check what values are actually stored
SELECT crm_type, COUNT(*) 
FROM crm_connections 
GROUP BY crm_type;

-- Verify table structure
\d crm_connections;
```

## Railway platform-specific solutions

### Force complete redeployment

```bash
# Clear Railway build cache
railway vars set NIXPACKS_NO_CACHE=1

# Add cache-busting to your code
# In requirements.txt or main application file:
# Add comment with timestamp to force rebuild
```

### Verify deployment integrity

```python
# Add to your health check endpoint
from datetime import datetime
import sys

@app.route('/debug/deployment')
def deployment_debug():
    return {
        'timestamp': datetime.now().isoformat(),
        'python_path': sys.path,
        'modules_loaded': list(sys.modules.keys()),
        'enum_values': [e.value for e in CrmType],
        'enum_names': [e.name for e in CrmType]
    }
```

## Celery worker solutions

### Proper worker restart configuration

```python
# In celery configuration
from celery import Celery

app = Celery('tasks')
app.conf.update(
    worker_max_tasks_per_child=1000,  # Restart workers periodically
    worker_disable_rate_limits=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Force worker restart on enum changes
@app.task
def restart_workers():
    import os
    import signal
    os.kill(os.getpid(), signal.SIGTERM)
```

### Worker cache clearing

```bash
# In Railway or your deployment script
# Kill all worker processes before redeployment
pkill -f 'celery worker'

# Clear Redis/broker task queue if using
redis-cli FLUSHALL

# Start workers fresh
celery -A your_app worker --loglevel=info --detach
```

## Advanced debugging techniques

### Trace enum value origins

```python
# Add to hubspot_tasks.py temporarily
import logging
import traceback

logger = logging.getLogger('enum_trace')

def trace_enum_value(value, context=""):
    if isinstance(value, str) and value.isupper():
        logger.error(f"UPPERCASE ENUM DETECTED: {value} in {context}")
        logger.error("Stack trace:")
        traceback.print_stack()

# Before any database operation in hubspot_tasks.py
trace_enum_value(crm_type, "before query")
```

### SQLAlchemy connection debugging

```python
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if 'crm_type' in str(statement):
        print("=== CRM_TYPE QUERY DEBUG ===")
        print(f"SQL: {statement}")
        print(f"Parameters: {parameters}")
        
        # Check for uppercase enum values
        if parameters:
            for param_dict in (parameters if isinstance(parameters, list) else [parameters]):
                if isinstance(param_dict, dict):
                    for key, value in param_dict.items():
                        if 'crm_type' in key and isinstance(value, str) and value.isupper():
                            print(f"🚨 FOUND UPPERCASE ENUM: {key}={value}")
```

## PostgreSQL migration solutions

If you need to change existing data:

```sql
-- Option 1: Update existing data to match expected case
UPDATE crm_connections 
SET crm_type = LOWER(crm_type) 
WHERE crm_type IN ('HUBSPOT', 'SALESFORCE');

-- Option 2: Recreate enum with proper values
BEGIN;
-- Convert to text temporarily
ALTER TABLE crm_connections ALTER COLUMN crm_type TYPE text;

-- Update values to lowercase
UPDATE crm_connections SET crm_type = LOWER(crm_type);

-- Recreate enum type
DROP TYPE IF EXISTS crm_type;
CREATE TYPE crm_type AS ENUM ('hubspot', 'salesforce');

-- Convert back to enum
ALTER TABLE crm_connections ALTER COLUMN crm_type TYPE crm_type USING crm_type::crm_type;
COMMIT;
```

## Best practices moving forward

### 1. Consistent enum definitions

```python
class CrmType(str, enum.Enum):  # Inherit from str for better compatibility
    HUBSPOT = 'hubspot'
    SALESFORCE = 'salesforce'
    
    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None
```

### 2. Input validation layers

```python
# Add validation in your API/service layer
def normalize_crm_type(crm_type_input: str) -> str:
    """Normalize CRM type input to lowercase"""
    if not isinstance(crm_type_input, str):
        raise ValueError("CRM type must be a string")
    
    normalized = crm_type_input.lower().strip()
    valid_types = {'hubspot', 'salesforce'}
    
    if normalized not in valid_types:
        raise ValueError(f"Invalid CRM type: {crm_type_input}")
    
    return normalized
```

### 3. Testing enum behavior

```python
def test_enum_case_handling():
    """Test enum handles various case inputs"""
    test_cases = ['HUBSPOT', 'hubspot', 'HubSpot']
    
    for case in test_cases:
        # Should not raise exception
        normalized = normalize_crm_type(case)
        assert normalized == 'hubspot'
        
        # Should work in database queries
        connection = CrmConnection(crm_type=normalized)
        session.add(connection)
        session.commit()  # Should not fail
```

## Immediate action plan

1. **Deploy with caching disabled**: Set `NIXPACKS_NO_CACHE=1` and `PYTHONDONTWRITEBYTECODE=1`
2. **Fix SQLAlchemy enum configuration**: Use `values_callable` parameter
3. **Kill all Celery workers**: Ensure complete process restart
4. **Enable debug logging**: Temporarily add enum tracing to identify sources
5. **Verify with health check**: Add endpoint to confirm enum values are correct
6. **Database cleanup**: Update any existing uppercase values to lowercase

The key insight is that this is rarely a simple code fix - it requires addressing multiple caching layers and SQLAlchemy's fundamental enum handling behavior. The `values_callable` configuration change combined with comprehensive cache clearing should resolve the persistent uppercase enum issue.