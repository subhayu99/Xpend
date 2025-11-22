import api from './api';
import { Transaction } from './transactionService';

export interface DashboardSummary {
  total_balance: number;
  monthly_income: number;
  monthly_expense: number;
  savings_rate: number;
}

export interface CategorySpend {
  category_name: string;
  amount: number;
  color: string | null;
  [key: string]: any; // Allow other properties for Recharts
}

export interface MonthlyTrend {
  month: string;
  income: number;
  expense: number;
}

export interface DashboardData {
  summary: DashboardSummary;
  category_spend: CategorySpend[];
  monthly_trend: MonthlyTrend[];
  recent_transactions: Transaction[];
}

const dashboardService = {
  getDashboardData: async (): Promise<DashboardData> => {
    const response = await api.get<DashboardData>('/dashboard');
    return response.data;
  }
};

export default dashboardService;
