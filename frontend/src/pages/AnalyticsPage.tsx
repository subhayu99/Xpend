import React, { useState, useEffect } from 'react';
import {
  analyticsService,
  RecurringTransaction,
  TopMerchant,
  CategorySpending,
  MonthlyTrend,
  MonthlySummary
} from '../services/analyticsService';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend,
  Area, AreaChart
} from 'recharts';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

export const AnalyticsPage: React.FC = () => {
  const [recurring, setRecurring] = useState<RecurringTransaction[]>([]);
  const [topMerchants, setTopMerchants] = useState<TopMerchant[]>([]);
  const [categorySpending, setCategorySpending] = useState<CategorySpending[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<MonthlyTrend[]>([]);
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [loading, setLoading] = useState(true);

  const currentDate = new Date();
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());

  useEffect(() => {
    loadData();
  }, [selectedMonth, selectedYear]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [recurringData, merchantsData, categoryData, trendsData, summaryData] = await Promise.all([
        analyticsService.getRecurring(),
        analyticsService.getTopMerchants(5),
        analyticsService.getSpendingByCategory(selectedMonth, selectedYear),
        analyticsService.getMonthlyTrends(6),
        analyticsService.getSummary(selectedMonth, selectedYear)
      ]);
      // Extract suggestions from the new response format
      setRecurring(recurringData.suggestions || []);
      setTopMerchants(merchantsData);
      setCategorySpending(categoryData);
      setMonthlyTrends(trendsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      if (selectedMonth === 1) {
        setSelectedMonth(12);
        setSelectedYear(selectedYear - 1);
      } else {
        setSelectedMonth(selectedMonth - 1);
      }
    } else {
      if (selectedMonth === 12) {
        setSelectedMonth(1);
        setSelectedYear(selectedYear + 1);
      } else {
        setSelectedMonth(selectedMonth + 1);
      }
    }
  };

  const formatCurrency = (value: number) => `₹${value.toLocaleString()}`;

  if (loading) return <div className="p-8 text-center">Loading insights...</div>;

  return (
    <div className="space-y-8">
      {/* Header with Month Navigation */}
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Spending Insights</h1>
        <div className="flex items-center gap-4">
          {/* Export Button */}
          <button
            onClick={async () => {
              try {
                const { exportService } = await import('../services/exportService');
                await exportService.exportMonthlyReportCSV(selectedMonth, selectedYear);
              } catch (error) {
                console.error('Export failed:', error);
                alert('Failed to export report');
              }
            }}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export Report
          </button>

          {/* Month/Year Navigation */}
          <div className="flex items-center gap-2 bg-white rounded-lg border border-gray-200 p-1">
            <button
              onClick={() => navigateMonth('prev')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <span className="px-3 py-1 font-medium text-gray-900 min-w-[140px] text-center">
              {MONTHS[selectedMonth - 1]} {selectedYear}
            </span>
            <button
              onClick={() => navigateMonth('next')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Total Income</p>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(summary.total_income)}</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Total Expenses</p>
            <p className="text-2xl font-bold text-red-600">{formatCurrency(summary.total_expenses)}</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Net Savings</p>
            <p className={`text-2xl font-bold ${summary.net_savings >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(summary.net_savings)}
            </p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <p className="text-sm text-gray-500">Transactions</p>
            <p className="text-2xl font-bold text-gray-900">{summary.transaction_count}</p>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending by Category (Pie Chart) */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Spending by Category</h2>
          {categorySpending.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No expense data for this month
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categorySpending.map(c => ({ ...c, name: c.category_name }))}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="amount"
                    nameKey="name"
                    label={({ name, percent }) =>
                      `${name} (${((percent || 0) * 100).toFixed(0)}%)`
                    }
                    labelLine={false}
                  >
                    {categorySpending.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
          {/* Category Legend */}
          <div className="mt-4 grid grid-cols-2 gap-2">
            {categorySpending.slice(0, 6).map((cat, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: cat.color || COLORS[index % COLORS.length] }}
                />
                <span className="text-gray-700 truncate">{cat.category_name}</span>
                <span className="text-gray-500 ml-auto">{formatCurrency(cat.amount)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Merchants Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Top Merchants</h2>
          {topMerchants.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No merchant data available
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topMerchants} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(v) => `₹${v}`} />
                  <YAxis type="category" dataKey="merchant" width={80} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number) => [formatCurrency(value), 'Spent']} cursor={{ fill: 'transparent' }} />
                  <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                    {topMerchants.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Monthly Trends (Income vs Expenses) */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold mb-4">Monthly Trends (Last 6 Months)</h2>
        {monthlyTrends.length === 0 ? (
          <div className="h-72 flex items-center justify-center text-gray-500">
            No trend data available
          </div>
        ) : (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthlyTrends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="income"
                  stroke="#10B981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorIncome)"
                  name="Income"
                />
                <Area
                  type="monotone"
                  dataKey="expenses"
                  stroke="#EF4444"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorExpenses)"
                  name="Expenses"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Recurring Transactions */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold mb-4">Recurring Subscriptions & Bills</h2>

        {recurring.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No recurring transactions detected yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  <th className="pb-3 pl-4">Merchant</th>
                  <th className="pb-3">Amount</th>
                  <th className="pb-3">Frequency</th>
                  <th className="pb-3">Next Due</th>
                  <th className="pb-3">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recurring.map((item, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="py-3 pl-4 font-medium text-gray-900">{item.merchant}</td>
                    <td className="py-3 text-gray-600">{formatCurrency(item.amount)}</td>
                    <td className="py-3">
                      <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                        {item.interval}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600">{item.next_date}</td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-green-500 h-1.5 rounded-full"
                            style={{ width: `${item.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-500">{Math.round(item.confidence * 100)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl text-white">
            <p className="text-blue-100 text-sm">Average Expense</p>
            <p className="text-3xl font-bold mt-1">{formatCurrency(summary.avg_expense)}</p>
            <p className="text-blue-200 text-sm mt-2">Per transaction this month</p>
          </div>
          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl text-white">
            <p className="text-purple-100 text-sm">Largest Expense</p>
            <p className="text-3xl font-bold mt-1">{formatCurrency(summary.largest_expense)}</p>
            <p className="text-purple-200 text-sm mt-2">Single transaction</p>
          </div>
          <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl text-white">
            <p className="text-orange-100 text-sm">Subscriptions</p>
            <p className="text-3xl font-bold mt-1">{recurring.length}</p>
            <p className="text-orange-200 text-sm mt-2">Recurring detected</p>
          </div>
        </div>
      )}
    </div>
  );
};
