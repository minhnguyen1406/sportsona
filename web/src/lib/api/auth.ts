/** Auth endpoints: register, login, logout, current user, password reset. */

import { apiFetch, type TokenResponse } from './client';

export interface UserRead {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export const authApi = {
  login(email: string, password: string): Promise<TokenResponse> {
    return apiFetch('/api/v1/auth/login', {
      method: 'POST',
      form: { username: email, password },
      skipAuth: true
    });
  },
  register(email: string, username: string, password: string): Promise<UserRead> {
    return apiFetch('/api/v1/auth/register', {
      method: 'POST',
      json: { email, username, password },
      skipAuth: true
    });
  },
  me(): Promise<UserRead> {
    return apiFetch('/api/v1/auth/me');
  },
  logout(refresh_token: string): Promise<void> {
    return apiFetch('/api/v1/auth/logout', {
      method: 'POST',
      json: { refresh_token },
      skipAuth: true
    });
  },
  forgotPassword(email: string): Promise<void> {
    return apiFetch('/api/v1/auth/password/forgot', {
      method: 'POST',
      json: { email },
      skipAuth: true
    });
  }
};
