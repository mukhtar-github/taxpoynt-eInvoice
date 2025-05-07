# Form Components Documentation

## Overview

This document provides comprehensive documentation for the form components that have been migrated from Chakra UI to Tailwind CSS as part of the Taxpoynt eInvoice UI modernization effort. These components are designed to be reusable, accessible, and consistent with the application's design system.

## Component Library

### Input

The `Input` component is a styled text input field with support for different states and variants.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'error'` | `'default'` | The visual style of the input |
| `size` | `'sm' \| 'default' \| 'lg'` | `'default'` | The size of the input |
| `error` | `boolean` | `false` | Whether the input is in an error state |
| `...rest` | `InputHTMLAttributes<HTMLInputElement>` | - | All standard input props |

#### Usage

```tsx
import { Input } from '../components/ui/Input';

// Basic usage
<Input placeholder="Enter your name" />

// With error state
<Input 
  placeholder="Email" 
  type="email" 
  error={true} 
/>

// With different sizes
<Input size="sm" placeholder="Small input" />
<Input size="default" placeholder="Default input" />
<Input size="lg" placeholder="Large input" />
```

### Select

The `Select` component is a styled dropdown select field with support for different states and variants.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'error'` | `'default'` | The visual style of the select |
| `selectSize` | `'sm' \| 'default' \| 'lg'` | `'default'` | The size of the select |
| `error` | `boolean` | `false` | Whether the select is in an error state |
| `...rest` | `SelectHTMLAttributes<HTMLSelectElement>` | - | All standard select props |

#### Usage

```tsx
import { Select } from '../components/ui/Select';

// Basic usage
<Select>
  <option value="">Select an option</option>
  <option value="option1">Option 1</option>
  <option value="option2">Option 2</option>
</Select>

// With error state
<Select error={true}>
  <option value="">Please select an option</option>
  <option value="option1">Option 1</option>
</Select>

// With different sizes
<Select selectSize="sm">
  <option value="">Small select</option>
</Select>
```

### Textarea

The `Textarea` component is a styled multi-line text input field.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'error'` | `'default'` | The visual style of the textarea |
| `error` | `boolean` | `false` | Whether the textarea is in an error state |
| `...rest` | `TextareaHTMLAttributes<HTMLTextAreaElement>` | - | All standard textarea props |

#### Usage

```tsx
import { Textarea } from '../components/ui/Textarea';

// Basic usage
<Textarea placeholder="Enter your message" rows={4} />

// With error state
<Textarea 
  placeholder="Enter your message" 
  rows={4} 
  error={true} 
/>
```

### Checkbox

The `Checkbox` component is a styled checkbox input with support for labels and descriptions.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Text label for the checkbox |
| `description` | `string` | - | Additional description text |
| `error` | `boolean` | `false` | Whether the checkbox is in an error state |
| `errorMessage` | `string` | - | Error message to display |
| `...rest` | `InputHTMLAttributes<HTMLInputElement>` | - | All standard checkbox input props |

#### Usage

```tsx
import { Checkbox } from '../components/ui/Checkbox';

// Basic usage
<Checkbox id="terms" name="terms" />

// With label and description
<Checkbox 
  id="terms" 
  name="terms"
  label="I accept the terms and conditions" 
  description="By checking this box, you agree to our Terms of Service and Privacy Policy" 
/>

// With error state
<Checkbox 
  id="terms" 
  name="terms"
  label="I accept the terms and conditions" 
  error={true}
  errorMessage="You must accept the terms to continue" 
/>
```

### FormField

The `FormField` component is a wrapper component that provides consistent labeling, help text, and error handling for form inputs.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Text label for the field |
| `htmlFor` | `string` | - | ID of the input element this label is for |
| `helpText` | `string` | - | Additional help text displayed below the input |
| `error` | `boolean` | `false` | Whether the field is in an error state |
| `errorMessage` | `string` | - | Error message to display when in error state |
| `required` | `boolean` | `false` | Whether the field is required |
| `children` | `ReactNode` | - | The form input to be wrapped |
| `className` | `string` | - | Additional CSS classes |

#### Usage

```tsx
import { FormField } from '../components/ui/FormField';
import { Input } from '../components/ui/Input';

// Basic usage
<FormField 
  label="Username" 
  htmlFor="username"
>
  <Input id="username" name="username" />
</FormField>

// With help text
<FormField 
  label="Email" 
  htmlFor="email"
  helpText="We'll never share your email with anyone else."
>
  <Input id="email" name="email" type="email" />
</FormField>

// With error state
<FormField 
  label="Password" 
  htmlFor="password"
  required
  error={true}
  errorMessage="Password must be at least 8 characters long"
>
  <Input id="password" name="password" type="password" error={true} />
