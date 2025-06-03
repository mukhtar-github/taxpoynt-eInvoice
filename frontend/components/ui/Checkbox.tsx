import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { Check } from 'lucide-react';

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
  error?: boolean;
  errorMessage?: string;
  /**
   * Callback fired when the checkbox state changes
   */
  onCheckedChange?: (checked: boolean) => void;
  /**
   * Current checked state of the checkbox
   */
  checked?: boolean;
}

const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, error, errorMessage, disabled, checked, onCheckedChange, onChange, ...props }, ref) => {
    return (
      <div className="flex items-start space-x-2">
        <div className="relative flex items-center">
          <input
            type="checkbox"
            className={cn(
              "peer h-4 w-4 appearance-none rounded border border-border bg-background text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
              error && "border-error focus:ring-error",
              className
            )}
            ref={ref}
            disabled={disabled}
            checked={checked}
            onChange={(e) => {
              onChange?.(e);
              onCheckedChange?.(e.target.checked);
            }}
            {...props}
          />
          <Check 
            className="absolute h-3 w-3 text-current opacity-0 peer-checked:opacity-100 text-primary pointer-events-none" 
            strokeWidth={3}
          />
        </div>
        
        {(label || description) && (
          <div className="grid gap-1">
            {label && (
              <label
                htmlFor={props.id}
                className={cn(
                  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
                  error && "text-error"
                )}
              >
                {label}
              </label>
            )}
            {description && (
              <p className="text-sm text-text-muted">{description}</p>
            )}
            {error && errorMessage && (
              <p className="text-sm text-error">{errorMessage}</p>
            )}
          </div>
        )}
      </div>
    );
  }
);

Checkbox.displayName = "Checkbox";

export { Checkbox };

export default Checkbox;
