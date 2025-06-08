import React, { useState, ReactNode } from 'react';
import * as Popover from '@radix-ui/react-popover';
import { X } from 'lucide-react';

interface ContextualHelpProps {
  children: ReactNode;
  content: string | Record<string, string>;
  width?: string;
}

const ContextualHelp: React.FC<ContextualHelpProps> = ({
  children,
  content,
  width = 'w-80',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const renderContent = () => {
    if (typeof content === 'string') {
      return <p className="text-sm text-gray-700">{content}</p>;
    }

    return (
      <div className="space-y-3">
        {Object.entries(content).map(([key, value]) => (
          <div key={key}>
            <h4 className="text-sm font-medium text-gray-900">{key.charAt(0).toUpperCase() + key.slice(1)}</h4>
            <p className="text-sm text-gray-700 mt-1">{value}</p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <Popover.Root open={isOpen} onOpenChange={setIsOpen}>
      <Popover.Trigger asChild>
        <button 
          type="button"
          className="contextual-help-trigger inline-flex items-center justify-center" 
          aria-label="Show help"
        >
          {children}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className={`contextual-help-content shadow-md ${width} z-50`}
          sideOffset={5}
          align="center"
          side="bottom"
        >
          <div className="flex flex-col gap-2.5">
            {renderContent()}
          </div>
          <Popover.Close
            className="absolute top-3.5 right-3.5 inline-flex items-center justify-center rounded-full h-5 w-5 text-gray-500 hover:text-gray-900"
            aria-label="Close"
          >
            <X className="h-3 w-3" />
          </Popover.Close>
          <Popover.Arrow className="fill-cyan-50" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};

export default ContextualHelp;
