import api from './api';

export interface Transaction {
  id: string;
  amount: number;
  description: string;
  merchant_name: string | null;
  transaction_date: string;
  transaction_type: 'income' | 'expense' | 'transfer';
  category_id: string | null;
  account_id: string;
  source_file: string | null;
}

export interface TransactionCreate {
  amount: number;
  description: string;
  merchant_name?: string;
  transaction_date: string;
  transaction_type: 'income' | 'expense' | 'transfer';
  category_id?: string;
  account_id: string;
}

export interface ParseResult {
  transactions: any[];
  template_found: boolean;
  detected_structure: any | null;
}

export interface TransactionFilters {
  skip?: number;
  limit?: number;
  account_id?: string;
  category_id?: string;
  transaction_type?: 'income' | 'expense' | 'transfer';
  start_date?: string;
  end_date?: string;
  search?: string;
}

export const transactionService = {
  getAll: async (filters: TransactionFilters = {}): Promise<Transaction[]> => {
    const params: any = { 
      skip: filters.skip || 0, 
      limit: filters.limit || 100 
    };
    if (filters.account_id) params.account_id = filters.account_id;
    if (filters.category_id) params.category_id = filters.category_id;
    if (filters.transaction_type) params.transaction_type = filters.transaction_type;
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;
    if (filters.search) params.search = filters.search;
    
    const response = await api.get('/transactions', { params });
    return response.data;
  },

  create: async (data: TransactionCreate): Promise<Transaction> => {
    const response = await api.post('/transactions', data);
    return response.data;
  },

  createBulk: async (data: TransactionCreate[]): Promise<Transaction[]> => {
    const response = await api.post('/transactions/confirm', data); // Updated endpoint
    return response.data;
  },

  uploadStatement: async (file: File, accountId: string): Promise<ParseResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', accountId);
    
    const response = await api.post('/transactions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  saveTemplate: async (accountId: string, fileType: string, structure: any) => {
    await api.post('/transactions/save-template', {
      account_id: accountId,
      file_type: fileType,
      structure_json: JSON.stringify(structure)
    });
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/transactions/${id}`);
  },

  update: async (id: string, data: Partial<TransactionCreate>): Promise<Transaction> => {
    const response = await api.put(`/transactions/${id}`, data);
    return response.data;
  },
};
