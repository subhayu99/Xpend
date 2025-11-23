import api from './api';

export interface Budget {
  id: string;
  category_id: string;
  amount: number;
  period: string;
  month: number;
  year: number;
  is_active: boolean;
}

export interface BudgetCreate {
  category_id: string;
  amount: number;
  period?: string;
  month?: number;
  year?: number;
}

export interface BudgetProgress extends Budget {
  spent: number;
  remaining: number;
  percentage: number;
}

export const budgetService = {
  getAll: async (month?: number, year?: number): Promise<BudgetProgress[]> => {
    const params: any = {};
    if (month) params.month = month;
    if (year) params.year = year;
    
    const response = await api.get('/budgets', { params });
    return response.data;
  },

  create: async (data: BudgetCreate): Promise<Budget> => {
    const response = await api.post('/budgets', data);
    return response.data;
  },

  update: async (id: string, amount: number): Promise<Budget> => {
    const response = await api.put(`/budgets/${id}`, { amount });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/budgets/${id}`);
  }
};
