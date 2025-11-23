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

export interface CategorySpending {
  category_id: string | null;
  category_name: string;
  icon: string | null;
  color: string;
  amount: number;
}

export interface MonthlyTrend {
  month: string;
  income: number;
  expenses: number;
  savings: number;
}

export interface DailySpending {
  day: number;
  date: string;
  amount: number;
}

export interface MonthlySummary {
  month: number;
  year: number;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  transaction_count: number;
  avg_expense: number;
  largest_expense: number;
}

export const analyticsService = {
  getRecurring: async (): Promise<RecurringTransaction[]> => {
    const response = await api.get('/analytics/recurring');
    return response.data;
  },

  getTopMerchants: async (limit: number = 5): Promise<TopMerchant[]> => {
    const response = await api.get('/analytics/top-merchants', { params: { limit } });
    return response.data;
  },

  getSpendingByCategory: async (month?: number, year?: number): Promise<CategorySpending[]> => {
    const params: any = {};
    if (month) params.month = month;
    if (year) params.year = year;
    const response = await api.get('/analytics/spending-by-category', { params });
    return response.data;
  },

  getMonthlyTrends: async (months: number = 6): Promise<MonthlyTrend[]> => {
    const response = await api.get('/analytics/monthly-trends', { params: { months } });
    return response.data;
  },

  getDailySpending: async (month?: number, year?: number): Promise<DailySpending[]> => {
    const params: any = {};
    if (month) params.month = month;
    if (year) params.year = year;
    const response = await api.get('/analytics/daily-spending', { params });
    return response.data;
  },

  getSummary: async (month?: number, year?: number): Promise<MonthlySummary> => {
    const params: any = {};
    if (month) params.month = month;
    if (year) params.year = year;
    const response = await api.get('/analytics/summary', { params });
    return response.data;
  }
};
