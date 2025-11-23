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

export const transactionService = {
  getAll: async (skip = 0, limit = 100, accountId?: string): Promise<Transaction[]> => {
    const params: any = { skip, limit };
    if (accountId) params.account_id = accountId;
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