</FormField>
```

## Complete Form Example

Below is an example of a complete form using all the components together:

```tsx
import React, { useState } from 'react';
import { FormField } from '../components/ui/FormField';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Textarea } from '../components/ui/Textarea';
import { Checkbox } from '../components/ui/Checkbox';
import { Button } from '../components/ui/Button';

const ExampleForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    category: '',
    message: '',
    acceptTerms: false
  });
  
  const [errors, setErrors] = useState({});
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // Form validation and submission logic
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <FormField 
        label="Full Name" 
        htmlFor="name"
        required
        error={!!errors.name}
        errorMessage={errors.name}
      >
        <Input
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          error={!!errors.name}
        />
      </FormField>
      
      <FormField 
        label="Email Address" 
        htmlFor="email"
        required
        error={!!errors.email}
        errorMessage={errors.email}
      >
        <Input
          id="email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          error={!!errors.email}
        />
      </FormField>
      
      <FormField 
        label="Category" 
        htmlFor="category"
        error={!!errors.category}
        errorMessage={errors.category}
      >
        <Select
          id="category"
          name="category"
          value={formData.category}
          onChange={handleChange}
          error={!!errors.category}
        >
          <option value="">Select a category</option>
          <option value="support">Support</option>
          <option value="feedback">Feedback</option>
          <option value="bug">Bug Report</option>
        </Select>
      </FormField>
      
      <FormField 
        label="Message" 
        htmlFor="message"
        required
        error={!!errors.message}
        errorMessage={errors.message}
      >
        <Textarea
          id="message"
          name="message"
          value={formData.message}
          onChange={handleChange}
          rows={4}
          error={!!errors.message}
        />
      </FormField>
      
      <FormField 
        error={!!errors.acceptTerms}
        errorMessage={errors.acceptTerms}
      >
        <Checkbox
          id="acceptTerms"
          name="acceptTerms"
          checked={formData.acceptTerms}
          onChange={handleChange}
          label="I accept the terms and conditions"
          error={!!errors.acceptTerms}
        />
      </FormField>
      
      <Button type="submit">Submit Form</Button>
    </form>
  );
};
```

## Accessibility Considerations

All form components are designed with accessibility in mind:

- Proper labeling with `htmlFor` attributes matching input IDs
- ARIA attributes where appropriate
- Keyboard navigation support
- Focus states that are visible and distinguishable
- Error states that are communicated visually and via screen readers
- Color contrast that meets WCAG 2.1 AA standards

## Styling and Customization

These components use Tailwind CSS classes and the `class-variance-authority` (CVA) package for variant management. To customize the appearance:

1. For minor adjustments, pass a `className` prop to override specific styles
2. For component-wide changes, modify the variant definitions in the component source
3. For system-wide changes, update the Tailwind configuration

Example of customizing a component:

```tsx
// Minor adjustment
<Input className="border-blue-500" />

// Component-wide change (in the component file)
const inputVariants = cva(
  "flex h-10 w-full rounded-md border...",
  {
    variants: {
      variant: {
        default: "",
        primary: "border-primary",
        // Add a new variant
        custom: "border-purple-500 bg-purple-50",
      },
      // ...
    },
  }
);

// Usage
<Input variant="custom" />
```

## Best Practices

1. **Always use FormField for consistent layout**: Wrap every form input in a `FormField` component to ensure consistent spacing, labeling, and error handling.

2. **Propagate error states**: When a field has an error, set the `error` prop on both the `FormField` and the input component.

3. **Use proper HTML5 input types**: Use appropriate types like `email`, `number`, `tel`, etc. for better mobile keyboard support and built-in validation.

4. **Provide meaningful error messages**: Error messages should be clear about what went wrong and how to fix it.

5. **Use required prop and visual indicator**: For required fields, set the `required` prop to true on the `FormField` component to show the visual indicator (asterisk).

## Migration Notes

These components replace the following Chakra UI components:

- `Input` → Chakra UI's `Input`
- `Select` → Chakra UI's `Select`
- `Textarea` → Chakra UI's `Textarea`
- `Checkbox` → Chakra UI's `Checkbox`
- `FormField` → Chakra UI's `FormControl`, `FormLabel`, `FormHelperText`, and `FormErrorMessage`

When migrating existing forms, follow these steps:

1. Replace Chakra UI imports with the new component imports
2. Wrap inputs in `FormField` components
3. Update props according to the new component API
4. Replace Chakra-specific props with their Tailwind equivalents

## Conclusion

These form components provide a solid foundation for building accessible, consistent, and visually appealing forms in the Taxpoynt eInvoice application. They are designed to be easy to use and maintain, while providing all the functionality needed for complex forms.
