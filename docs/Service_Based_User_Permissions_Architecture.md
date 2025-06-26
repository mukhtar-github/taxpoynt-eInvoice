# Service-Based User Permissions Architecture

**Document**: Enhanced User Role and Permission System Design  
**Date**: June 26, 2025  
**Context**: TaxPoynt Multi-Service Platform Architecture  
**Status**: Design Complete - Ready for Implementation  

---

## 🎯 **Problem Statement**

### **Current Gap Analysis**

The existing rigid role structure doesn't accommodate TaxPoynt's diverse service offerings:

```python
# Current roles don't cover all use cases
SI_USER      → ERP/CRM integration services ✓
MEMBER       → Basic organization access ✓  
Admin roles  → Administrative functions ✓
APP_USER     → FIRS e-invoicing services ❌ (MISSING!)
```

### **Real-World User Scenarios**

#### Scenario 1: Pure APP User
```
- Small business owner
- Only needs FIRS e-invoicing
- No ERP integration required
- Current system: Forced into SI_USER role ❌
```

#### Scenario 2: Pure SI User  
```
- ERP consultant
- Helps with Odoo/SAP integration
- No direct invoicing needs
- Current system: Works fine ✅
```

#### Scenario 3: Hybrid User (Critical Gap!)
```
- Large enterprise client
- Needs ERP integration AND e-invoicing
- Should access both SI and APP services
- Current system: Can't handle this ❌
```

#### Scenario 4: TaxPoynt Executive
```
- Platform owner/executive
- Needs oversight of all services
- Requires compliance monitoring access
- Current system: Limited admin role ❌
```

---

## 🏗️ **Recommended Architecture: Service-Based Permissions**

### **Core Concepts**

1. **Services**: Different offerings TaxPoynt provides
2. **Access Levels**: Granular permissions within each service
3. **Many-to-Many**: Users can access multiple services with different levels
4. **Time-bound**: Access can expire (useful for trials, contractors)
5. **Auditable**: Track who granted access and when

### **Service Types Definition**

```python
class ServiceType(Enum):
    """Types of services TaxPoynt provides"""
    SYSTEM_INTEGRATION = "system_integration"      # ERP/CRM integrations
    ACCESS_POINT_PROVIDER = "access_point_provider" # FIRS e-invoicing
    NIGERIAN_COMPLIANCE = "nigerian_compliance"     # Regulatory monitoring
    ORGANIZATION_MANAGEMENT = "organization_management" # Admin functions

class AccessLevel(Enum):
    """Access levels for each service"""
    READ = "read"           # View only
    WRITE = "write"         # Create/modify
    ADMIN = "admin"         # Full control
    OWNER = "owner"         # TaxPoynt executives only
```

### **Database Schema**

#### **UserServiceAccess Model**
```python
class UserServiceAccess(Base):
    """Many-to-many relationship: Users can access multiple services"""
    __tablename__ = "user_service_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    service_type = Column(Enum(ServiceType))
    access_level = Column(Enum(AccessLevel))
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])
```

#### **Enhanced User Model**
```python
class User(Base):
    # ... existing fields ...
    
    # Remove single role constraint
    # role = Column(Enum(UserRole), default=UserRole.SI_USER)  # Remove this
    
    # Add service access relationships
    service_access = relationship("UserServiceAccess", foreign_keys="UserServiceAccess.user_id")
    
    def has_service_access(self, service: ServiceType, level: AccessLevel = AccessLevel.READ) -> bool:
        """Check if user has access to a specific service"""
        access_levels = {
            AccessLevel.READ: 1, 
            AccessLevel.WRITE: 2, 
            AccessLevel.ADMIN: 3, 
            AccessLevel.OWNER: 4
        }
        
        for access in self.service_access:
            if (access.service_type == service and 
                access.is_active and 
                (access.expires_at is None or access.expires_at > datetime.utcnow()) and
                access_levels[access.access_level] >= access_levels[level]):
                return True
        return False
    
    def get_accessible_services(self) -> List[ServiceType]:
        """Get list of services user can access"""
        services = []
        for access in self.service_access:
            if (access.is_active and 
                (access.expires_at is None or access.expires_at > datetime.utcnow())):
                services.append(access.service_type)
        return list(set(services))
```

---

## 🔐 **Permission System Implementation**

### **Permission Decorators**

