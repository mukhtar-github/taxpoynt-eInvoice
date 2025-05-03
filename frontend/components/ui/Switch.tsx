import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const switchVariants = cva(
  "peer h-[24px] w-[44px] cursor-pointer appearance-none rounded-full bg-border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[checked]:bg-primary",
  {
    variants: {
      size: {
        default: "h-[24px] w-[44px]",
        sm: "h-[20px] w-[36px]",
        lg: "h-[28px] w-[52px]",
      },
    },
    defaultVariants: {
      size: "default",
    },
  }
);

const thumbVariants = cva(
  "pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[checked]:translate-x-5",
  {
    variants: {
      size: {
        default: "h-5 w-5 data-[checked]:translate-x-5",
        sm: "h-4 w-4 data-[checked]:translate-x-4",
        lg: "h-6 w-6 data-[checked]:translate-x-6",
      },
    },
    defaultVariants: {
      size: "default",
    },
  }
);

export interface SwitchProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size' | 'type'>,
    VariantProps<typeof switchVariants> {
  onCheckedChange?: (checked: boolean) => void;
}

const Switch = forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, size, checked, onCheckedChange, ...props }, ref) => {
    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (onCheckedChange) {
        onCheckedChange(event.target.checked);
      }
    };

    return (
      <div className="relative inline-flex items-center">
        <input
          type="checkbox"
          className={switchVariants({ size, className })}
          ref={ref}
          checked={checked}
          onChange={handleChange}
          {...props}
          data-checked={checked ? "" : undefined}
        />
        <div 
          className={thumbVariants({ size })}
          data-checked={checked ? "" : undefined}
          style={{
            position: 'absolute',
            left: 2,
            top: '50%',
            transform: `translateY(-50%) ${checked ? 'translateX(20px)' : 'translateX(0)'}`,
            transition: 'transform 0.2s',
          }}
        />
      </div>
    );
  }
);

Switch.displayName = "Switch";

export { Switch };
