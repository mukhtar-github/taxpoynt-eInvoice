"""
Repository Base Classes for TaxPoynt Platform

Enterprise repository pattern with tenant-aware data access,
caching integration, and performance optimizations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Generic, Callable
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import Select
from sqlalchemy import and_, or_, text, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Type variables for generic repository
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class SortDirection(Enum):
    """Sort direction options."""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(Enum):
    """Filter operators for queries."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    LIKE = "like"
    ILIKE = "ilike"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


@dataclass
class FilterCriteria:
    """Filter criteria for repository queries."""
    field: str
    operator: FilterOperator
    value: Any
    case_sensitive: bool = True


@dataclass
class SortCriteria:
    """Sort criteria for repository queries."""
    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20
    max_page_size: int = 1000
    
    def __post_init__(self):
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 20
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size


@dataclass
class PaginatedResult(Generic[ModelType]):
    """Paginated query result."""
    items: List[ModelType]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(
        cls,
        items: List[ModelType],
        total: int,
        pagination: PaginationParams
    ) -> 'PaginatedResult[ModelType]':
        """Create paginated result from items and pagination params."""
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            has_next=pagination.page < total_pages,
            has_previous=pagination.page > 1
        )


class RepositoryError(Exception):
    """Base repository error."""
    pass


class EntityNotFoundError(RepositoryError):
    """Entity not found error."""
    pass


