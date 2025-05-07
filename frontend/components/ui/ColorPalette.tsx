import React from 'react';
import { Card, CardHeader, CardContent } from './Card';
import { Typography } from './Typography';

/**
 * Color Palette Component
 * 
 * A component that displays the application's color palette
 * as specified in the core UI/UX requirements:
 * - Brand colors
 * - Success/Error/Warning/Info states
 * - Neutral tones
 */

interface ColorSwatchProps {
  name: string;
  color: string;
  textColor?: string;
  value?: string;
}

const ColorSwatch: React.FC<ColorSwatchProps> = ({ 
  name, 
  color, 
  textColor = 'text-text-primary',
  value
}) => (
  <div className="mb-4">
    <div 
      className={`h-16 rounded-md shadow-sm ${color} mb-2`} 
      style={{ borderWidth: '1px', borderColor: 'rgba(0,0,0,0.1)' }}
    />
    <div className="flex justify-between">
      <Typography.Text as="span" weight="medium" className={textColor}>
        {name}
      </Typography.Text>
      {value && (
        <Typography.Text as="span" variant="secondary" size="sm">
          {value}
        </Typography.Text>
      )}
    </div>
  </div>
);

/**
 * Section for grouping color swatches
 */
interface ColorSectionProps {
  title: string;
  children: React.ReactNode;
}

const ColorSection: React.FC<ColorSectionProps> = ({ title, children }) => (
  <div className="mb-8">
    <Typography.Heading level="h3" className="mb-4">{title}</Typography.Heading>
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {children}
    </div>
  </div>
);

/**
 * The main ColorPalette component
 */
export const ColorPalette: React.FC = () => {
  return (
    <Card className="w-full">
      <CardHeader title="Color Palette" subtitle="Core design system colors" />
      <CardContent>
        <Typography.Text className="mb-6">
          This palette represents the core colors used throughout the application, following the UI/UX requirements
          to establish a primary color palette with brand colors, status indicators, and neutral tones.
        </Typography.Text>
        
        {/* Brand Colors */}
        <ColorSection title="Brand Colors">
          <ColorSwatch 
            name="Primary" 
            color="bg-primary" 
            textColor="text-white" 
            value="var(--color-primary)"
          />
          <ColorSwatch 
            name="Primary Dark" 
            color="bg-primary-dark" 
            textColor="text-white" 
            value="var(--color-primary-dark)"
          />
          <ColorSwatch 
            name="Primary Light" 
            color="bg-primary-light" 
            value="var(--color-primary-light)"
          />
        </ColorSection>
        
        {/* Status Colors */}
        <ColorSection title="Status Colors">
          <ColorSwatch 
            name="Success" 
            color="bg-success" 
            textColor="text-white" 
            value="var(--color-success)"
          />
          <ColorSwatch 
            name="Error" 
            color="bg-error" 
            textColor="text-white" 
            value="var(--color-error)"
          />
          <ColorSwatch 
            name="Warning" 
            color="bg-warning" 
            value="var(--color-warning)"
          />
          <ColorSwatch 
            name="Info" 
            color="bg-info" 
            textColor="text-white" 
            value="var(--color-info)"
          />
          <ColorSwatch 
            name="Success Light" 
            color="bg-success-light" 
            value="var(--color-success-light)"
          />
          <ColorSwatch 
            name="Error Light" 
            color="bg-error-light" 
            value="var(--color-error-light)"
          />
          <ColorSwatch 
            name="Warning Light" 
            color="bg-warning-light" 
            value="var(--color-warning-light)"
          />
          <ColorSwatch 
            name="Info Light" 
            color="bg-info-light" 
            value="var(--color-info-light)"
          />
        </ColorSection>
        
        {/* Neutral Colors */}
        <ColorSection title="Neutral Colors">
          <ColorSwatch 
            name="Text Primary" 
            color="bg-text-primary" 
            textColor="text-white" 
            value="var(--color-text-primary)"
          />
          <ColorSwatch 
            name="Text Secondary" 
            color="bg-text-secondary" 
            textColor="text-white" 
            value="var(--color-text-secondary)"
          />
          <ColorSwatch 
            name="Text Muted" 
            color="bg-text-muted" 
            value="var(--color-text-muted)"
          />
          <ColorSwatch 
            name="Border" 
            color="bg-border" 
            value="var(--color-border)"
          />
          <ColorSwatch 
            name="Background" 
            color="bg-background" 
            value="var(--color-background)"
          />
          <ColorSwatch 
            name="Background Alt" 
            color="bg-background-alt" 
            value="var(--color-background-alt)"
          />
        </ColorSection>
      </CardContent>
    </Card>
  );
};

export default ColorPalette;
