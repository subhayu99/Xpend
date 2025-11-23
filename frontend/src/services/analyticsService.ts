import api from './api';

export interface RecurringTransaction {
  merchant: string;
  amount: number;
  amount_min: number;
  amount_max: number;
  is_variable_amount: boolean;
  interval: string;
  confidence: number;
  avg_days: number;
  std_days: number;
  last_date: string;
  next_date: string;
  transaction_count: number;
  transaction_ids: string[];
  transactions: { id: string; date: string; amount: number }[];
  example_tx_id: string;
  status: 'suggested' | 'confirmed' | 'dismissed';
  existing_rule_id?: string | null;
  existing_rule_status?: string | null;
}

export interface RecurringRule {
  id: string;
  user_id: string;
  merchant_name: string;
  expected_amount: number;
  amount_min: number | null;
  amount_max: number | null;
  is_variable_amount: boolean;
  interval: string;
  avg_days: number;
  status: 'suggested' | 'confirmed' | 'dismissed';
  confidence: number;
  last_transaction_date: string | null;
  next_expected_date: string | null;
  transaction_count: number;
  category_id: string | null;
  notify_before_days: number;
  is_notification_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface RecurringListResponse {
  suggestions: RecurringTransaction[];
  confirmed: RecurringRule[];
  dismissed_count: number;
}

export interface ConfirmRecurringRequest {
  merchant_name: string;
  expected_amount: number;
  amount_min?: number | null;
  amount_max?: number | null;
  is_variable_amount: boolean;
  interval: string;
  avg_days: number;
  confidence: number;
  last_transaction_date?: string | null;
  next_expected_date?: string | null;
  transaction_count: number;
  category_id?: string | null;
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
  getRecurring: async (): Promise<RecurringListResponse> => {
    const response = await api.get('/analytics/recurring');
    return response.data;
  },

  confirmRecurring: async (request: ConfirmRecurringRequest): Promise<RecurringRule> => {
    const response = await api.post('/analytics/recurring/confirm', request);
    return response.data;
  },

  dismissRecurring: async (merchantName: string): Promise<{ message: string }> => {
    const response = await api.post('/analytics/recurring/dismiss', { merchant_name: merchantName });
    return response.data;
  },

  deleteRecurringRule: async (ruleId: string): Promise<{ message: string }> => {
    const response = await api.delete(`/analytics/recurring/${ruleId}`);
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