class DuplicateEntityError(RepositoryError):
    """Duplicate entity error."""
    pass


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Abstract base repository with tenant-aware operations.
    
    Provides common CRUD operations with caching, filtering, and pagination.
    """
    
    def __init__(
        self,
        model: Type[ModelType],
        session_factory: Callable[[], Session],
        tenant_manager=None,
        cache_manager=None
    ):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session_factory: Function to create database sessions
            tenant_manager: Optional tenant manager for multi-tenant operations
            cache_manager: Optional cache manager for caching
        """
        self.model = model
        self.session_factory = session_factory
        self.tenant_manager = tenant_manager
        self.cache_manager = cache_manager
        
        # Cache configuration
        self.cache_ttl = 300  # 5 minutes default
        self.enable_caching = cache_manager is not None
        
        # Performance tracking
        self._query_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    @abstractmethod
    def _get_cache_key_prefix(self) -> str:
        """Get cache key prefix for this repository."""
        pass
    
    def _get_cache_key(self, key: str) -> str:
        """Generate cache key with tenant context."""
        prefix = self._get_cache_key_prefix()
        
        if self.tenant_manager and hasattr(self.tenant_manager, 'tenant_context'):
            org_id = self.tenant_manager.tenant_context.get_organization_id()
            if org_id:
                return f"{prefix}:tenant:{org_id}:{key}"
        
        return f"{prefix}:global:{key}"
    
    def _apply_tenant_filter(self, query: Query) -> Query:
        """Apply tenant filtering to query."""
        if self.tenant_manager and hasattr(self.model, 'organization_id'):
            query = self.tenant_manager.apply_tenant_filter(query, self.model)
        return query
    
    def _apply_filters(self, query: Query, filters: List[FilterCriteria]) -> Query:
        """Apply filter criteria to query."""
        for filter_criteria in filters:
            if not hasattr(self.model, filter_criteria.field):
                logger.warning(f"Field {filter_criteria.field} not found in model {self.model.__name__}")
                continue
            
            field = getattr(self.model, filter_criteria.field)
            
            if filter_criteria.operator == FilterOperator.EQUALS:
                query = query.filter(field == filter_criteria.value)
            elif filter_criteria.operator == FilterOperator.NOT_EQUALS:
                query = query.filter(field != filter_criteria.value)
            elif filter_criteria.operator == FilterOperator.GREATER_THAN:
                query = query.filter(field > filter_criteria.value)
            elif filter_criteria.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                query = query.filter(field >= filter_criteria.value)
            elif filter_criteria.operator == FilterOperator.LESS_THAN:
                query = query.filter(field < filter_criteria.value)
            elif filter_criteria.operator == FilterOperator.LESS_THAN_OR_EQUAL:
                query = query.filter(field <= filter_criteria.value)
            elif filter_criteria.operator == FilterOperator.LIKE:
                if filter_criteria.case_sensitive:
                    query = query.filter(field.like(f"%{filter_criteria.value}%"))
                else:
                    query = query.filter(field.ilike(f"%{filter_criteria.value}%"))
            elif filter_criteria.operator == FilterOperator.ILIKE:
                query = query.filter(field.ilike(f"%{filter_criteria.value}%"))
            elif filter_criteria.operator == FilterOperator.IN:
                query = query.filter(field.in_(filter_criteria.value))
            elif filter_criteria.operator == FilterOperator.NOT_IN:
                query = query.filter(~field.in_(filter_criteria.value))
            elif filter_criteria.operator == FilterOperator.IS_NULL:
                query = query.filter(field.is_(None))
            elif filter_criteria.operator == FilterOperator.IS_NOT_NULL:
                query = query.filter(field.is_not(None))
            elif filter_criteria.operator == FilterOperator.BETWEEN:
                if isinstance(filter_criteria.value, (list, tuple)) and len(filter_criteria.value) == 2:
                    query = query.filter(field.between(filter_criteria.value[0], filter_criteria.value[1]))
        
        return query
    
    def _apply_sorting(self, query: Query, sort_criteria: List[SortCriteria]) -> Query:
        """Apply sorting criteria to query."""
        for sort in sort_criteria:
            if not hasattr(self.model, sort.field):
                logger.warning(f"Sort field {sort.field} not found in model {self.model.__name__}")
                continue
            
            field = getattr(self.model, sort.field)
            
            if sort.direction == SortDirection.DESC:
                query = query.order_by(desc(field))
            else:
                query = query.order_by(asc(field))
        
        return query
    
    def _apply_pagination(self, query: Query, pagination: PaginationParams) -> Query:
        """Apply pagination to query."""
        offset = (pagination.page - 1) * pagination.page_size
        return query.offset(offset).limit(pagination.page_size)
    
    def get_by_id(self, id: Union[int, str, UUID]) -> Optional[ModelType]:
        """Get entity by ID with caching."""
        cache_key = self._get_cache_key(f"id:{id}")
        
        # Check cache first
        if self.enable_caching:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result is not None:
                self._cache_hits += 1
                return cached_result
            self._cache_misses += 1
        
        # Query database
        with self.session_factory() as session:
            query = session.query(self.model).filter(self.model.id == id)
            query = self._apply_tenant_filter(query)
            
            result = query.first()
            self._query_count += 1
            
            # Cache result
            if self.enable_caching and result:
                self.cache_manager.set(cache_key, result, self.cache_ttl)
            
            return result
    
    def get_by_ids(self, ids: List[Union[int, str, UUID]]) -> List[ModelType]:
        """Get multiple entities by IDs with bulk caching."""
        if not ids:
            return []
        
        # Check cache for each ID
        cached_results = {}
        missing_ids = []
        
        if self.enable_caching:
            cache_keys = {id_val: self._get_cache_key(f"id:{id_val}") for id_val in ids}
            cached_data = self.cache_manager.get_many(list(cache_keys.values()))
            
            for id_val, cache_key in cache_keys.items():
                if cache_key in cached_data:
                    cached_results[id_val] = cached_data[cache_key]
                    self._cache_hits += 1
                else:
                    missing_ids.append(id_val)
                    self._cache_misses += 1
        else:
            missing_ids = ids
        
        # Query database for missing IDs
        db_results = []
        if missing_ids:
            with self.session_factory() as session:
                query = session.query(self.model).filter(self.model.id.in_(missing_ids))
                query = self._apply_tenant_filter(query)
                
                db_results = query.all()
                self._query_count += 1
                
                # Cache database results
                if self.enable_caching:
                    cache_data = {}
                    for result in db_results:
                        cache_key = self._get_cache_key(f"id:{result.id}")
                        cache_data[cache_key] = result
                    
                    if cache_data:
                        self.cache_manager.set_many(cache_data, self.cache_ttl)
        
        # Combine cached and database results
        all_results = list(cached_results.values()) + db_results
        
        # Maintain original order
        result_map = {str(item.id): item for item in all_results}
        return [result_map[str(id_val)] for id_val in ids if str(id_val) in result_map]
    
    def get_all(
        self,
        filters: Optional[List[FilterCriteria]] = None,
        sort_criteria: Optional[List[SortCriteria]] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Union[List[ModelType], PaginatedResult[ModelType]]:
        """Get all entities with filtering, sorting, and pagination."""
        with self.session_factory() as session:
            query = session.query(self.model)
            query = self._apply_tenant_filter(query)
            
            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)
            
            # Apply sorting
            if sort_criteria:
                query = self._apply_sorting(query, sort_criteria)
            
            # Handle pagination
            if pagination:
                # Get total count for pagination
                count_query = query.statement.with_only_columns(func.count()).order_by(None)
                total = session.execute(count_query).scalar()
                
                # Apply pagination
                query = self._apply_pagination(query, pagination)
                items = query.all()
                
                self._query_count += 2  # One for count, one for items
                
                return PaginatedResult.create(items, total, pagination)
            else:
                items = query.all()
                self._query_count += 1
                return items
    
    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create new entity."""
        with self.session_factory() as session:
            # Convert schema to model instance
            if hasattr(obj_in, 'dict'):
                # Pydantic model
                obj_data = obj_in.dict()
            elif hasattr(obj_in, '__dict__'):
                # Dataclass or regular object
                obj_data = obj_in.__dict__
            else:
                # Dictionary
                obj_data = obj_in
            
            # Add tenant context if applicable
            if (self.tenant_manager and 
                hasattr(self.model, 'organization_id') and 
                'organization_id' not in obj_data):
                org_id = self.tenant_manager.tenant_context.get_organization_id()
                if org_id:
                    obj_data['organization_id'] = org_id
            
            # Create model instance
            db_obj = self.model(**obj_data)
            
            try:
                session.add(db_obj)
                session.commit()
                session.refresh(db_obj)
                
                # Invalidate related cache entries
                if self.enable_caching:
                    self._invalidate_cache_for_entity(db_obj)
                
                self._query_count += 1
                return db_obj
                
            except SQLAlchemyError as e:
                session.rollback()
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    raise DuplicateEntityError(f"Entity already exists: {e}")
                raise RepositoryError(f"Failed to create entity: {e}")
    
    def update(
        self,
        id: Union[int, str, UUID],
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """Update entity by ID."""
        with self.session_factory() as session:
            # Get existing entity
            query = session.query(self.model).filter(self.model.id == id)
            query = self._apply_tenant_filter(query)
            
            db_obj = query.first()
            if not db_obj:
                raise EntityNotFoundError(f"Entity with id {id} not found")
            
            # Get update data
            if hasattr(obj_in, 'dict'):
                # Pydantic model
                update_data = obj_in.dict(exclude_unset=True)
            elif hasattr(obj_in, '__dict__'):
                # Dataclass or regular object
                update_data = {k: v for k, v in obj_in.__dict__.items() if v is not None}
            else:
                # Dictionary
                update_data = obj_in
            
            # Apply updates
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            # Update timestamp if available
            if hasattr(db_obj, 'updated_at'):
                db_obj.updated_at = datetime.utcnow()
            
            try:
                session.commit()
                session.refresh(db_obj)
                
                # Invalidate cache
                if self.enable_caching:
                    self._invalidate_cache_for_entity(db_obj)
                
                self._query_count += 1
                return db_obj
                
            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to update entity: {e}")
    
    def delete(self, id: Union[int, str, UUID]) -> bool:
        """Delete entity by ID."""
        with self.session_factory() as session:
            query = session.query(self.model).filter(self.model.id == id)
            query = self._apply_tenant_filter(query)
            
            db_obj = query.first()
            if not db_obj:
                raise EntityNotFoundError(f"Entity with id {id} not found")
            
            try:
                session.delete(db_obj)
                session.commit()
                
                # Invalidate cache
                if self.enable_caching:
                    self._invalidate_cache_for_entity(db_obj)
                
                self._query_count += 1
                return True
                
            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to delete entity: {e}")
    
    def soft_delete(self, id: Union[int, str, UUID]) -> Optional[ModelType]:
        """Soft delete entity (mark as deleted)."""
        if not hasattr(self.model, 'is_deleted'):
            raise NotImplementedError("Model does not support soft delete")
        
        update_data = {'is_deleted': True}
        if hasattr(self.model, 'deleted_at'):
            update_data['deleted_at'] = datetime.utcnow()
        
        return self.update(id, update_data)
    
    def count(self, filters: Optional[List[FilterCriteria]] = None) -> int:
        """Count entities with optional filtering."""
        with self.session_factory() as session:
            query = session.query(func.count(self.model.id))
            
            # Apply tenant filter
            if self.tenant_manager and hasattr(self.model, 'organization_id'):
                org_id = self.tenant_manager.tenant_context.get_organization_id()
                if org_id:
                    query = query.filter(self.model.organization_id == org_id)
            
            # Apply filters
            if filters:
                # Need to join with main table for filtering
                query = session.query(self.model)
                query = self._apply_tenant_filter(query)
                query = self._apply_filters(query, filters)
                query = query.with_entities(func.count(self.model.id))
            
            result = query.scalar()
            self._query_count += 1
            return result or 0
    
    def exists(self, id: Union[int, str, UUID]) -> bool:
        """Check if entity exists by ID."""
        with self.session_factory() as session:
            query = session.query(self.model.id).filter(self.model.id == id)
            query = self._apply_tenant_filter(query)
            
            result = query.first()
            self._query_count += 1
            return result is not None
    
    def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Bulk create entities."""
        if not objects:
            return []
        
        with self.session_factory() as session:
            db_objects = []
            
            for obj_in in objects:
                # Convert schema to dict
                if hasattr(obj_in, 'dict'):
                    obj_data = obj_in.dict()
                elif hasattr(obj_in, '__dict__'):
                    obj_data = obj_in.__dict__
                else:
                    obj_data = obj_in
                
                # Add tenant context
                if (self.tenant_manager and 
                    hasattr(self.model, 'organization_id') and 
                    'organization_id' not in obj_data):
                    org_id = self.tenant_manager.tenant_context.get_organization_id()
                    if org_id:
                        obj_data['organization_id'] = org_id
                
                db_obj = self.model(**obj_data)
                db_objects.append(db_obj)
            
            try:
                session.add_all(db_objects)
                session.commit()
                
                # Refresh all objects
                for db_obj in db_objects:
                    session.refresh(db_obj)
                
                # Invalidate cache
                if self.enable_caching:
                    for db_obj in db_objects:
                        self._invalidate_cache_for_entity(db_obj)
                
                self._query_count += 1
                return db_objects
                
            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to bulk create entities: {e}")
    
    def bulk_update(
        self,
        updates: List[Dict[str, Any]],
        filters: Optional[List[FilterCriteria]] = None
    ) -> int:
        """Bulk update entities."""
        with self.session_factory() as session:
            query = session.query(self.model)
            query = self._apply_tenant_filter(query)
            
            if filters:
                query = self._apply_filters(query, filters)
            
            try:
                # Build update values
                update_values = {}
                for update_dict in updates:
                    update_values.update(update_dict)
                
                # Add timestamp
                if hasattr(self.model, 'updated_at'):
                    update_values['updated_at'] = datetime.utcnow()
                
                result = query.update(update_values, synchronize_session=False)
                session.commit()
                
                # Invalidate cache (broad invalidation)
                if self.enable_caching:
                    self._invalidate_cache_pattern(f"{self._get_cache_key_prefix()}:*")
                
                self._query_count += 1
                return result
                
            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to bulk update entities: {e}")
    
    def _invalidate_cache_for_entity(self, entity: ModelType):
        """Invalidate cache entries for specific entity."""
        if not self.enable_caching:
            return
        
        # Invalidate by ID
        cache_key = self._get_cache_key(f"id:{entity.id}")
        self.cache_manager.delete(cache_key)
        
        # Could add more specific cache invalidation patterns here
    
    def _invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        if not self.enable_caching:
            return
        
        # Implementation depends on cache manager capabilities
        # For now, we can clear tenant-specific cache
        if self.tenant_manager:
            org_id = self.tenant_manager.tenant_context.get_organization_id()
            if org_id:
                self.cache_manager.clear_tenant_cache(org_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get repository performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_ratio = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "query_count": self._query_count,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_ratio_percent": round(hit_ratio, 2),
            "caching_enabled": self.enable_caching
        }
    
    def clear_performance_stats(self):
        """Clear performance statistics."""
        self._query_count = 0
        self._cache_hits = 0
        self._cache_misses = 0


