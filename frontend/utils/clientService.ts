import api from './api';

// Types
export interface Client {
  id: string;
  organization_id: string;
  name: string;
  tax_id: string;
  email?: string;
  phone?: string;
  address?: string;
  industry?: string;
  created_at: string;
  updated_at: string;
  status: string;
}

export interface ClientCreate {
  organization_id: string;
  name: string;
  tax_id: string;
  email?: string;
  phone?: string;
  address?: string;
  industry?: string;
}

export interface ClientUpdate {
  name?: string;
  tax_id?: string;
  email?: string;
  phone?: string;
  address?: string;
  industry?: string;
  status?: string;
}

// Get all clients
export const getClients = async () => {
  const response = await api.get<Client[]>('/clients');
  return response.data;
};

// Get client by ID
export const getClient = async (id: string) => {
  const response = await api.get<Client>(`/clients/${id}`);
  return response.data;
};

// Create a new client
export const createClient = async (client: ClientCreate) => {
  const response = await api.post<Client>('/clients', client);
  return response.data;
};

// Update a client
export const updateClient = async (id: string, update: ClientUpdate) => {
  const response = await api.put<Client>(`/clients/${id}`, update);
  return response.data;
};

// Delete a client
export const deleteClient = async (id: string) => {
  const response = await api.delete<Client>(`/clients/${id}`);
  return response.data;
}; 