# MetricCard Migration Guide

## Overview

This guide helps you migrate from the old `MetricCard` component to the new `EnhancedMetricCard` with animated counters and improved mobile responsiveness.

## What's Changed

### Old MetricCard (Card.tsx)
```typescript
import { MetricCard } from '../ui/Card';

<MetricCard 
  title="Total Invoices"
  value="2,547"
  change={{
    value: "12.5%",
    type: "increase"
  }}
/>
```

### New EnhancedMetricCard
```typescript
import { EnhancedMetricCard, MetricCardGrid } from '../dashboard/EnhancedMetricCard';

<EnhancedMetricCard 
  title="Total Invoices"
  value={2547}
  previousValue={2270}
  icon={<FileText className="w-6 h-6" />}
  countUp={true}
  animationDuration={2000}
/>
```

## Key Differences

| Feature | Old MetricCard | New EnhancedMetricCard |
|---------|----------------|------------------------|
| **Value Type** | `string \| number` | `number` (required) |
| **Change Calculation** | Manual `change` object | Auto-calculated from `previousValue` |
| **Animation** | None | Animated counter with `countUp` |
| **Icons** | Optional ReactNode | Optional ReactNode with hover effects |
| **Mobile Support** | Basic | Touch-friendly, responsive breakpoints |
| **Loading States** | None | Built-in shimmer loading |
| **Formatting** | Manual string formatting | `prefix`, `suffix`, `formatValue` options |

## Migration Steps

### Step 1: Update Imports

**Before:**
```typescript
import { MetricCard } from '../ui/Card';
```

**After:**
```typescript
import { EnhancedMetricCard, MetricCardGrid } from '../dashboard/EnhancedMetricCard';
import { FileText, TrendingUp, DollarSign } from 'lucide-react';
```

### Step 2: Convert Data Format

**Before:**
```typescript
const metric = {
  title: 'Total Revenue',
  value: '₦4.5M',
  change: {
    value: '15.3%',
    type: 'increase'
  }
};
```

**After:**
```typescript
const metric = {
  title: 'Total Revenue',
  value: 4500000,
  previousValue: 3900000,
  prefix: '₦',
  icon: <DollarSign className="w-6 h-6" />,
  formatValue: (value: number) => `${(value / 1000000).toFixed(1)}M`,
  countUp: true
};
```

### Step 3: Update Component Usage

**Before:**
```typescript
<div className="grid grid-cols-4 gap-6">
  <MetricCard 
    title={metric.title}
    value={metric.value}
    change={metric.change}
  />
</div>
```

**After:**
```typescript
<MetricCardGrid>
  <EnhancedMetricCard 
    title={metric.title}
    value={metric.value}
    previousValue={metric.previousValue}
    prefix={metric.prefix}
    icon={metric.icon}
    formatValue={metric.formatValue}
    countUp={metric.countUp}
    animationDuration={2000}
  />
</MetricCardGrid>
```

## Migration Examples

### Example 1: Simple Counter
```typescript
// Old
<MetricCard 
  title="Total Invoices"
  value="1,245"
/>

// New
<EnhancedMetricCard 
  title="Total Invoices"
  value={1245}
  countUp={true}
  icon={<FileText className="w-6 h-6" />}
/>
```

### Example 2: Percentage Values
```typescript
// Old
<MetricCard 
  title="Success Rate"
  value="94.6%"
  change={{ value: "2.1%", type: "increase" }}
/>

// New
<EnhancedMetricCard 
  title="Success Rate"
  value={94.6}
  previousValue={92.5}
  suffix="%"
  precision={1}
  icon={<TrendingUp className="w-6 h-6" />}
  countUp={true}
/>
```

### Example 3: Currency Values
```typescript
// Old
<MetricCard 
  title="Monthly Revenue"
  value="₦2.4M"
  change={{ value: "8.3%", type: "increase" }}
/>

// New
<EnhancedMetricCard 
  title="Monthly Revenue"
  value={2400000}
  previousValue={2216000}
  prefix="₦"
  icon={<DollarSign className="w-6 h-6" />}
  formatValue={(value) => `${(value / 1000000).toFixed(1)}M`}
  countUp={true}
/>
```

## Files to Update

### High Priority (Active Usage)
1. ✅ `components/dashboard/MetricsDashboard.tsx` - **UPDATED**
2. `pages/dashboard/index.tsx` - Needs conversion from custom HTML to components
3. `pages/dashboard/metrics.tsx` - Check for MetricCard usage

### Medium Priority (Remove Imports)
1. `pages/dashboard/index.tsx` - Remove unused MetricCard import
2. `components/ui/index.ts` - Update exports if needed
3. `pages/ui-system.tsx` - Update showcase page

### Low Priority (Documentation/Examples)
1. `components/dashboard/EnhancedDashboardExample.tsx` - Already uses new components
2. Any Storybook stories or documentation files

## Benefits of Migration

### 🎨 **Visual Enhancements**
- Smooth animated counters
- Micro-interactions and hover effects
- Professional loading states
- Better visual hierarchy

### 📱 **Mobile Improvements**
- Touch-friendly interactions
- Responsive typography
- Optimized spacing for small screens
- Mobile-first design approach

### 🚀 **Performance**
- Intersection Observer for scroll-triggered animations
- RequestAnimationFrame for smooth animations
- Efficient re-rendering with React hooks

### 🔧 **Developer Experience**
- TypeScript support with proper typing
- Flexible formatting options
- Easy customization and theming
- Consistent API across components

## Testing Migration

After migrating, verify:

1. **Functionality**: All metrics display correctly
2. **Animations**: Counters animate smoothly
3. **Responsiveness**: Components work well on mobile
4. **Performance**: No lag or memory leaks
5. **Accessibility**: Screen readers work properly

## Troubleshooting

### Common Issues

**Issue**: "Cannot read property of undefined"
**Solution**: Ensure `value` is a number, not a string

**Issue**: Animation not working
**Solution**: Check that `countUp={true}` and `value` is numeric

**Issue**: Styling looks different
**Solution**: Use `MetricCardGrid` wrapper for consistent layout

**Issue**: Mobile layout broken
**Solution**: Remove custom grid classes, let `MetricCardGrid` handle responsive layout

## Support

If you encounter issues during migration:

1. Check the `EnhancedDashboardExample.tsx` for working examples
2. Ensure all required props are provided
3. Verify imports are correct
4. Test on different screen sizes

The migration provides significant UX improvements and better maintainability. Take time to test thoroughly after each file migration.