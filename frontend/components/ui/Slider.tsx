import React, { forwardRef } from 'react';
import * as SliderPrimitive from '@radix-ui/react-slider';
import { cn } from '../../utils/cn';
import { SetStateAction } from 'react';

interface SliderProps {
  /**
   * Optional ID for the slider element
   */
  id?: string;
  /**
   * Optional label for accessibility
   */
  label?: string;
  /**
   * Optional classname for the component wrapper
   */
  className?: string;
  /**
   * Optional classname for the thumb
   */
  thumbClassName?: string;
  /**
   * Value of the slider (array of numbers)
   */
  value?: number[];
  /**
   * Callback fired when the value changes
   */
  onValueChange?: (value: SetStateAction<number>[]) => void;
  /**
   * Optional classname for the track
   */
  trackClassName?: string;
  /**
   * Optional classname for the range
   */
  rangeClassName?: string;
  /**
   * Minimum value of the slider
   */
  min?: number;
  /**
   * Maximum value of the slider
   */
  max?: number;
  /**
   * Step value of the slider
   */
  step?: number;
  /**
   * Default value of the slider
   */
  defaultValue?: number[];
  /**
   * Whether the slider is disabled
   */
  disabled?: boolean;
  /**
   * Orientation of the slider
   */
  orientation?: 'horizontal' | 'vertical';
  /**
   * Direction of the slider
   */
  dir?: 'ltr' | 'rtl';
  /**
   * Whether the slider is inverted
   */
  inverted?: boolean;
  /**
   * Name of the slider
   */
  name?: string;
}

/**
 * Slider component based on Radix UI Slider
 * 
 * Uses the ShadcnUI pattern and TaxPoynt styling system
 */
const Slider = forwardRef<React.ElementRef<typeof SliderPrimitive.Root>, SliderProps>(
  ({
    className,
    label,
    thumbClassName,
    trackClassName,
    rangeClassName,
    id,
    min = 0,
    max = 100,
    step = 1,
    value,
    defaultValue,
    onValueChange,
    disabled,
    orientation,
    dir,
    inverted,
    name,
    ...props
  }, ref) => (
    <div id={id} className={cn('relative flex w-full touch-none select-none items-center', className)}>
      {label && (
        <label className="text-sm text-gray-500 mb-1 block">{label}</label>
      )}
      <SliderPrimitive.Root
        ref={ref}
        min={min}
        max={max}
        step={step}
        value={value}
        defaultValue={defaultValue}
        onValueChange={onValueChange}
        disabled={disabled}
        orientation={orientation}
        dir={dir}
        inverted={inverted}
        name={name}
        className="relative flex w-full touch-none select-none items-center"
        {...props}
      >
        <SliderPrimitive.Track
          className={cn(
            "relative h-1.5 w-full grow overflow-hidden rounded-full bg-gray-200",
            trackClassName
          )}
        >
          <SliderPrimitive.Range
            className={cn(
              "absolute h-full bg-primary",
              rangeClassName
            )}
          />
        </SliderPrimitive.Track>
        {Array.isArray(value) && value.map((_, index) => (
          <SliderPrimitive.Thumb
            key={index}
            className={cn(
              "block h-4 w-4 rounded-full border border-primary/50 bg-background shadow transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
              thumbClassName
            )}
          />
        ))}
      </SliderPrimitive.Root>
    </div>
  )
);

Slider.displayName = "Slider";

export { Slider };
