# Migration Guide: MobileNavigation to MobileNav

This guide outlines the process of migrating from the old `MobileNavigation` component to the new `MobileNav` component.

## Why Migrate?

The new `MobileNav` component offers several advantages:

- Uses Tailwind CSS instead of Chakra UI for better performance
- Implements modern animation transitions for a smoother user experience
- Uses Lucide icons which are more lightweight and consistent with our design system
- Has improved accessibility features
- Better TypeScript support
- Consistent with our new UI component system

## Migration Plan

### Phase 1: Parallel Implementation (Current)

- Both components exist in the codebase:
  - Old: `MobileNavigation.tsx` (Chakra UI-based)
  - New: `MobileNav.tsx` (Tailwind CSS-based)
- A compatibility layer `MobileNavigationAliases.tsx` is provided
- New projects should use `MobileNav`
- Test page available at `/mobile-nav-test`

### Phase 2: Update Existing Usage

- Find all imports of `MobileNavigation` and update them to use `MobileNav`
- Update any component styling to match Tailwind patterns
- Test thoroughly on all devices and browsers

### Phase 3: Removal

- Once all usage has been migrated, remove:
  - `MobileNavigation.tsx`
  - `MobileNavigationAliases.tsx`

## Usage Comparison

### Old Usage (MobileNavigation)

```tsx
import { MobileNavigation } from '../components/ui/MobileNavigation';

// In your component
<MobileNavigation 
  title="App Name"
  userInfo={{ name: "John Doe", email: "john@example.com" }}
  onLogout={() => handleLogout()}
/>
```

### New Usage (MobileNav)

```tsx
import { MobileNav } from '../components/ui/MobileNav';

// In your component
<MobileNav 
  title="App Name"
  userInfo={{ name: "John Doe", email: "john@example.com" }}
  onLogout={() => handleLogout()}
/>
```

## API Comparison

Both components share the same props interface:

| Prop | Type | Description |
|------|------|-------------|
| title | string | The title displayed in the nav bar |
| logo | ReactNode | Optional logo component |
| showProfileInfo | boolean | Whether to show user profile info |
| userInfo | { name: string; email: string; avatar?: string } | User information |
| navItems | Array of NavItems | Navigation menu items |
| onLogout | function | Callback for logout action |

## Testing

Before removing the old component, ensure the new component is thoroughly tested:

1. Responsive behavior on different screen sizes
2. Proper display of navigation items and user info
3. Correct active state highlighting for current route
4. Smooth open/close animations
5. Backdrop click to close functionality
6. Browser compatibility (Chrome, Firefox, Safari, Edge)
7. Mobile device testing (iOS and Android)

## Need Help?

If you encounter any issues during migration, please contact the UI team or refer to the example implementation at `/mobile-nav-test`. 