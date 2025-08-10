# TaxPoynt Role Management System

A comprehensive role-based UI management system for the TaxPoynt platform, providing role detection, permission management, access control, and feature flags.

## Overview

The TaxPoynt Role Management System provides:

- **Role Detection**: Automatically detect user roles from authentication context
- **Permission Management**: Fine-grained permission-based access control
- **Role Switching**: Allow users to switch between SI/APP views (for hybrid users)
- **Access Guards**: Component and route-level access protection
- **Feature Flags**: Role-based feature enablement and A/B testing

## Architecture

```
role_management/
├── role_detector.tsx           # Core role detection and management
├── permission_provider.tsx     # Permission-based access control
├── role_switcher.tsx          # UI for role switching
├── access_guard.tsx           # Component/route guards
├── feature_flag_provider.tsx  # Feature flag management
├── combined_provider.tsx      # All-in-one provider setup
└── index.ts                   # Main exports
```

## Quick Start

### 1. Basic Setup

Wrap your app with the combined provider:

```tsx
import { CombinedRoleProvider } from '@/role_management';

function App() {
  return (
    <CombinedRoleProvider authToken={userToken}>
      <Routes />
    </CombinedRoleProvider>
  );
}
```

### 2. Individual Provider Setup

For more control, use individual providers:

```tsx
import { 
  RoleDetectorProvider, 
  PermissionProvider, 
  FeatureFlagProvider 
} from '@/role_management';

function App() {
  return (
    <RoleDetectorProvider authToken={userToken}>
      <PermissionProvider>
        <FeatureFlagProvider>
          <Routes />
        </FeatureFlagProvider>
      </PermissionProvider>
    </RoleDetectorProvider>
  );
}
```

## Core Components

### Role Detection

Automatically detects user roles from JWT tokens or session data:

```tsx
import { useRoleDetector, PlatformRole } from '@/role_management';

function UserProfile() {
  const { detectionResult, switchRole } = useRoleDetector();
  
  const currentRole = detectionResult?.primaryRole;
  const canSwitch = detectionResult?.canSwitchRoles;
  
  return (
    <div>
      <p>Current Role: {currentRole}</p>
      {canSwitch && (
        <button onClick={() => switchRole(PlatformRole.SYSTEM_INTEGRATOR)}>
          Switch to SI
        </button>
      )}
    </div>
  );
}
```

### Permission Management

Check permissions throughout your app:

```tsx
import { usePermissions } from '@/role_management';

function BillingPage() {
  const { hasPermission, canPerformAction } = usePermissions();
  
  const canViewBilling = hasPermission('si_billing_access');
  const canCreateInvoice = canPerformAction('create', 'invoice');
  
  if (!canViewBilling) {
    return <div>Access denied</div>;
  }
  
  return (
    <div>
      <h1>Billing Dashboard</h1>
      {canCreateInvoice && (
        <button>Create New Invoice</button>
      )}
    </div>
  );
}
```

### Access Guards

Protect components with role/permission requirements:

```tsx
import { RoleGuard, PermissionGuard, PlatformRole } from '@/role_management';

// Role-based protection
<RoleGuard requiredRoles={[PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID]}>
  <BillingComponent />
</RoleGuard>

// Permission-based protection
<PermissionGuard requiredPermissions={['si_billing_access']}>
  <InvoiceCreator />
</PermissionGuard>

// Multiple conditions
<AccessGuard
  type="role"
  level="strict"
  requiredRoles={[PlatformRole.PLATFORM_ADMIN]}
  fallbackBehavior="redirect"
  redirectTo="/unauthorized"
>
  <AdminPanel />
</AccessGuard>
```

### Role Switcher

UI component for role switching:

```tsx
import { RoleSwitcher } from '@/role_management';

// Dropdown variant
<RoleSwitcher variant="dropdown" showDescription={true} />

// Tab variant
<RoleSwitcher variant="tabs" />

// Card variant
<RoleSwitcher variant="cards" showCapabilities={true} />
```

### Feature Flags

Conditional feature enablement:

```tsx
import { useFeatureFlags, FeatureGate, useFeature } from '@/role_management';

// Using the hook
function Dashboard() {
  const { isEnabled } = useFeatureFlags();
  
  return (
    <div>
      {isEnabled('enhanced_reporting') && (
        <AdvancedReports />
      )}
    </div>
  );
}

// Using the component
<FeatureGate feature="si_advanced_integration">
  <AdvancedIntegrationPanel />
</FeatureGate>

// Using the convenience hook
function ThemeToggle() {
  const { enabled } = useFeature('dark_mode');
  
  return enabled ? <DarkModeToggle /> : null;
}
```

## TaxPoynt Roles

The system supports all TaxPoynt platform roles:

### System Integrator (SI)
- **Purpose**: Manage integrations with ERPs, CRMs, and business systems
- **Key Features**: Integration management, certificate handling, commercial billing
- **Icon**: 🔗
- **Color**: Blue

### Access Point Provider (APP)
- **Purpose**: Submit invoices to FIRS and manage compliance
- **Key Features**: FIRS submission, compliance monitoring, grant management
- **Icon**: 🏛️
- **Color**: Green

### Hybrid Premium
- **Purpose**: Full access to both SI and APP capabilities
- **Key Features**: All SI + APP features, advanced analytics, premium support
- **Icon**: 👑
- **Color**: Purple

### Platform Admin
- **Purpose**: Administer the entire TaxPoynt platform
- **Key Features**: User management, system configuration, grant administration
- **Icon**: ⚙️
- **Color**: Red

### Tenant Admin
- **Purpose**: Administer organization/tenant
- **Key Features**: Organization management, user administration
- **Icon**: 👥
- **Color**: Orange

