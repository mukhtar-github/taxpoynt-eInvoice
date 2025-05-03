import React from 'react';
import { TailwindExample } from '../components/examples/TailwindExample';

const UIDesignSystem: React.FC = () => {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-3xl font-heading font-semibold mb-4">UI/UX Design System</h1>
      
      <div className="mb-10 p-6 bg-background-alt rounded-lg">
        <h2 className="text-2xl font-heading font-semibold mb-4">Recommended Stack</h2>
        <p className="mb-4">
          Based on our UI/UX evaluation, we're implementing the following stack:
        </p>
        
        <ul className="list-disc pl-6 mb-6 space-y-2">
          <li className="text-text-primary">
            <strong>Iconography:</strong> Lucide React - lightweight SVG icons with consistent design
          </li>
          <li className="text-text-primary">
            <strong>Base Components:</strong> Native HTML with Tailwind CSS for better performance
          </li>
          <li className="text-text-primary">
            <strong>Component Library:</strong> Shadcn UI approach (copy-into-codebase components)
          </li>
          <li className="text-text-primary">
            <strong>Styling:</strong> Tailwind CSS with a custom typography scale for consistency
          </li>
        </ul>
        
        <p className="mb-4 text-text-secondary">
          This approach focuses on accessibility, performance optimization, and
          consistent design token management in the Tailwind configuration.
        </p>
      </div>
      
      <div className="mb-10">
        <h2 className="text-2xl font-heading font-semibold mb-4">Design Tokens</h2>
        
        <h3 className="text-xl font-heading font-semibold mb-2">Colors</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="flex flex-col">
            <div className="h-16 bg-primary rounded-md mb-2"></div>
            <span className="text-sm font-medium">primary</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-primary-dark rounded-md mb-2"></div>
            <span className="text-sm font-medium">primary-dark</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-primary-light rounded-md mb-2"></div>
            <span className="text-sm font-medium">primary-light</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-background rounded-md mb-2 border border-border"></div>
            <span className="text-sm font-medium">background</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-success rounded-md mb-2"></div>
            <span className="text-sm font-medium">success</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-error rounded-md mb-2"></div>
            <span className="text-sm font-medium">error</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-warning rounded-md mb-2"></div>
            <span className="text-sm font-medium">warning</span>
          </div>
          <div className="flex flex-col">
            <div className="h-16 bg-info rounded-md mb-2"></div>
            <span className="text-sm font-medium">info</span>
          </div>
        </div>
        
        <h3 className="text-xl font-heading font-semibold mb-2 mt-8">Typography</h3>
        <div className="space-y-4 mb-8">
          <div>
            <h1 className="font-heading">Heading 1 (h1)</h1>
            <p className="text-text-secondary text-sm mt-1">font-family: Inter, font-size: 1.875rem</p>
          </div>
          <div>
            <h2 className="font-heading">Heading 2 (h2)</h2>
            <p className="text-text-secondary text-sm mt-1">font-family: Inter, font-size: 1.5rem</p>
          </div>
          <div>
            <h3 className="font-heading">Heading 3 (h3)</h3>
            <p className="text-text-secondary text-sm mt-1">font-family: Inter, font-size: 1.25rem</p>
          </div>
          <div>
            <p className="font-body">Body text (p)</p>
            <p className="text-text-secondary text-sm mt-1">font-family: Source Sans Pro, font-size: 1rem</p>
          </div>
          <div>
            <p className="font-body text-sm">Small text</p>
            <p className="text-text-secondary text-sm mt-1">font-family: Source Sans Pro, font-size: 0.875rem</p>
          </div>
        </div>
      </div>
      
      <div className="mb-10">
        <h2 className="text-2xl font-heading font-semibold mb-4">Component Examples</h2>
        <div className="border border-border rounded-lg overflow-hidden">
          <TailwindExample />
        </div>
      </div>
    </div>
  );
};

export default UIDesignSystem; 