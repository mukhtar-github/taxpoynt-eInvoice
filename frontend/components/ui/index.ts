/**
 * UI Components - Week 3 Enhanced Export Index
 * 
 * Provides clean imports for all UI components including Week 3 enhancements.
 */

// Enhanced Form Components (Week 3)
export { 
  EnhancedFormField, 
  EnhancedInput, 
  EnhancedTextarea 
} from './EnhancedFormField';

export type { 
  ValidationResult,
  EnhancedFormFieldProps,
  EnhancedInputProps,
  EnhancedTextareaProps 
} from './EnhancedFormField';

// Enhanced Loading Components (Week 3)
export { 
  LoadingSpinner,
  LoadingButton,
  Skeleton,
  IntegrationCardSkeleton,
  MetricsCardSkeleton,
  TableSkeleton,
  ProgressBar,
  CircularProgress,
  PulseIndicator,
  LoadingOverlay,
  AnimatedState
} from './LoadingStates';

export type {
  LoadingSpinnerProps,
  LoadingButtonProps,
  SkeletonProps,
  ProgressBarProps,
  CircularProgressProps,
  LoadingOverlayProps,
  AnimatedStateProps
} from './LoadingStates';

// Core UI Components (Existing)
export { FormField } from './FormField';
export { Button } from './Button';
export { Card, CardContent, CardHeader, CardTitle } from './Card';
export { Badge } from './Badge';
export { Typography } from './Typography';

// Additional UI Components
export { Input } from './Input';
export { Textarea } from './Textarea';
export { Label } from './Label';
export { Container } from './Container';
export { Divider } from './Divider';
export { Spinner } from './Spinner';
export { useToast } from './Toast';

// Text/Heading Components
export { Heading } from './Heading';
export { Text } from './Text';

// Type exports for core components
export type { FormFieldProps } from './FormField';
export type { ButtonProps } from './Button';
export type { InputProps } from './Input';

/**
 * Recommended Usage:
 * 
 * // Week 3 Enhanced Components (Preferred)
 * import { 
 *   EnhancedInput, 
 *   LoadingButton, 
 *   ProgressBar 
 * } from '@/components/ui';
 * 
 * // Legacy Components (Backward Compatibility)
 * import { 
 *   FormField, 
 *   Button 
 * } from '@/components/ui';
 */