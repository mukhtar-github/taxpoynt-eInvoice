import React from 'react';
import { Container } from '../components/ui/Grid';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Typography } from '../components/ui/Typography';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Textarea } from '../components/ui/Textarea';
import { Checkbox } from '../components/ui/Checkbox';
import { FormField } from '../components/ui/FormField';
// SampleForm removed due to TypeScript errors
import { Button } from '../components/ui/Button';

/**
 * Form Examples Page
 * 
 * This page demonstrates the various form components that have been migrated
 * from Chakra UI to Tailwind CSS, showcasing their appearance and functionality.
 */
const FormExamplesPage: React.FC = () => {
  return (
    <Container>
      <div className="py-8">
        <Typography.Heading level="h1" className="mb-8">Form Components</Typography.Heading>
        <Typography.Text className="mb-8 text-lg">
          This page demonstrates the form components that have been migrated from Chakra UI to Tailwind CSS,
          following the modern UI/UX requirements.
        </Typography.Text>
        
        {/* Individual Components Section */}
        <section className="mb-12">
          <Typography.Heading level="h2" className="mb-6">Individual Form Components</Typography.Heading>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Input Examples */}
            <Card>
              <CardHeader>
                <Typography.Heading level="h3">Input Component</Typography.Heading>
                <Typography.Text variant="secondary">Text input field with various states</Typography.Text>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Typography.Text weight="medium" className="mb-2">Default Input</Typography.Text>
                  <Input placeholder="Default input field" />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Input with Value</Typography.Text>
                  <Input value="This is a completed input" />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Disabled Input</Typography.Text>
                  <Input disabled value="This input is disabled" />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Error Input</Typography.Text>
                  <Input error placeholder="Input with error state" />
                  <Typography.Text variant="error" size="sm" className="mt-1">This field has an error</Typography.Text>
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Input Sizes</Typography.Text>
                  <div className="space-y-2">
                    <Input size="sm" placeholder="Small input" />
                    <Input placeholder="Default size input" />
                    <Input size="lg" placeholder="Large input" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Select Examples */}
            <Card>
              <CardHeader>
                <Typography.Heading level="h3">Select Component</Typography.Heading>
                <Typography.Text variant="secondary">Dropdown selection field with various states</Typography.Text>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Typography.Text weight="medium" className="mb-2">Default Select</Typography.Text>
                  <Select>
                    <option value="">Select an option</option>
                    <option value="option1">Option 1</option>
                    <option value="option2">Option 2</option>
                    <option value="option3">Option 3</option>
                  </Select>
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Select with Value</Typography.Text>
                  <Select defaultValue="option1">
                    <option value="option1">Option 1</option>
                    <option value="option2">Option 2</option>
                    <option value="option3">Option 3</option>
                  </Select>
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Disabled Select</Typography.Text>
                  <Select disabled defaultValue="option1">
                    <option value="option1">This select is disabled</option>
                    <option value="option2">Option 2</option>
                  </Select>
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Error Select</Typography.Text>
                  <Select error>
                    <option value="">Please select an option</option>
                    <option value="option1">Option 1</option>
                    <option value="option2">Option 2</option>
                  </Select>
                  <Typography.Text variant="error" size="sm" className="mt-1">This field is required</Typography.Text>
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Select Sizes</Typography.Text>
                  <div className="space-y-2">
                    <Select selectSize="sm">
                      <option value="">Small select</option>
                      <option value="option1">Option 1</option>
                    </Select>
                    <Select>
                      <option value="">Default size select</option>
                      <option value="option1">Option 1</option>
                    </Select>
                    <Select selectSize="lg">
                      <option value="">Large select</option>
                      <option value="option1">Option 1</option>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Textarea Examples */}
            <Card>
              <CardHeader>
                <Typography.Heading level="h3">Textarea Component</Typography.Heading>
                <Typography.Text variant="secondary">Multi-line text input field</Typography.Text>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Typography.Text weight="medium" className="mb-2">Default Textarea</Typography.Text>
                  <Textarea placeholder="Enter your message here" rows={3} />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Textarea with Value</Typography.Text>
                  <Textarea value="This is a pre-filled textarea with some sample content that spans multiple lines to demonstrate how it looks." rows={3} />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Disabled Textarea</Typography.Text>
                  <Textarea disabled value="This textarea is disabled" rows={3} />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Error Textarea</Typography.Text>
                  <Textarea error placeholder="Textarea with error state" rows={3} />
                  <Typography.Text variant="error" size="sm" className="mt-1">This field has an error</Typography.Text>
                </div>
              </CardContent>
            </Card>
            
            {/* Checkbox Examples */}
            <Card>
              <CardHeader>
                <Typography.Heading level="h3">Checkbox Component</Typography.Heading>
                <Typography.Text variant="secondary">Boolean selection field</Typography.Text>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Typography.Text weight="medium" className="mb-2">Default Checkbox</Typography.Text>
                  <Checkbox id="checkbox1" label="Default checkbox" />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Checked Checkbox</Typography.Text>
                  <Checkbox id="checkbox2" label="Checked checkbox" checked />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">With Description</Typography.Text>
                  <Checkbox 
                    id="checkbox3" 
                    label="Terms and Conditions" 
                    description="I agree to the terms and conditions of this service"
                  />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Disabled Checkbox</Typography.Text>
                  <Checkbox id="checkbox4" disabled label="This checkbox is disabled" />
                </div>
                
                <div>
                  <Typography.Text weight="medium" className="mb-2">Error Checkbox</Typography.Text>
                  <Checkbox 
                    id="checkbox5" 
                    label="Required checkbox" 
                    error 
                    errorMessage="This field is required"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
        
        {/* FormField Examples */}
        <section className="mb-12">
          <Typography.Heading level="h2" className="mb-6">FormField Component</Typography.Heading>
          <Card>
            <CardHeader>
              <Typography.Heading level="h3">FormField Examples</Typography.Heading>
              <Typography.Text variant="secondary">
                FormField is a wrapper component that provides consistent labeling and error handling
              </Typography.Text>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField 
                label="Username" 
                htmlFor="username"
                helpText="Choose a unique username for your account"
              >
                <Input id="username" placeholder="Enter username" />
              </FormField>
              
              <FormField 
                label="Password" 
                htmlFor="password"
                required
              >
                <Input id="password" type="password" placeholder="Enter password" />
              </FormField>
              
              <FormField 
                label="Email" 
                htmlFor="email"
                required
                error={true}
                errorMessage="Please enter a valid email address"
              >
                <Input id="email" type="email" placeholder="Enter email" error />
              </FormField>
              
              <FormField 
                label="Category" 
                htmlFor="category"
                helpText="Select the category that best describes your request"
              >
                <Select id="category">
                  <option value="">Select a category</option>
                  <option value="support">Technical Support</option>
                  <option value="billing">Billing</option>
                  <option value="feedback">Feedback</option>
                </Select>
              </FormField>
            </CardContent>
          </Card>
        </section>
        
        {/* Complete Form Example - Removed due to TypeScript errors */}
        <section className="mb-12">
          <Typography.Heading level="h2" className="mb-6">Complete Form Example</Typography.Heading>
          <Typography.Text className="mb-8">
            This section previously contained a sample form that has been removed due to compatibility issues with the new component architecture.
          </Typography.Text>
        </section>
      </div>
    </Container>
  );
};

export default FormExamplesPage;
