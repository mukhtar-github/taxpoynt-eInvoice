import React, { useState } from 'react';
import { Typography } from '../ui/Typography';
import { cn } from '../../utils/cn';

interface JsonEditorProps {
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  height?: string;
}

export const JsonEditor: React.FC<JsonEditorProps> = ({ 
  value, 
  onChange,
  height = '200px'
}) => {
  const [error, setError] = useState<string | null>(null);
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    try {
      const parsedValue = JSON.parse(e.target.value);
      onChange(parsedValue);
      setError(null);
    } catch (err) {
      setError('Invalid JSON format');
      // Don't update the parent value when there's an error
    }
  };
  
  return (
    <div className="relative w-full">
      <textarea
        value={JSON.stringify(value, null, 2)}
        onChange={handleChange}
        className={cn(
          "w-full font-mono p-3 rounded-md resize-vertical border border-border focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background",
          error && "border-error focus:ring-error"
        )}
        style={{ height }}
      />
      
      {error && (
        <Typography.Text variant="error" size="sm" className="mt-1">
          {error}
        </Typography.Text>
      )}
    </div>
  );
}; 