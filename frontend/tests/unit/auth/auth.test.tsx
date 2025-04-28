import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';

// Assuming these components exist - adjust imports based on your actual implementation
import Login from '@/components/auth/Login';
import Register from '@/components/auth/Register';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Authentication Components', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Login Component', () => {
    test('renders login form', () => {
      render(<Login />);
      
      // Check if key elements are rendered
      expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    test('handles successful login', async () => {
      // Mock successful login response
      mockedAxios.post.mockResolvedValueOnce({
        data: { 
          access_token: 'test-token',
          token_type: 'bearer'
        }
      });

      render(<Login />);
      
      // Fill the form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'password123' }
      });
      
      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /login/i }));
      
      // Verify API call was made with correct data
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/auth/login'),
          expect.any(Object)
        );
      });
      
      // Verify redirect or success message
      await waitFor(() => {
        expect(screen.getByText(/logged in successfully/i)).toBeInTheDocument();
      });
    });

    test('handles login failure', async () => {
      // Mock login failure
      mockedAxios.post.mockRejectedValueOnce({
        response: {
          status: 401,
          data: {
            detail: 'Incorrect email or password'
          }
        }
      });

      render(<Login />);
      
      // Fill the form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'wrong-password' }
      });
      
      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /login/i }));
      
      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/incorrect email or password/i)).toBeInTheDocument();
      });
    });
  });

  describe('Register Component', () => {
    test('renders registration form', () => {
      render(<Register />);
      
      // Check if key elements are rendered
      expect(screen.getByRole('heading', { name: /register/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
    });

    test('handles successful registration', async () => {
      // Mock successful registration
      mockedAxios.post.mockResolvedValueOnce({
        data: {
          id: '123',
          email: 'new@example.com',
          full_name: 'New User',
          role: 'si_user'
        }
      });

      render(<Register />);
      
      // Fill the form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'new@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'Password123' }
      });
      fireEvent.change(screen.getByLabelText(/full name/i), {
        target: { value: 'New User' }
      });
      
      // Submit the form
      fireEvent.click(screen.getByRole('button', { name: /register/i }));
      
      // Verify API call was made with correct data
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/auth/register'),
          expect.objectContaining({
            email: 'new@example.com',
            password: 'Password123',
            full_name: 'New User'
          })
        );
      });
      
      // Verify success message or redirect
      await waitFor(() => {
        expect(screen.getByText(/registered successfully/i)).toBeInTheDocument();
      });
    });

    test('validates form inputs', async () => {
      render(<Register />);
      
      // Submit without filling the form
      fireEvent.click(screen.getByRole('button', { name: /register/i }));
      
      // Verify validation messages
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });
    });
  });
}); 