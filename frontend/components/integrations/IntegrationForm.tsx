import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Typography } from '../ui/Typography';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { LegacySelect } from '../ui/Select';
import { Textarea } from '../ui/Textarea';
import { Button } from '../ui/Button';
import { useToast } from '../ui/Toast';
import { JsonEditor } from './JsonEditor';

interface Client {
  id: string;
  name: string;
}

interface IntegrationFormData {
  name: string;
  description: string;
  client_id: string;
  config: Record<string, any>;
}

interface IntegrationFormProps {
  clients: Client[];
  onSubmit: (data: IntegrationFormData) => Promise<void>;
  initialData?: Partial<IntegrationFormData>;
}

export const IntegrationForm: React.FC<IntegrationFormProps> = ({
  clients,
  onSubmit,
  initialData = {}
}) => {
  const { 
    handleSubmit, 
    register, 
    control,
    formState: { errors, isSubmitting } 
  } = useForm<IntegrationFormData>({
    defaultValues: {
      name: initialData.name || '',
      description: initialData.description || '',
      client_id: initialData.client_id || '',
      config: initialData.config || {
        api_url: '',
        auth_method: 'api_key',
        api_key: '',
        schedule: 'daily',
        timezone: 'Africa/Lagos'
      }
    }
  });
  
  const toast = useToast();
  
  const handleFormSubmit = async (data: IntegrationFormData) => {
    try {
      await onSubmit(data);
      toast({
        title: 'Integration saved',
        description: 'The integration has been successfully saved',
        status: 'success',
        duration: 5000,
        isClosable: true
      });
    } catch (error) {
      toast({
        title: 'Error saving integration',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };
  
  return (
    <div className="w-full max-w-3xl p-4">
      <Typography.Heading level="h2" className="mb-6">
        {initialData.name ? 'Update Integration' : 'Create New Integration'}
      </Typography.Heading>
      
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <div className="space-y-6">
          <FormField 
            label="Integration Name" 
            htmlFor="name" 
            required
            error={!!errors.name}
            errorMessage={errors.name?.message?.toString()}
          >
            <Input
              id="name"
              placeholder="Enter integration name"
              error={!!errors.name}
              {...register("name", {
                required: "Name is required",
                minLength: { value: 3, message: "Name must be at least 3 characters" }
              })}
            />
          </FormField>
          
          <FormField 
            label="Client" 
            htmlFor="client_id" 
            required
            error={!!errors.client_id}
            errorMessage={errors.client_id?.message?.toString()}
          >
            <LegacySelect
              id="client_id"
              error={!!errors.client_id}
              {...register("client_id", {
                required: "Client selection is required"
              })}
            >
              <option value="" disabled selected>Select client</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </LegacySelect>
          </FormField>
          
          <FormField 
            label="Description" 
            htmlFor="description"
            error={!!errors.description}
            errorMessage={errors.description?.message?.toString()}
          >
            <Textarea
              id="description"
              placeholder="Enter integration description"
              error={!!errors.description}
              rows={4}
              {...register("description")}
            />
          </FormField>
          
          <FormField 
            label="Configuration" 
            htmlFor="config" 
            required
            error={!!errors.config}
            errorMessage={errors.config?.message?.toString()}
          >
            <Controller
              name="config"
              control={control}
              rules={{ required: "Configuration is required" }}
              render={({ field }) => (
                <JsonEditor
                  value={field.value}
                  onChange={field.onChange}
                  height="300px"
                />
              )}
            />
          </FormField>
          
          <Button 
            loading={isSubmitting} 
            type="submit"
            size="lg"
            className="w-full mt-6"
          >
            {initialData.name ? 'Update Integration' : 'Create Integration'}
          </Button>
        </div>
      </form>
    </div>
  );
}; 