import React from 'react';
import { Loader2 } from 'lucide-react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

// Define the form validation schema using Yup
const schema = yup.object().shape({
  name: yup.string().required('Integration name is required'),
  description: yup.string(),
  url: yup
    .string()
    .required('Odoo URL is required')
    .matches(
      /^https?:\/\/.+/,
      'URL must start with http:// or https://'
    ),
  database: yup.string().required('Database name is required'),
  username: yup.string().required('Username is required'),
  password: yup.string().when('auth_method', (auth_method) => {
    return auth_method[0] === 'password' 
      ? yup.string().required('Password is required')
      : yup.string();
  }),
  api_key: yup.string().when('auth_method', (auth_method) => {
    return auth_method[0] === 'api_key'
      ? yup.string().required('API Key is required') 
      : yup.string();
  }),
  auth_method: yup
    .string()
    .oneOf(['password', 'api_key'], 'Invalid authentication method')
    .required('Authentication method is required')
});

interface OdooConnectionFormProps {
  config: {
    name: string;
    description: string;
    url: string;
    database: string;
    username: string;
    password: string;
    api_key?: string;
    auth_method: string;
  };
  onChange: (field: string, value: string) => void;
  isSubmitting: boolean;
}

// Define the shape of the form values to match the schema
type FormValues = {
  name: string;
  description: string;
  url: string;
  database: string;
  username: string;
  password: string;
  api_key: string;
  auth_method: "password" | "api_key";
};

const OdooConnectionForm: React.FC<OdooConnectionFormProps> = ({
  config,
  onChange,
  isSubmitting
}) => {
  const { control, formState: { errors } } = useForm<FormValues>({
    resolver: yupResolver(schema) as any,
    defaultValues: {
      ...config,
      api_key: config.api_key || '',
      auth_method: (config.auth_method as "password" | "api_key") || 'password'
    },
    mode: 'onChange'
  });

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement | { value: unknown }>) => {
    onChange(field, e.target.value as string);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="col-span-1 md:col-span-2">
        <h3 className="text-lg font-medium mb-2">
          Integration Details
        </h3>
      </div>
      
      <div>
        <Controller
          name="name"
          control={control}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Integration Name <span className="text-red-500">*</span>
              </label>
              <input
                id="name"
                type="text"
                className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.name ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                value={config.name}
                onChange={handleChange('name')}
                disabled={isSubmitting}
              />
              {errors.name && (
                <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>
              )}
            </div>
          )}
        />
      </div>
      
      <div>
        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <input
                id="description"
                type="text"
                className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.description ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                value={config.description}
                onChange={handleChange('description')}
                disabled={isSubmitting}
              />
              {errors.description && (
                <p className="text-red-500 text-xs mt-1">{errors.description.message}</p>
              )}
            </div>
          )}
        />
      </div>
      
      <div className="col-span-1 md:col-span-2 mt-4">
        <h3 className="text-lg font-medium mb-2">
          Odoo Connection Details
        </h3>
      </div>
      
      <div>
        <Controller
          name="url"
          control={control}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="url" className="block text-sm font-medium text-gray-700">
                Odoo URL <span className="text-red-500">*</span>
              </label>
              <input
                id="url"
                type="text"
                placeholder="https://example.odoo.com"
                className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.url ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                value={config.url}
                onChange={handleChange('url')}
                disabled={isSubmitting}
              />
              {errors.url ? (
                <p className="text-red-500 text-xs mt-1">{errors.url.message}</p>
              ) : (
                <p className="text-gray-500 text-xs mt-1">e.g. https://example.odoo.com</p>
              )}
            </div>
          )}
        />
      </div>
      
      <div>
        <Controller
          name="database"
          control={control}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="database" className="block text-sm font-medium text-gray-700">
                Database Name <span className="text-red-500">*</span>
              </label>
              <input
                id="database"
                type="text"
                className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.database ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                value={config.database}
                onChange={handleChange('database')}
                disabled={isSubmitting}
              />
              {errors.database && (
                <p className="text-red-500 text-xs mt-1">{errors.database.message}</p>
              )}
            </div>
          )}
        />
      </div>
      
      <div>
        <Controller
          name="auth_method"
          control={control}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="auth_method" className="block text-sm font-medium text-gray-700">
                Authentication Method <span className="text-red-500">*</span>
              </label>
              <select
                id="auth_method"
                className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.auth_method ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                value={config.auth_method}
                onChange={(e) => {
                  handleChange('auth_method')(e);
                  // Clear password or API key when switching auth methods
                  if (e.target.value === 'password') {
                    onChange('api_key', '');
                  } else if (e.target.value === 'api_key') {
                    onChange('password', '');
                  }
                }}
                disabled={isSubmitting}
              >
                <option value="password">Username & Password</option>
                <option value="api_key">API Key</option>
              </select>
              {errors.auth_method && (
                <p className="text-red-500 text-xs mt-1">{errors.auth_method.message}</p>
              )}
            </div>
          )}
        />
      </div>
      
      <div>
        <Controller
          name="username"
          control={control}
          render={({ field }) => (
            <div className="space-y-1">
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Username <span className="text-red-500">*</span>
              </label>
              <input
                id="username"
                type="text"
                className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.username ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                value={config.username}
                onChange={handleChange('username')}
                disabled={isSubmitting}
              />
              {errors.username && (
                <p className="text-red-500 text-xs mt-1">{errors.username.message}</p>
              )}
            </div>
          )}
        />
      </div>
      
      {config.auth_method === 'password' && (
        <div>
          <Controller
            name="password"
            control={control}
            render={({ field }) => (
              <div className="space-y-1">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password <span className="text-red-500">*</span>
                </label>
                <input
                  id="password"
                  type="password"
                  className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.password ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                  value={config.password}
                  onChange={handleChange('password')}
                  disabled={isSubmitting}
                />
                {errors.password && (
                  <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>
                )}
              </div>
            )}
          />
        </div>
      )}
      
      {config.auth_method === 'api_key' && (
        <div>
          <Controller
            name="api_key"
            control={control}
            render={({ field }) => (
              <div className="space-y-1">
                <label htmlFor="api_key" className="block text-sm font-medium text-gray-700">
                  API Key <span className="text-red-500">*</span>
                </label>
                <input
                  id="api_key"
                  type="text"
                  className={`block w-full rounded-md shadow-sm py-2 px-3 border ${errors.api_key ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'} sm:text-sm ${isSubmitting ? 'bg-gray-100 cursor-not-allowed' : ''}`}
                  value={config.api_key || ''}
                  onChange={handleChange('api_key')}
                  disabled={isSubmitting}
                />
                {errors.api_key && (
                  <p className="text-red-500 text-xs mt-1">{errors.api_key.message}</p>
                )}
              </div>
            )}
          />
        </div>
      )}

      {isSubmitting && (
        <div className="col-span-1 md:col-span-2 flex justify-center items-center mt-4">
          <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
          <span className="ml-2 text-sm text-gray-600">
            Testing connection...
          </span>
        </div>
      )}

      <div className="col-span-1 md:col-span-2 mt-4">
        <p className="text-xs text-gray-500">
          Note: Your credentials are encrypted and securely stored. We only use them to communicate with your Odoo instance.
        </p>
      </div>
    </div>
  );
};

export default OdooConnectionForm;