class ReadOnlyRepository(BaseRepository[ModelType, None, None]):
    """Read-only repository for view-like entities."""
    
    def create(self, obj_in) -> ModelType:
        """Not supported in read-only repository."""
        raise NotImplementedError("Create operation not supported in read-only repository")
    
    def update(self, id, obj_in) -> Optional[ModelType]:
        """Not supported in read-only repository."""
        raise NotImplementedError("Update operation not supported in read-only repository")
    
    def delete(self, id) -> bool:
        """Not supported in read-only repository."""
        raise NotImplementedError("Delete operation not supported in read-only repository")
    
    def bulk_create(self, objects) -> List[ModelType]:
        """Not supported in read-only repository."""
        raise NotImplementedError("Bulk create operation not supported in read-only repository")
    
    def bulk_update(self, updates, filters=None) -> int:
        """Not supported in read-only repository."""
        raise NotImplementedError("Bulk update operation not supported in read-only repository")


# Utility functions for creating filter and sort criteria
def create_filter(field: str, operator: FilterOperator, value: Any, case_sensitive: bool = True) -> FilterCriteria:
    """Create filter criteria."""
    return FilterCriteria(field, operator, value, case_sensitive)


def create_sort(field: str, direction: SortDirection = SortDirection.ASC) -> SortCriteria:
    """Create sort criteria."""
    return SortCriteria(field, direction)


def create_pagination(page: int = 1, page_size: int = 20, max_page_size: int = 1000) -> PaginationParams:
    """Create pagination parameters."""
    return PaginationParams(page, page_size, max_page_size)