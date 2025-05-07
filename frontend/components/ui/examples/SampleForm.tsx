import React, { useState } from 'react';
import { Card, CardHeader, CardContent, CardFooter } from '../Card';
import { Typography } from '../Typography';
import { Input } from '../Input';
import { Select } from '../Select';
import { Textarea } from '../Textarea';
import { Checkbox } from '../Checkbox';
import { FormField } from '../FormField';
import { Button } from '../Button';

interface FormData {
  name: string;
  email: string;
  companySize: string;
  message: string;
  acceptTerms: boolean;
}

interface FormErrors {
  name?: string;
  email?: string;
  companySize?: string;
  message?: string;
  acceptTerms?: string;
}

/**
 * SampleForm Component
 * 
 * This is a sample form that demonstrates how to use all the new Tailwind-based form components
 * together in a complete form with validation and error handling.
 */
const SampleForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    companySize: '',
    message: '',
    acceptTerms: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when field is changed
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^\S+@\S+\.\S+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    if (!formData.companySize) {
      newErrors.companySize = 'Please select your company size';
    }
    
    if (!formData.message.trim()) {
      newErrors.message = 'Message is required';
    } else if (formData.message.length < 10) {
      newErrors.message = 'Message must be at least 10 characters';
    }
    
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the terms and conditions';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      setIsSubmitting(true);
      
      // Simulate API call
      setTimeout(() => {
        setIsSubmitting(false);
        setIsSubmitted(true);
        
        // Reset form after successful submission
        setTimeout(() => {
          setFormData({
            name: '',
            email: '',
            companySize: '',
            message: '',
            acceptTerms: false,
          });
          setIsSubmitted(false);
        }, 3000);
      }, 1500);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <Typography.Heading level="h2">Contact Form</Typography.Heading>
        <Typography.Text variant="secondary">
          Fill out this form to get in touch with our team
        </Typography.Text>
      </CardHeader>
      
      <CardContent>
        {isSubmitted ? (
          <div className="bg-success-light p-4 rounded-md text-center">
            <Typography.Heading level="h4" className="text-success mb-2">Form Submitted Successfully!</Typography.Heading>
            <Typography.Text>Thank you for contacting us. We'll get back to you shortly.</Typography.Text>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <FormField 
              label="Full Name" 
              htmlFor="name"
              required
              error={!!errors.name}
              errorMessage={errors.name}
            >
              <Input
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Enter your full name"
                error={!!errors.name}
              />
            </FormField>
            
            <FormField 
              label="Email Address" 
              htmlFor="email"
              required
              error={!!errors.email}
              errorMessage={errors.email}
            >
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Enter your email address"
                error={!!errors.email}
              />
            </FormField>
            
            <FormField 
              label="Company Size" 
              htmlFor="companySize"
              required
              error={!!errors.companySize}
              errorMessage={errors.companySize}
            >
              <Select
                id="companySize"
                name="companySize"
                value={formData.companySize}
                onChange={handleChange}
                error={!!errors.companySize}
              >
                <option value="">Select company size</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-500">201-500 employees</option>
                <option value="501+">501+ employees</option>
              </Select>
            </FormField>
            
            <FormField 
              label="Message" 
              htmlFor="message"
              required
              error={!!errors.message}
              errorMessage={errors.message}
              helpText="Please provide details about your inquiry"
            >
              <Textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                placeholder="Enter your message"
                rows={4}
                error={!!errors.message}
              />
            </FormField>
            
            <FormField 
              error={!!errors.acceptTerms}
              errorMessage={errors.acceptTerms}
            >
              <Checkbox
                id="acceptTerms"
                name="acceptTerms"
                checked={formData.acceptTerms}
                onChange={handleChange}
                label="I accept the terms and conditions"
                error={!!errors.acceptTerms}
              />
            </FormField>
          </form>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-end">
        {!isSubmitted && (
          <Button 
            type="submit" 
            onClick={handleSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Form'}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

export default SampleForm;