```python
# app/dependencies/permissions.py
def require_service_access(service: ServiceType, level: AccessLevel = AccessLevel.READ):
    """Decorator to require specific service access"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user.has_service_access(service, level):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: {service.value} service requires {level.value} permission"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Convenience decorators for common patterns
def require_app_access(level: AccessLevel = AccessLevel.READ):
    return require_service_access(ServiceType.ACCESS_POINT_PROVIDER, level)

def require_si_access(level: AccessLevel = AccessLevel.READ):
    return require_service_access(ServiceType.SYSTEM_INTEGRATION, level)

def require_compliance_access(level: AccessLevel = AccessLevel.READ):
    return require_service_access(ServiceType.NIGERIAN_COMPLIANCE, level)

def require_owner_access():
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            has_owner_access = any(
                access.access_level == AccessLevel.OWNER 
                for access in current_user.service_access 
                if access.is_active
            )
            if not has_owner_access:
                raise HTTPException(status_code=403, detail="Owner access required")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### **Route Protection Examples**

```python
# app/routes/irn.py
@router.post("/irn/generate")
@require_app_access(AccessLevel.WRITE)
async def generate_irn(current_user: User = Depends(get_current_user)):
    """Only users with APP write access can generate IRNs"""
    pass

# app/routes/integrations.py
@router.get("/integrations/odoo")
@require_si_access(AccessLevel.READ)
async def get_odoo_status(current_user: User = Depends(get_current_user)):
    """Only users with SI read access can view integrations"""
    pass

# app/routes/nigerian_compliance.py
@router.get("/nigerian-compliance/overview/{org_id}")
@require_compliance_access(AccessLevel.READ)
async def get_compliance_overview(current_user: User = Depends(get_current_user)):
    """Only users with compliance access can view regulatory data"""
    pass

# app/routes/admin.py
@router.delete("/admin/users/{user_id}")
@require_owner_access()
async def delete_user(current_user: User = Depends(get_current_user)):
    """Only TaxPoynt owners can delete users"""
    pass
```

---

## 📊 **User Type Examples and Permissions**

### **Pure APP User (Small Business)**
```python
user_permissions = [
    UserServiceAccess(
        service_type=ServiceType.ACCESS_POINT_PROVIDER,
        access_level=AccessLevel.WRITE
    ),
    UserServiceAccess(
        service_type=ServiceType.NIGERIAN_COMPLIANCE,
        access_level=AccessLevel.READ
    )
]

# Capabilities:
# ✅ Generate IRNs and submit to FIRS
# ✅ View invoice history
# ✅ Check compliance status
# ❌ Access ERP integrations
# ❌ Admin functions
```

### **Pure SI User (Integration Consultant)**
```python
user_permissions = [
    UserServiceAccess(
        service_type=ServiceType.SYSTEM_INTEGRATION,
        access_level=AccessLevel.ADMIN
    )
]

# Capabilities:
# ✅ Manage ERP/CRM integrations
# ✅ Configure Odoo connections
# ✅ Set up data mappings
# ❌ Generate IRNs
# ❌ Access compliance data
```

### **Hybrid User (Enterprise Client)**
```python
user_permissions = [
    UserServiceAccess(
        service_type=ServiceType.SYSTEM_INTEGRATION,
        access_level=AccessLevel.WRITE
    ),
    UserServiceAccess(
        service_type=ServiceType.ACCESS_POINT_PROVIDER,
        access_level=AccessLevel.WRITE
    ),
    UserServiceAccess(
        service_type=ServiceType.NIGERIAN_COMPLIANCE,
        access_level=AccessLevel.READ
    )
]

# Capabilities:
# ✅ Manage integrations AND generate IRNs
# ✅ Full-service access
# ✅ View compliance monitoring
# ❌ TaxPoynt platform administration
```

### **Organization Admin**
```python
user_permissions = [
    UserServiceAccess(
        service_type=ServiceType.ACCESS_POINT_PROVIDER,
        access_level=AccessLevel.ADMIN
    ),
    UserServiceAccess(
        service_type=ServiceType.SYSTEM_INTEGRATION,
        access_level=AccessLevel.ADMIN
    ),
    UserServiceAccess(
        service_type=ServiceType.ORGANIZATION_MANAGEMENT,
        access_level=AccessLevel.ADMIN
    ),
    UserServiceAccess(
        service_type=ServiceType.NIGERIAN_COMPLIANCE,
        access_level=AccessLevel.READ
    )
]

