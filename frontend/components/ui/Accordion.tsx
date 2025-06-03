import React, { createContext, useContext, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';

// Context for accordion state management
const AccordionContext = createContext<{
  expanded: Record<string, boolean>;
  toggle: (value: string) => void;
  type: 'single' | 'multiple';
}>({
  expanded: {},
  toggle: () => {},
  type: 'single',
});

interface AccordionProps {
  children: React.ReactNode;
  type?: 'single' | 'multiple';
  defaultValue?: string | string[];
  className?: string;
}

export const Accordion: React.FC<AccordionProps> = ({
  children,
  type = 'single',
  defaultValue = [],
  className,
}) => {
  // Initialize state based on type and defaultValue
  const initialState = Array.isArray(defaultValue)
    ? defaultValue.reduce((acc, val) => ({ ...acc, [val]: true }), {})
    : { [defaultValue as string]: true };

  const [expanded, setExpanded] = useState<Record<string, boolean>>(initialState);

  // Toggle accordion item
  const toggle = (value: string) => {
    setExpanded((prev) => {
      if (type === 'single') {
        return { [value]: !prev[value] };
      } else {
        return { ...prev, [value]: !prev[value] };
      }
    });
  };

  return (
    <AccordionContext.Provider value={{ expanded, toggle, type }}>
      <div className={cn('divide-y divide-gray-200', className)}>{children}</div>
    </AccordionContext.Provider>
  );
};

interface AccordionItemProps {
  children: React.ReactNode;
  value: string;
  className?: string;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  children,
  value,
  className,
}) => {
  return (
    <div className={cn('py-2', className)} data-state-value={value}>
      {children}
    </div>
  );
};

interface AccordionTriggerProps {
  children: React.ReactNode;
  className?: string;
}

export const AccordionTrigger: React.FC<AccordionTriggerProps> = ({
  children,
  className,
}) => {
  const { expanded, toggle, type } = useContext(AccordionContext);
  const item = React.useContext(AccordionItemContext);

  if (!item) {
    throw new Error('AccordionTrigger must be used within an AccordionItem');
  }

  const isExpanded = expanded[item.value] || false;

  return (
    <button
      className={cn(
        'flex w-full items-center justify-between py-2 font-medium text-left text-gray-900',
        className
      )}
      onClick={() => toggle(item.value)}
      aria-expanded={isExpanded}
    >
      {children}
      <ChevronDown
        className={cn(
          'h-4 w-4 transition-transform duration-200',
          isExpanded ? 'transform rotate-180' : ''
        )}
      />
    </button>
  );
};

interface AccordionContentProps {
  children: React.ReactNode;
  className?: string;
}

// Context for keeping track of the parent AccordionItem
const AccordionItemContext = createContext<{ value: string } | null>(null);

export const AccordionContent: React.FC<AccordionContentProps> = ({
  children,
  className,
}) => {
  const { expanded } = useContext(AccordionContext);
  const item = useContext(AccordionItemContext);

  if (!item) {
    throw new Error('AccordionContent must be used within an AccordionItem');
  }

  const isExpanded = expanded[item.value] || false;

  if (!isExpanded) {
    return null;
  }

  return <div className={cn('pt-2 pb-4', className)}>{children}</div>;
};

// Override the AccordionItem component to provide context
export const AccordionItem2: React.FC<AccordionItemProps> = (props) => {
  return (
    <AccordionItemContext.Provider value={{ value: props.value }}>
      <AccordionItem {...props} />
    </AccordionItemContext.Provider>
  );
};

// Replace the original AccordionItem with the context-providing version
Object.assign(AccordionItem, AccordionItem2);

// Export all components
export default Accordion;