### User
- **Purpose**: Basic platform access
- **Key Features**: View data, basic reporting, profile management
- **Icon**: 👤
- **Color**: Gray

## Common Permissions

```typescript
// SI Permissions
SI_CREATE_INTEGRATION: 'si_integration_create'
SI_MANAGE_CERTIFICATES: 'si_certificate_manage'
SI_ACCESS_BILLING: 'si_billing_access'

// APP Permissions
APP_SUBMIT_INVOICE: 'app_invoice_submit'
APP_MONITOR_COMPLIANCE: 'app_compliance_monitor'
APP_ACCESS_GRANTS: 'app_grant_access'

// Admin Permissions
ADMIN_MANAGE_USERS: 'admin_user_manage'
ADMIN_SYSTEM_CONFIG: 'admin_system_config'
ADMIN_MANAGE_GRANTS: 'admin_grant_manage'
```

## Feature Flags

### SI Features
- `si_advanced_integration`: Advanced integration capabilities
- `si_custom_schemas`: Custom invoice schema support
- `si_white_label`: White label branding

### APP Features
- `app_bulk_submission`: Bulk invoice submission
- `app_real_time_validation`: Real-time FIRS validation
- `app_grant_tracking`: Grant compliance tracking

### Hybrid Features
- `hybrid_cross_role_analytics`: Cross-role analytics
- `hybrid_unified_dashboard`: Unified SI+APP dashboard

### General Features
- `enhanced_reporting`: Advanced reporting capabilities
- `dark_mode`: Dark mode UI

## Advanced Usage

### Custom Guards

Create custom access logic:

```tsx
import { AccessGuard, GuardType, AccessLevel } from '@/role_management';

<AccessGuard
  type={GuardType.CUSTOM}
  customCondition={(context) => {
    // Custom logic here
    return context.userRoles.includes(PlatformRole.HYBRID) && 
           context.organizationId === 'special-org';
  }}
  fallbackBehavior="show_message"
  fallbackMessage="This feature requires hybrid role in a special organization"
>
  <SpecialFeature />
</AccessGuard>
```

### HOCs for Component Protection

```tsx
import { withRoleGuard, withPermissionGuard } from '@/role_management';

// Protect entire components
const ProtectedBilling = withRoleGuard(
  BillingComponent,
  [PlatformRole.SYSTEM_INTEGRATOR],
  <div>SI access required</div>
);

const ProtectedInvoicing = withPermissionGuard(
  InvoicingComponent,
  ['app_invoice_submit'],
  <div>Invoice permission required</div>
);
```

### Development Tools

Enable dev tools in development:

```tsx
<CombinedRoleProvider 
  authToken={token}
  enableDevTools={process.env.NODE_ENV === 'development'}
>
  <App />
</CombinedRoleProvider>
```

## Integration with Backend

The system integrates with TaxPoynt's backend role management:

- **Role Manager**: `core_platform/authentication/role_manager.py`
- **API Gateway**: `api_gateway/role_routing/`
- **HTTP Detection**: `api_gateway/role_routing/role_detector.py`

Role data flows from:
1. Backend authentication → JWT token
2. Frontend role detector → User context
3. Permission provider → Access decisions
4. UI components → Conditional rendering

## Error Handling

The system includes comprehensive error handling:

```tsx
<CombinedRoleProvider
  authToken={token}
  onError={(error, context) => {
    console.error('Role management error:', error, context);
    // Send to error tracking service
  }}
  errorFallback={<CustomErrorPage />}
>
  <App />
</CombinedRoleProvider>
```

## Performance Considerations

- **Caching**: Permission checks and role evaluations are cached
- **Memoization**: Components use React.memo and useMemo for optimization
- **Lazy Loading**: Guards prevent unnecessary component mounting
- **Batch Updates**: Multiple permission checks are batched

## Testing

Test role-based functionality:

```tsx
import { render } from '@testing-library/react';
import { CombinedRoleProvider } from '@/role_management';

function renderWithRole(component, role = PlatformRole.USER) {
  const mockToken = createMockToken({ role });
  
  return render(
    <CombinedRoleProvider authToken={mockToken}>
      {component}
    </CombinedRoleProvider>
  );
}

test('SI users can access billing', () => {
  const { getByText } = renderWithRole(
    <BillingPage />, 
    PlatformRole.SYSTEM_INTEGRATOR
  );
  
  expect(getByText('Billing Dashboard')).toBeInTheDocument();
});
```

## Best Practices

1. **Use Guards Liberally**: Protect sensitive components and routes
2. **Granular Permissions**: Use specific permissions rather than broad role checks
3. **Fallback UI**: Always provide meaningful fallbacks for denied access
4. **Performance**: Use permission checks in render logic, not in loops
5. **Testing**: Test all role combinations and edge cases
6. **Documentation**: Document permission requirements in component comments

## Migration Guide

To integrate with existing TaxPoynt components:

1. **Wrap App**: Add `CombinedRoleProvider` to your root component
2. **Add Guards**: Wrap existing components with appropriate guards
3. **Update Navigation**: Use role-based navigation visibility
4. **Feature Flags**: Migrate existing feature toggles to the flag system
5. **Testing**: Update tests to include role context

## Contributing

When adding new roles, permissions, or features:

1. Update type definitions in the appropriate provider
2. Add to the common constants in `index.ts`
3. Update this documentation
4. Add comprehensive tests
5. Consider backward compatibility

## Support

For questions or issues with the role management system:

- Check the integration guide in `index.ts`
- Review error messages in the browser console
- Enable dev tools for debugging
- Refer to backend role management documentation