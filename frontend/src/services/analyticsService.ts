import api from './api';

export interface RecurringTransaction {
  merchant: string;
  amount: number;
  interval: string;
  confidence: number;
  avg_days: number;
  last_date: string;
  next_date: string;
  transaction_count: number;
  example_tx_id: string;
}

export interface TopMerchant {
  merchant: string;
  amount: number;
}

export const analyticsService = {
  getRecurring: async (): Promise<RecurringTransaction[]> => {
    const response = await api.get('/analytics/recurring');
    return response.data;
  },

  getTopMerchants: async (limit: number = 5): Promise<TopMerchant[]> => {
    const response = await api.get('/analytics/top-merchants', { params: { limit } });
    return response.data;
  }
};
