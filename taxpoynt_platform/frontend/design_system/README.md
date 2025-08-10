# TaxPoynt Design System

## Overview

The TaxPoynt Design System provides the foundational building blocks for consistent UI across the entire platform. It serves as the **single source of truth** for visual design, containing design tokens and primitive components.

## Architecture

```
design_system/
├── tokens.ts           # Design tokens (colors, typography, spacing)
├── components/         # Primitive UI components
│   ├── Button.tsx     # Role-aware button primitive
│   ├── Input.tsx      # Role-aware input primitive
│   └── index.ts       # Component exports
└── README.md          # This file
```

## Role-Based Theming

The design system supports TaxPoynt's four user roles with distinct visual identities:

### SI (System Integrator) - Default
- **Primary Color**: TaxPoynt Blue (`#0054B0`)
- **Use Case**: Default platform experience
- **Audience**: Businesses integrating with TaxPoynt

### APP (Access Point Provider)
- **Primary Color**: Nigerian Green (`#008751`) 
- **Use Case**: FIRS compliance workflows
- **Audience**: Businesses using TaxPoynt for Nigerian tax compliance

### Hybrid
- **Primary Color**: Premium Indigo (`#6366F1`)
- **Use Case**: Advanced multi-role workflows
- **Audience**: Power users with multiple roles

### Admin
- **Primary Color**: Distinctive Purple (`#7C3AED`)
- **Use Case**: Platform administration
- **Audience**: TaxPoynt administrators

## Component Principles

### Primitive Components Only
- Keep components simple and focused
- No business logic - only visual and interaction patterns
- Composable building blocks for complex components

### Consistent API
- Role-based theming via `role` prop
- Standard size variants: `sm`, `md`, `lg`, `xl`
- Consistent variant naming: `primary`, `secondary`, `outline`, `ghost`, `destructive`

### Accessibility First
- ARIA labels and semantic HTML
- Keyboard navigation support
- Focus management
- Screen reader compatibility

## Usage

### Direct Import (Recommended for primitives)
```tsx
import { Button, Input } from '../design_system/components';

<Button variant="primary" role="app">Submit Invoice</Button>
<Input placeholder="Enter amount" role="app" />
```

### Via Shared Components (Recommended for consistency)
```tsx
import { Button, Input } from '../shared_components';

<Button variant="primary" role="hybrid">Process Transaction</Button>
```

## Technology Stack

- **TailwindCSS**: Utility-first styling
- **class-variance-authority**: Type-safe variant handling
- **TypeScript**: Full type safety
- **React**: Component architecture

## Development Guidelines

### Adding New Primitives
1. Create component in `components/` directory
2. Use `class-variance-authority` for variants
3. Implement role-based theming
4. Add comprehensive TypeScript types
5. Export from `components/index.ts`
6. Re-export from `shared_components/index.ts`

### Design Token Usage
```tsx
// Import design tokens
import { colors, typography, spacing } from '../design_system/tokens';

// Use in TailwindCSS config
// Colors are automatically available as Tailwind classes
```

### Role Implementation
```tsx
// Role-specific compound variants
compoundVariants: [
  {
    variant: 'primary',
    role: 'app',
    class: 'bg-green-600 hover:bg-green-700'
  }
]
```

## Future Expansion

### Planned Primitives
- `Card` - Content containers
- `Modal` - Dialog overlays  
- `Badge` - Status indicators
- `Alert` - Notification messages
- `Avatar` - User profile images
- `Tooltip` - Contextual help

### Token Expansion
- Animation tokens
- Shadow variations
- Border variations
- Grid system tokens

## Best Practices

1. **Single Responsibility**: Each component serves one clear purpose
2. **Composition Over Inheritance**: Build complex components by composing primitives
3. **Role Awareness**: Always consider which user role will use the component
4. **Accessibility**: Test with screen readers and keyboard navigation
5. **Performance**: Use React.forwardRef and proper TypeScript for optimal renders
6. **Documentation**: Include comprehensive examples and prop descriptions

## Integration with Shared Components

The design system primitives are re-exported through `shared_components/index.ts` to provide a unified import interface. Complex business logic components in `shared_components/` use these primitives as building blocks while adding specific functionality like data fetching, state management, and business rules.