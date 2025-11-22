import api from './api';

export interface Account {
  id: string;
  name: string;
  bank_name: string | null;
  account_type: 'savings' | 'current' | 'credit_card' | 'wallet';
  last_4_digits: string | null;
  opening_balance: number;
  opening_balance_date: string | null;
  current_balance: number;
  is_active: boolean;
}

export interface AccountCreate {
  name: string;
  bank_name?: string;
  account_type: 'savings' | 'current' | 'credit_card' | 'wallet';
  last_4_digits?: string;
  opening_balance: number;
  opening_balance_date?: string;
}

export const accountService = {
  getAll: async (): Promise<Account[]> => {
    const response = await api.get('/accounts');
    return response.data;
  },

  getById: async (id: string): Promise<Account> => {
    const response = await api.get(`/accounts/${id}`);
    return response.data;
  },

  create: async (data: AccountCreate): Promise<Account> => {
    const response = await api.post('/accounts', data);
    return response.data;
  },

  update: async (id: string, data: Partial<AccountCreate>): Promise<Account> => {
    const response = await api.put(`/accounts/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/accounts/${id}`);
  },
};
