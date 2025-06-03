"""
CRUD operations for signature settings.

This module provides database operations for creating, retrieving,
updating, and deleting signature settings.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError

from app.models.signature_settings import SignatureSettings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# In-memory fallback settings storage
_IN_MEMORY_SETTINGS = {}
_DEFAULT_SETTINGS = {
    "algorithm": "RSA-PSS-SHA256",
    "csid_version": "2.0",
    "enable_caching": True,
    "cache_size": 1000,
    "cache_ttl": 3600,
    "parallel_processing": True,
    "max_workers": 4,
    "extra_settings": {}
}

# Flag to track database availability
_DB_TABLE_EXISTS = None

@contextmanager
def with_db_error_handling(db_session):
    """Context manager to handle database errors gracefully"""
    global _DB_TABLE_EXISTS
    
    try:
        yield
        # If we get here successfully, we know the table exists
        if _DB_TABLE_EXISTS is None:
            _DB_TABLE_EXISTS = True
    except (ProgrammingError, OperationalError) as e:
        # These errors typically indicate the table doesn't exist
        if "relation \"signature_settings\" does not exist" in str(e) or "no such table" in str(e):
            _DB_TABLE_EXISTS = False
            logger.warning(f"SignatureSettings table does not exist yet: {e}")
        else:
            logger.error(f"Database error: {e}")
        if db_session:
            db_session.rollback()
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {e}")
        if db_session:
            db_session.rollback()

def get_settings(db: Session, settings_id: int) -> Optional[SignatureSettings]:
    """Get settings by ID"""
    with with_db_error_handling(db):
        return db.query(SignatureSettings).filter(SignatureSettings.id == settings_id).first()

def get_active_settings_by_user(db: Session, user_id: int) -> Optional[SignatureSettings]:
    """Get active settings for a specific user"""
    with with_db_error_handling(db):
        return db.query(SignatureSettings).filter(
            SignatureSettings.user_id == user_id,
            SignatureSettings.is_active == True
        ).order_by(SignatureSettings.version.desc()).first()

def get_default_settings(db: Session) -> Optional[SignatureSettings]:
    """Get system-wide default settings (where user_id is NULL)"""
    with with_db_error_handling(db):
        return db.query(SignatureSettings).filter(
            SignatureSettings.user_id.is_(None),
            SignatureSettings.is_active == True
        ).order_by(SignatureSettings.version.desc()).first()

def get_settings_history(
    db: Session, 
    user_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 100
) -> List[SignatureSettings]:
    """Get settings history for a user or system defaults"""
    with with_db_error_handling(db):
        query = db.query(SignatureSettings)
        
        if user_id is not None:
            query = query.filter(SignatureSettings.user_id == user_id)
        else:
            query = query.filter(SignatureSettings.user_id.is_(None))
            
        return query.order_by(SignatureSettings.created_at.desc()).offset(skip).limit(limit).all()

def get_active_settings(db: Session, user_id: Optional[int] = None) -> Optional[Union[SignatureSettings, Dict[str, Any]]]:
    """Get active signature settings for a user, or default settings if user_id is None"""
    global _DB_TABLE_EXISTS, _IN_MEMORY_SETTINGS
    
    # If we know the table doesn't exist, use in-memory storage
    if _DB_TABLE_EXISTS is False:
        user_key = str(user_id) if user_id else "default"
        return _IN_MEMORY_SETTINGS.get(user_key, _DEFAULT_SETTINGS)
    
    # Try to fetch from database
    with with_db_error_handling(db):
        query = db.query(SignatureSettings).filter(SignatureSettings.is_active == True)
        
        if user_id:
            query = query.filter(SignatureSettings.user_id == user_id)
        else:
            query = query.filter(SignatureSettings.user_id == None)
            
        result = query.order_by(SignatureSettings.updated_at.desc()).first()
        
        # If we got here, the table exists but we didn't find settings
        if not result:
            # Check in-memory fallback
            user_key = str(user_id) if user_id else "default"
            if user_key in _IN_MEMORY_SETTINGS:
                return _IN_MEMORY_SETTINGS[user_key]
            
            # Create default settings in database
            default_settings = _DEFAULT_SETTINGS.copy()
            if user_id:
                default_settings["user_id"] = user_id
                
            return create_settings(db, SignatureSettings(**default_settings))
            
        return result
    
    # If we get here, there was a database error
    user_key = str(user_id) if user_id else "default"
    return _IN_MEMORY_SETTINGS.get(user_key, _DEFAULT_SETTINGS)

def create_settings(
    db: Session, 
    settings: SignatureSettings
) -> Union[SignatureSettings, Dict[str, Any]]:
    """Create new settings"""
    global _DB_TABLE_EXISTS, _IN_MEMORY_SETTINGS
    
    # Set default values if not provided
    if settings.version is None:
        settings.version = 1
    if settings.is_active is None:
        settings.is_active = True
    
    # If we know the table doesn't exist, use in-memory storage
    if _DB_TABLE_EXISTS is False:
        # Convert to dictionary for in-memory storage
        settings_dict = settings.to_dict() if hasattr(settings, 'to_dict') else {
            'id': len(_IN_MEMORY_SETTINGS) + 1,
            'version': settings.version,
            'is_active': settings.is_active,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'user_id': settings.user_id,
            'algorithm': settings.algorithm,
            'csid_version': settings.csid_version,
            'enable_caching': settings.enable_caching,
            'cache_size': settings.cache_size,
            'cache_ttl': settings.cache_ttl,
            'parallel_processing': settings.parallel_processing,
            'max_workers': settings.max_workers,
            'extra_settings': settings.extra_settings
        }
        
        # Deactivate previous active settings for this user in memory
        user_key = str(settings.user_id) if settings.user_id else "default"
        _IN_MEMORY_SETTINGS[user_key] = settings_dict
        logger.info(f"Stored settings in memory for user {user_key}")
        return settings_dict
        
    # Try to save to database
    with with_db_error_handling(db):
        # Deactivate previous active settings for this user
        if settings.is_active:
            previous_settings_query = db.query(SignatureSettings)
            if settings.user_id is not None:
                previous_settings_query = previous_settings_query.filter(SignatureSettings.user_id == settings.user_id)
            else:
                previous_settings_query = previous_settings_query.filter(SignatureSettings.user_id.is_(None))
                
            for prev_setting in previous_settings_query.filter(SignatureSettings.is_active == True).all():
                prev_setting.is_active = False
                db.add(prev_setting)
        
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    
    # If we get here, there was a database error - fallback to memory
    settings_dict = {
        'id': len(_IN_MEMORY_SETTINGS) + 1,
        'version': settings.version,
        'is_active': settings.is_active,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'user_id': settings.user_id,
        'algorithm': settings.algorithm,
        'csid_version': settings.csid_version,
        'enable_caching': settings.enable_caching,
        'cache_size': settings.cache_size,
        'cache_ttl': settings.cache_ttl,
        'parallel_processing': settings.parallel_processing,
        'max_workers': settings.max_workers,
        'extra_settings': settings.extra_settings
    }
    
    user_key = str(settings.user_id) if settings.user_id else "default"
    _IN_MEMORY_SETTINGS[user_key] = settings_dict
    return settings_dict

def update_settings(
    db: Session, 
    *, 
    db_settings: Union[SignatureSettings, Dict[str, Any]],
    user_id: Optional[int] = None,
    settings_update: Dict[str, Any]
) -> Union[SignatureSettings, Dict[str, Any]]:
    """Update settings (creates a new version)"""
    global _DB_TABLE_EXISTS, _IN_MEMORY_SETTINGS
    
    # Handle dictionary input (from in-memory settings)
    if isinstance(db_settings, dict):
        # If we're using in-memory storage
        new_version = db_settings.get('version', 0) + 1
        user_id = user_id if user_id is not None else db_settings.get('user_id')
        
        # Create updated settings dictionary
        new_settings = db_settings.copy()
        new_settings.update(settings_update)
        new_settings['version'] = new_version
        new_settings['is_active'] = True
        new_settings['updated_at'] = datetime.now()
        
        # Store in memory
        user_key = str(user_id) if user_id else "default"
        _IN_MEMORY_SETTINGS[user_key] = new_settings
        return new_settings
    
    # If we know the table doesn't exist, convert to in-memory and update
    if _DB_TABLE_EXISTS is False:
        # Convert to dictionary
        settings_dict = db_settings.to_dict() if hasattr(db_settings, 'to_dict') else {
            'id': getattr(db_settings, 'id', 1),
            'version': getattr(db_settings, 'version', 0),
            'is_active': getattr(db_settings, 'is_active', True),
            'created_at': getattr(db_settings, 'created_at', datetime.now()),
            'updated_at': datetime.now(),
            'user_id': getattr(db_settings, 'user_id', None),
            'algorithm': getattr(db_settings, 'algorithm', None),
            'csid_version': getattr(db_settings, 'csid_version', None),
            'enable_caching': getattr(db_settings, 'enable_caching', None),
            'cache_size': getattr(db_settings, 'cache_size', None),
            'cache_ttl': getattr(db_settings, 'cache_ttl', None),
            'parallel_processing': getattr(db_settings, 'parallel_processing', None),
            'max_workers': getattr(db_settings, 'max_workers', None),
            'extra_settings': getattr(db_settings, 'extra_settings', {})
        }
        
        # Update with new values
        settings_dict.update(settings_update)
        settings_dict['version'] = settings_dict.get('version', 0) + 1
        settings_dict['updated_at'] = datetime.now()
        
        # Store in memory
        user_id = user_id if user_id is not None else settings_dict.get('user_id')
        user_key = str(user_id) if user_id else "default"
        _IN_MEMORY_SETTINGS[user_key] = settings_dict
        return settings_dict
    
    # Try to update in database
    with with_db_error_handling(db):
        # Create a new settings object with incremented version
        new_version = db_settings.version + 1 if db_settings.version else 1
        
        # Create new settings object with values from existing + updates
        new_settings = SignatureSettings(
            version=new_version,
            is_active=True,  # New version is active by default
            user_id=user_id if user_id is not None else db_settings.user_id,
            algorithm=settings_update.get('algorithm', db_settings.algorithm),
            csid_version=settings_update.get('csid_version', db_settings.csid_version),
            enable_caching=settings_update.get('enable_caching', db_settings.enable_caching),
            cache_size=settings_update.get('cache_size', db_settings.cache_size),
            cache_ttl=settings_update.get('cache_ttl', db_settings.cache_ttl),
            parallel_processing=settings_update.get('parallel_processing', db_settings.parallel_processing),
            max_workers=settings_update.get('max_workers', db_settings.max_workers),
            extra_settings=settings_update.get('extra_settings', db_settings.extra_settings)
        )
        
        # Deactivate the current active settings
        db_settings.is_active = False
        db.add(db_settings)
        
        # Create the new settings
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings
    
    # If we get here, there was a database error - fallback to memory
    settings_dict = {
        'id': getattr(db_settings, 'id', 1),
        'version': getattr(db_settings, 'version', 0) + 1,
        'is_active': True,
        'created_at': getattr(db_settings, 'created_at', datetime.now()),
        'updated_at': datetime.now(),
        'user_id': user_id if user_id is not None else getattr(db_settings, 'user_id', None),
        'algorithm': settings_update.get('algorithm', getattr(db_settings, 'algorithm', None)),
        'csid_version': settings_update.get('csid_version', getattr(db_settings, 'csid_version', None)),
        'enable_caching': settings_update.get('enable_caching', getattr(db_settings, 'enable_caching', None)),
        'cache_size': settings_update.get('cache_size', getattr(db_settings, 'cache_size', None)),
        'cache_ttl': settings_update.get('cache_ttl', getattr(db_settings, 'cache_ttl', None)),
        'parallel_processing': settings_update.get('parallel_processing', getattr(db_settings, 'parallel_processing', None)),
        'max_workers': settings_update.get('max_workers', getattr(db_settings, 'max_workers', None)),
        'extra_settings': settings_update.get('extra_settings', getattr(db_settings, 'extra_settings', {}))
    }
    
    user_key = str(settings_dict['user_id']) if settings_dict.get('user_id') else "default"
    _IN_MEMORY_SETTINGS[user_key] = settings_dict
    return settings_dict

def delete_settings(db: Session, *, settings_id: int) -> Optional[Union[SignatureSettings, Dict[str, Any]]]:
    """Delete settings (soft delete by marking as inactive)"""
    global _DB_TABLE_EXISTS, _IN_MEMORY_SETTINGS
    
    # Try to delete from database
    with with_db_error_handling(db):
        settings = get_settings(db, settings_id=settings_id)
        if not settings:
            return None
            
        settings.is_active = False
        db.add(settings)
        db.commit()
        return settings
    
    # If database failed, check in-memory (this is a bit limited since we don't track by ID)
    # For in-memory, we just return the settings dict with is_active=False
    for user_key, settings in _IN_MEMORY_SETTINGS.items():
        if settings.get('id') == settings_id:
            settings['is_active'] = False
            return settings
    
    return None

def rollback_settings(db: Session, *, settings_id: int, user_id: Optional[int] = None) -> Optional[Union[SignatureSettings, Dict[str, Any]]]:
    """Rollback to previous settings version"""
    global _DB_TABLE_EXISTS, _IN_MEMORY_SETTINGS
    
    # Try to rollback in database
    with with_db_error_handling(db):
        # Get the settings to rollback to
        settings_to_rollback = get_settings(db, settings_id=settings_id)
        if not settings_to_rollback:
            return None
            
        # Ensure we're rolling back to settings for the same user
        if user_id is not None and settings_to_rollback.user_id != user_id:
            return None
            
        # Get current active settings
        query = db.query(SignatureSettings).filter(SignatureSettings.is_active == True)
        if user_id is not None:
            query = query.filter(SignatureSettings.user_id == user_id)
        else:
            query = query.filter(SignatureSettings.user_id.is_(None))
            
        current_active = query.first()
        if current_active:
            current_active.is_active = False
            db.add(current_active)
        
        # Create a new version based on the rolled back settings
        new_version = (current_active.version if current_active else 0) + 1
        new_settings = SignatureSettings(
            version=new_version,
            is_active=True,
            user_id=settings_to_rollback.user_id,
            algorithm=settings_to_rollback.algorithm,
            csid_version=settings_to_rollback.csid_version,
            enable_caching=settings_to_rollback.enable_caching,
            cache_size=settings_to_rollback.cache_size,
            cache_ttl=settings_to_rollback.cache_ttl,
            parallel_processing=settings_to_rollback.parallel_processing,
            max_workers=settings_to_rollback.max_workers,
            extra_settings=settings_to_rollback.extra_settings
        )
        
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings
        
    # If database failed, we can attempt to find the settings in memory
    # This is limited functionality since we don't fully track history in memory
    user_key = str(user_id) if user_id is not None else "default"
    if user_key in _IN_MEMORY_SETTINGS:
        # Create a new version based on current settings
        current = _IN_MEMORY_SETTINGS[user_key]
        new_settings = current.copy()
        new_settings['version'] = (current.get('version', 0) + 1)
        new_settings['updated_at'] = datetime.now()
        _IN_MEMORY_SETTINGS[user_key] = new_settings
        return new_settings
    
    return None

def get_effective_settings(db: Session, user: Optional[User] = None) -> Dict[str, Any]:
    """
    Get effective settings for a user
    - First check for user-specific settings
    - If none exist, use system default settings
    - If no settings exist at all, use hardcoded defaults
    """
    global _DB_TABLE_EXISTS, _IN_MEMORY_SETTINGS, _DEFAULT_SETTINGS
    
    user_id = user.id if user else None
    
    # If we know the table doesn't exist, use in-memory settings
    if _DB_TABLE_EXISTS is False:
        # Try user-specific settings first
        user_key = str(user_id) if user_id is not None else None
        if user_key and user_key in _IN_MEMORY_SETTINGS:
            settings = _IN_MEMORY_SETTINGS[user_key].copy()
            settings["is_default"] = False
            return settings
            
        # Fall back to default settings
        if "default" in _IN_MEMORY_SETTINGS:
            settings = _IN_MEMORY_SETTINGS["default"].copy()
            settings["is_default"] = True
            return settings
            
        # Use hardcoded defaults if nothing in memory
        default = _DEFAULT_SETTINGS.copy()
        default["is_default"] = True
        default["user_id"] = None
        default["is_active"] = True
        default["version"] = 1
        return default
    
    # Try to get from database
    with with_db_error_handling(db):
        # Try to get user-specific settings if user is provided
        if user:
            user_settings = get_active_settings_by_user(db, user.id)
            if user_settings:
                result = user_settings.to_dict() if hasattr(user_settings, 'to_dict') else {
                    "id": user_settings.id,
                    "version": user_settings.version,
                    "is_active": user_settings.is_active,
                    "created_at": user_settings.created_at,
                    "updated_at": user_settings.updated_at,
                    "user_id": user_settings.user_id,
                    "algorithm": user_settings.algorithm,
                    "csid_version": user_settings.csid_version,
                    "enable_caching": user_settings.enable_caching,
                    "cache_size": user_settings.cache_size,
                    "cache_ttl": user_settings.cache_ttl,
                    "parallel_processing": user_settings.parallel_processing,
                    "max_workers": user_settings.max_workers,
                    "extra_settings": user_settings.extra_settings or {}
                }
                result["is_default"] = False
                return result
        
        # Fall back to system default settings
        default_settings = get_default_settings(db)
        if default_settings:
            result = default_settings.to_dict() if hasattr(default_settings, 'to_dict') else {
                "id": default_settings.id,
                "version": default_settings.version,
                "is_active": default_settings.is_active,
                "created_at": default_settings.created_at,
                "updated_at": default_settings.updated_at,
                "user_id": default_settings.user_id,
                "algorithm": default_settings.algorithm,
                "csid_version": default_settings.csid_version,
                "enable_caching": default_settings.enable_caching,
                "cache_size": default_settings.cache_size,
                "cache_ttl": default_settings.cache_ttl,
                "parallel_processing": default_settings.parallel_processing,
                "max_workers": default_settings.max_workers,
                "extra_settings": default_settings.extra_settings or {}
            }
            result["is_default"] = True
            return result
    
    # If we get here, either there was a database error or no settings were found
    # Check in-memory settings
    user_key = str(user_id) if user_id is not None else None
    if user_key and user_key in _IN_MEMORY_SETTINGS:
        settings = _IN_MEMORY_SETTINGS[user_key].copy()
        settings["is_default"] = False
        return settings
        
    if "default" in _IN_MEMORY_SETTINGS:
        settings = _IN_MEMORY_SETTINGS["default"].copy()
        settings["is_default"] = True
        return settings
    
    # If nothing found anywhere, return hardcoded defaults
    return {
        "id": None,
        "version": 1,
        "is_active": True,
        "created_at": None,
        "updated_at": None,
        "user_id": None,
        "algorithm": "RSA-PSS-SHA256",
        "csid_version": "2.0",
        "enable_caching": True,
        "cache_size": 1000,
        "cache_ttl": 3600,
        "parallel_processing": True,
        "max_workers": 4,
        "extra_settings": {},
        "is_default": True
    }
