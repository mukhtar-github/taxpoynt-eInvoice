import React from 'react';
import { Button } from '../ui/Button';
import { Home, Settings, ChevronRight, Bell, Mail, User, Calendar, Search } from 'lucide-react';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from '../ui/Card';
import { IconButton } from '../ui/IconButton';

export const TailwindExample: React.FC = () => {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-heading font-semibold mb-6">Tailwind UI Components</h1>
      
      {/* Buttons Section */}
      <section className="mb-10">
        <h2 className="text-2xl font-heading font-semibold mb-4">Buttons</h2>
        <div className="flex flex-wrap gap-4">
          <Button>Default Button</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="link">Link</Button>
        </div>
        
        <h3 className="text-xl font-heading font-semibold mt-6 mb-4">With Icons</h3>
        <div className="flex flex-wrap gap-4">
          <Button className="flex items-center gap-2">
            <Home size={16} className="shrink-0" aria-hidden="true" />
            Home
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Settings size={16} className="shrink-0" aria-hidden="true" />
            Settings
          </Button>
          <Button variant="secondary" className="flex items-center gap-2">
            View Details
            <ChevronRight size={16} className="shrink-0" aria-hidden="true" />
          </Button>
        </div>
        
        <h3 className="text-xl font-heading font-semibold mt-6 mb-4">IconButton Component</h3>
        <div className="flex flex-wrap gap-4">
          <IconButton icon={Home} variant="default">Home</IconButton>
          <IconButton icon={Mail} variant="outline">Messages</IconButton>
          <IconButton icon={ChevronRight} iconPosition="right" variant="secondary">Next</IconButton>
          <IconButton icon={User} variant="ghost">Profile</IconButton>
          <IconButton icon={Calendar} iconSize={20} variant="default">Schedule</IconButton>
          <IconButton icon={Search} size="sm">Search</IconButton>
        </div>
        
        <h3 className="text-xl font-heading font-semibold mt-6 mb-4">Sizes</h3>
        <div className="flex flex-wrap items-center gap-4">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
          <Button size="icon" aria-label="Notifications">
            <Bell size={18} aria-hidden="true" />
          </Button>
        </div>
      </section>
      
      {/* Cards Section */}
      <section className="mb-10">
        <h2 className="text-2xl font-heading font-semibold mb-4">Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Card */}
          <Card>
            <CardHeader>
              <CardTitle>Card Title</CardTitle>
              <CardDescription>This is a basic card example with description.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary">
                This is the main content area of the card. You can put any content here.
              </p>
            </CardContent>
            <CardFooter>
              <Button variant="outline" size="sm">Cancel</Button>
              <Button size="sm" className="ml-2">Submit</Button>
            </CardFooter>
          </Card>
          
          {/* Compact Card */}
          <Card variant="compact">
            <CardHeader>
              <CardTitle>Compact Card</CardTitle>
              <CardDescription>This card uses less padding.</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary">
                This is a compact card with less internal padding.
              </p>
            </CardContent>
            <CardFooter>
              <Button variant="link" size="sm" className="ml-auto">Learn more</Button>
            </CardFooter>
          </Card>
        </div>
      </section>
    </div>
  );
}; 