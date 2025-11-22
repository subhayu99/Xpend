import api from './api';

export interface Category {
  id: string;
  name: string;
  type: 'income' | 'expense';
  icon: string | null;
  color: string | null;
  is_default: boolean;
}

export interface CategoryCreate {
  name: string;
  type: 'income' | 'expense';
  icon?: string;
  color?: string;
}

export const categoryService = {
  getAll: async (type?: 'income' | 'expense'): Promise<Category[]> => {
    const params: any = {};
    if (type) params.type = type;
    const response = await api.get('/categories', { params });
    return response.data;
  },

  create: async (data: CategoryCreate): Promise<Category> => {
    const response = await api.post('/categories', data);
    return response.data;
  },

  update: async (id: string, data: Partial<CategoryCreate>): Promise<Category> => {
    const response = await api.put(`/categories/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/categories/${id}`);
  },
};
