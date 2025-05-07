# Component Migration Guide

## Overview

This document outlines the ongoing migration from Chakra UI components to our new Tailwind CSS and Shadcn-inspired components. The migration is being implemented incrementally to ensure minimal disruption to the application while improving performance and maintainability.

## Current Status

As of May 2025, the Taxpoynt eInvoice frontend is in a transition period where both old (Chakra UI) and new (Tailwind CSS) components exist side by side. New features are being developed with the new component system, while existing features are gradually being migrated.

**Latest Update (May 7, 2025)**: We have completed the migration of several core components including Typography, Grid system, Card components, and ColorPalette. Additionally, we've migrated the MetricsDashboard and Odoo IRN Management pages to use the new Tailwind CSS components.

## Migration Strategy

### Phase 1: Parallel Implementation (Current)
- New components are created alongside existing ones
- New features use the new component system
- Legacy components remain functional

### Phase 2: Gradual Replacement (Q3 2025)
- Systematically replace old components with new equivalents
- Update existing pages to use new components
- Maintain backward compatibility where needed

### Phase 3: Complete Migration (Q4 2025)
- Remove all legacy Chakra UI components
- Complete the transition to Tailwind CSS
- Optimize bundle size and performance

## Pages Migrated

The following pages have been migrated to use the new component system:
- MetricsDashboard
- Odoo IRN Management

## Component Mapping

Below is a mapping between old components and their new equivalents:

| Old Component (Chakra UI) | New Component (Tailwind CSS) | Status |
|---------------------------|------------------------------|--------|
| `IntegrationStatusCard.tsx` | `IntegrationStatus.tsx` | Migrated |
| `TransactionMetricsCard.tsx` | `TransactionMetrics.tsx` | Migrated |
| `Text, Heading` | `Typography.tsx` | Migrated |
| `Badge` | `Badge.tsx` | Migrated |
| ChakraButton | `Button.tsx` | Migrated |
| ChakraCard | `Card.tsx` | Migrated |
| ChakraProgress | `Progress.tsx` | Migrated |
| ChakraTable | `Table.tsx` | Migrated |
| MobileNav | `MobileNav.tsx` | Migrated |
| N/A (New) | `ColorPalette.tsx` | Completed |

## Recently Added Components

### Typography System

A new Typography system has been implemented with the following components:

- `Typography.Heading` - For heading elements (h1-h6) using the Inter font
- `Typography.Text` - For paragraph and text elements using Source Sans Pro font
- `Typography.Label` - For form labels and other labeling elements

This provides consistent typography throughout the application and replaces the various Chakra UI text components.

### Color Palette System

A Color Palette component and corresponding Tailwind CSS classes have been added to standardize our color system:

- Brand colors (primary, primary-dark, primary-light)
- Status colors (success, error, warning, info, and their light variants)
- Neutral colors (background, text-primary, text-secondary, etc.)

### Grid System

A responsive 12-column grid system has been implemented with these components:

- `Container` - Main container with optional max width
- `Row` - Row container with configurable gap
- `Col` - Column with configurable span and responsive breakpoints

## Key Differences

### Styling Approach
- **Old**: Chakra UI uses its own styling system with theme providers
- **New**: Tailwind CSS uses utility classes directly in JSX

### Component Architecture
- **Old**: High-level abstracted components with many built-in features
- **New**: Composable, lower-level components that can be combined

### Bundle Size
- **Old**: Larger bundle size due to comprehensive component library
- **New**: Smaller bundle with JIT compilation and tree-shaking

## Dashboard Components Transition

The monitoring dashboard exemplifies our migration approach:

### Integration Status Components

#### Old: `IntegrationStatusCard.tsx`
- Uses Chakra UI components (`Box`, `Flex`, etc.)
- Focuses on a single integration status
- Limited customization options
- Uses color schemes from Chakra theme

#### New: `IntegrationStatus.tsx`
- Uses Tailwind CSS for styling
- Displays multiple integrations in a comprehensive view
- Enhanced features (response time, detailed status, error handling)
- Follows our new design system
- Better performance with lower bundle size

### Transaction Metrics Components

#### Old: `TransactionMetricsCard.tsx`
- Simple metric display with Chakra UI
- Basic icon and count presentation
- Limited to displaying a single metric

#### New: `TransactionMetrics.tsx`
- Comprehensive metrics dashboard with charts
- Tabbed interface for time period selection
- Detailed breakdowns and trends
- Interactive elements and better accessibility

## How to Migrate Components

When migrating a component from the old system to the new:

1. Create a new component using Tailwind CSS classes
2. Replicate all existing functionality
3. Add new features and improvements
4. Use composable UI components from the `/components/ui` directory
5. Test thoroughly for visual and functional regressions
6. Update all imports in consumer components
7. Add documentation for any API changes

## Examples

### Button Migration Example

**Old (Chakra UI):**
```tsx
import { Button } from '@chakra-ui/react';

<Button colorScheme="blue" size="md">
  Click Me
</Button>
```

**New (Tailwind CSS):**
```tsx
import { Button } from '../ui/Button';

<Button variant="primary" size="md">
  Click Me
</Button>
```

### Card Migration Example

**Old (Chakra UI):**
```tsx
import { Box, Heading, Text } from '@chakra-ui/react';

<Box p={5} shadow="md" borderWidth="1px">
  <Heading fontSize="xl">{title}</Heading>
  <Text mt={4}>{description}</Text>
</Box>
```

**New (Tailwind CSS):**
```tsx
import { Card, CardHeader, CardContent } from '../ui/Card';

<Card>
  <CardHeader title={title} />
  <CardContent>
    <p className="mt-4">{description}</p>
  </CardContent>
</Card>
```

## Best Practices

1. **Don't mix systems** - Avoid using Chakra UI and Tailwind CSS in the same component
2. **Complete component migration** - Migrate entire components rather than partial elements
3. **Update tests** - Ensure tests are updated to reflect new component structure
4. **Document API changes** - Note any props or behavior changes in component documentation
5. **Performance testing** - Verify that new components maintain or improve performance

## Support and Questions

For questions about the migration process, please contact the Frontend Team Lead or refer to the design system documentation in `/frontend/docs/UI_STACK.md`.