# Capabilities:
# ✅ Manage organization users
# ✅ Full service access for their org
# ✅ View compliance data
# ❌ TaxPoynt platform oversight
```

### **TaxPoynt Executive**
```python
user_permissions = [
    UserServiceAccess(service_type=ServiceType.SYSTEM_INTEGRATION, access_level=AccessLevel.OWNER),
    UserServiceAccess(service_type=ServiceType.ACCESS_POINT_PROVIDER, access_level=AccessLevel.OWNER),
    UserServiceAccess(service_type=ServiceType.NIGERIAN_COMPLIANCE, access_level=AccessLevel.OWNER),
    UserServiceAccess(service_type=ServiceType.ORGANIZATION_MANAGEMENT, access_level=AccessLevel.OWNER)
]

# Capabilities:
# ✅ Everything - full platform oversight
# ✅ User management across all organizations
# ✅ Compliance monitoring and reporting
# ✅ Platform configuration and settings
```

---

## 💼 **Business Benefits**

### **Flexible Pricing Models**
```
Service Packages:
├── Starter Package (APP only)
│   ├── Price: $50/month
│   ├── Features: Basic e-invoicing, FIRS submission
│   └── Target: Small businesses
│
├── Integration Package (SI only)  
│   ├── Price: $200/month
│   ├── Features: ERP/CRM integration, data mapping
│   └── Target: System integrators, consultants
│
├── Enterprise Package (APP + SI)
│   ├── Price: $400/month
│   ├── Features: Full service integration + e-invoicing
│   └── Target: Large enterprises
│
└── Compliance Plus (All services)
    ├── Price: $600/month
    ├── Features: Everything + compliance monitoring
    └── Target: Regulated industries, public companies
```

### **Improved User Experience**
```
Dashboard Benefits:
├── Users see only relevant services
├── No confusing features they can't access  
├── Streamlined workflows per service type
├── Service-specific onboarding flows
└── Contextual help and documentation
```

### **Operational Benefits**
```
Administrative Advantages:
├── Granular access control
├── Time-bound access for contractors
├── Audit trail for compliance
├── Easy service provisioning
└── Flexible user management
```

---

## 🚀 **Migration Strategy**

### **Phase 1: Add Service Access Model (Week 1)**
```python
# Create new models without breaking existing system
# Add UserServiceAccess table
# Keep existing role system temporarily

# Migration mapping
role_mapping = {
    UserRole.SI_USER: [
        (ServiceType.SYSTEM_INTEGRATION, AccessLevel.WRITE)
    ],
    UserRole.MEMBER: [
        (ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.WRITE)
    ],
    UserRole.ADMIN: [
        (ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.ADMIN),
        (ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.ADMIN),
        (ServiceType.SYSTEM_INTEGRATION, AccessLevel.ADMIN)
    ]
}
```

### **Phase 2: Gradual Migration (Week 2)**
```python
# Migration script
def migrate_existing_users():
    for user in User.query.all():
        current_role = user.role
        service_permissions = role_mapping.get(current_role, [])
        
        for service_type, access_level in service_permissions:
            service_access = UserServiceAccess(
                user_id=user.id,
                service_type=service_type,
                access_level=access_level,
                granted_by=admin_user.id,  # System migration
                granted_at=datetime.utcnow()
            )
            db.add(service_access)
    
    db.commit()
```

### **Phase 3: Update Authentication Logic (Week 3)**
```python
# Update all route decorators
# Replace role-based checks with service-based checks
# Test thoroughly with different user types

# Before
@require_role(UserRole.SI_USER)

# After  
@require_si_access(AccessLevel.WRITE)
```

### **Phase 4: Remove Old Role System (Week 4)**
```python
# After thorough testing:
# 1. Remove role column from User model
# 2. Remove UserRole enum
# 3. Update all references
# 4. Deploy new permission system
# 5. Update documentation
```

---

## 🧪 **Testing Strategy**

### **Unit Tests**
```python
def test_user_service_access():
    user = create_test_user()
    grant_service_access(user, ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.WRITE)
    
    assert user.has_service_access(ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.READ)
    assert user.has_service_access(ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.WRITE)
    assert not user.has_service_access(ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.ADMIN)
    assert not user.has_service_access(ServiceType.SYSTEM_INTEGRATION, AccessLevel.READ)

def test_expired_access():
    user = create_test_user()
    grant_service_access(
        user, 
        ServiceType.ACCESS_POINT_PROVIDER, 
        AccessLevel.WRITE,
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
    )
    
    assert not user.has_service_access(ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.READ)
