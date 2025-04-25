import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { Box, Heading } from '@chakra-ui/react';
import { FormControl, FormLabel, FormErrorMessage, Input, Select, Textarea, VStack } from '../ui/ChakraForm';
import { Button, useToast } from '../ui/ChakraButton';
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
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error saving integration',
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };
  
  return (
    <Box width="100%" maxWidth="800px" p={4}>
      <Heading size="lg" mb={6}>
        {initialData.name ? 'Update Integration' : 'Create New Integration'}
      </Heading>
      
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <VStack spacing={6} align="flex-start">
          <FormControl isInvalid={!!errors.name} isRequired>
            <FormLabel htmlFor="name">Integration Name</FormLabel>
            <Input
              id="name"
              placeholder="Enter integration name"
              {...register("name", {
                required: "Name is required",
                minLength: { value: 3, message: "Name must be at least 3 characters" }
              })}
            />
            <FormErrorMessage>{errors.name?.message?.toString() || ''}</FormErrorMessage>
          </FormControl>
          
          <FormControl isInvalid={!!errors.client_id} isRequired>
            <FormLabel htmlFor="client_id">Client</FormLabel>
            <Select
              id="client_id"
              placeholder="Select client"
              {...register("client_id", {
                required: "Client selection is required"
              })}
            >
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </Select>
            <FormErrorMessage>{errors.client_id?.message?.toString() || ''}</FormErrorMessage>
          </FormControl>
          
          <FormControl isInvalid={!!errors.description}>
            <FormLabel htmlFor="description">Description</FormLabel>
            <Textarea
              id="description"
              placeholder="Enter integration description"
              {...register("description")}
            />
            <FormErrorMessage>{errors.description?.message?.toString() || ''}</FormErrorMessage>
          </FormControl>
          
          <FormControl isInvalid={!!errors.config} isRequired>
            <FormLabel htmlFor="config">Configuration</FormLabel>
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
            <FormErrorMessage>{errors.config?.message?.toString() || ''}</FormErrorMessage>
          </FormControl>
          
          <Button 
            mt={4} 
            colorScheme="blue" 
            isLoading={isSubmitting} 
            type="submit"
            size="lg"
            width="full"
          >
            {initialData.name ? 'Update Integration' : 'Create Integration'}
          </Button>
        </VStack>
      </form>
    </Box>
  );
}; 