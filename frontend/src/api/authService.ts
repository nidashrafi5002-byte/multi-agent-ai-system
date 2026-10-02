import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export async function register(data: RegisterData): Promise<User> {
  try {
    const response = await axios.post<User>(`${API_BASE}/api/auth/register`, data);
    return response.data;
  } catch (error: any) {
    throw new Error(error?.response?.data?.detail || 'Registration failed');
  }
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  try {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await axios.post<AuthResponse>(
      `${API_BASE}/api/auth/login`,
      formData,
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }
    );
    return response.data;
  } catch (error: any) {
    throw new Error(error?.response?.data?.detail || 'Login failed');
  }
}

export async function getCurrentUser(token: string): Promise<User> {
  try {
    const response = await axios.get<User>(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(error?.response?.data?.detail || 'Failed to fetch user');
  }
}

export function setToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

export function getToken(): string | null {
  return localStorage.getItem('auth_token');
}

export function removeToken(): void {
  localStorage.removeItem('auth_token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