```

### **Integration Tests**
```python
def test_route_protection():
    # Test that routes properly enforce service access
    client = TestClient(app)
    
    # User with only SI access tries to access APP endpoint
    si_user = create_si_user()
    response = client.post("/api/v1/irn/generate", headers=auth_headers(si_user))
    assert response.status_code == 403
    
    # User with APP access can access APP endpoint
    app_user = create_app_user()
    response = client.post("/api/v1/irn/generate", headers=auth_headers(app_user))
    assert response.status_code == 200
```

---

## 📋 **API Endpoints for Service Management**

### **Service Access Management Routes**
```python
# app/routes/service_access.py

@router.post("/users/{user_id}/service-access")
@require_owner_access()
async def grant_service_access(
    user_id: UUID,
    service_type: ServiceType,
    access_level: AccessLevel,
    expires_at: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Grant service access to a user"""
    pass

@router.delete("/users/{user_id}/service-access/{access_id}")
@require_owner_access()
async def revoke_service_access(
    user_id: UUID,
    access_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Revoke service access from a user"""
    pass

@router.get("/users/{user_id}/service-access")
@require_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.READ)
async def list_user_service_access(
    user_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """List all service access for a user"""
    pass

@router.get("/services/available")
async def list_available_services(current_user: User = Depends(get_current_user)):
    """List services available to the current user"""
    return {
        "accessible_services": current_user.get_accessible_services(),
        "service_details": {
            service.value: {
                "name": service.value.replace("_", " ").title(),
                "description": get_service_description(service)
            }
            for service in current_user.get_accessible_services()
        }
    }
```

---

## 🎯 **Frontend Implementation Considerations**

### **Dynamic Navigation**
```typescript
// Frontend service access check
interface UserServiceAccess {
  serviceType: string;
  accessLevel: string;
  expiresAt?: string;
}

const useServiceAccess = () => {
  const { user } = useAuth();
  
  const hasAccess = (service: string, level: string = 'read') => {
    return user?.serviceAccess?.some(access => 
      access.serviceType === service && 
      hasRequiredLevel(access.accessLevel, level) &&
      (!access.expiresAt || new Date(access.expiresAt) > new Date())
    );
  };
  
  return { hasAccess };
};

// Dynamic dashboard navigation
const DashboardNav = () => {
  const { hasAccess } = useServiceAccess();
  
  return (
    <nav>
      {hasAccess('access_point_provider') && (
        <NavItem href="/invoices" icon="📄">e-Invoicing</NavItem>
      )}
      {hasAccess('system_integration') && (
        <NavItem href="/integrations" icon="🔗">Integrations</NavItem>
      )}
      {hasAccess('nigerian_compliance') && (
        <NavItem href="/compliance" icon="🏛️">Compliance</NavItem>
      )}
      {hasAccess('organization_management', 'admin') && (
        <NavItem href="/admin" icon="⚙️">Administration</NavItem>
      )}
    </nav>
  );
};
```

---

## 📈 **Success Metrics**

### **Technical Metrics**
- **Reduced Permission Errors**: Target 90% reduction in 403 errors
- **Improved API Response Times**: Faster permission checks
- **Higher Test Coverage**: 95%+ coverage for permission logic

### **Business Metrics**
- **User Satisfaction**: Survey scores for ease of access
- **Service Adoption**: Users utilizing multiple services
- **Support Ticket Reduction**: Fewer access-related issues

### **Operational Metrics**
- **Onboarding Time**: Faster user setup with appropriate access
- **Security Incidents**: Zero unauthorized access events
- **Audit Compliance**: 100% pass rate for access audits

---

## 📋 **Summary**

This service-based permission architecture addresses the critical gap in TaxPoynt's user management system by:

1. **Flexibility**: Users can access multiple services with appropriate permissions
2. **Scalability**: Easy to add new services and permission levels
3. **Security**: Granular control with audit trails
4. **Business Alignment**: Supports diverse pricing and service models
5. **User Experience**: Streamlined interfaces showing only relevant features

### **Key Implementation Points**:
- ✅ Backward compatible migration strategy
- ✅ Comprehensive testing approach
- ✅ API endpoints for service management
- ✅ Frontend considerations documented
- ✅ Business benefits clearly defined

This architecture positions TaxPoynt to serve diverse client needs while maintaining security and operational excellence.