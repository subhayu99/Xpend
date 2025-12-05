import React, { useEffect, useState } from 'react';
import dashboardService, { DashboardData } from '../services/dashboardService';
import { transactionService, Transaction } from '../services/transactionService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#8dd1e1'];

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Details Modal State
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [detailsTitle, setDetailsTitle] = useState('');
  const [detailsTransactions, setDetailsTransactions] = useState<Transaction[]>([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const result = await dashboardService.getDashboardData();
      setData(result);
    } catch (error) {
      console.error('Failed to load dashboard data', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMonthClick = async (data: any) => {
    if (!data || !data.activePayload) return;
    const month = data.activePayload[0].payload.month; // "YYYY-MM"
    setDetailsTitle(`Transactions for ${month}`);
    setDetailsModalOpen(true);
    setLoadingDetails(true);
    try {
        const [year, m] = month.split('-');
        const startDate = `${month}-01`;
        const endDate = new Date(parseInt(year), parseInt(m), 0).toISOString().split('T')[0];
        
        const result = await transactionService.getAll({
            start_date: startDate,
            end_date: endDate,
            limit: 100
        });
        setDetailsTransactions(result.items);
    } catch (e) {
        console.error(e);
    } finally {
        setLoadingDetails(false);
    }
  };

  const handleCategoryClick = async (data: any) => {
      if (!data) return;
      setDetailsTitle(`Transactions for ${data.category_name}`);
      setDetailsModalOpen(true);
      setLoadingDetails(true);
      try {
          const today = new Date();
          const startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
          const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
          
          const result = await transactionService.getAll({
              category_id: data.category_id || undefined,
              start_date: startDate,
              end_date: endDate,
              limit: 100
          });
          setDetailsTransactions(result.items);
      } catch (e) {
          console.error(e);
      } finally {
          setLoadingDetails(false);
      }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading dashboard...</div>;
  if (!data) return <div className="p-8 text-center text-gray-500">Failed to load data</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500 mb-1">Total Balance</p>
          <p className="text-2xl font-bold text-gray-900">
            ₹{data.summary.total_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500 mb-1">Monthly Income</p>
          <p className="text-2xl font-bold text-green-600">
            +₹{data.summary.monthly_income.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500 mb-1">Monthly Expense</p>
          <p className="text-2xl font-bold text-red-600">
            -₹{data.summary.monthly_expense.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500 mb-1">Savings Rate</p>
          <p className={`text-2xl font-bold ${data.summary.savings_rate >= 20 ? 'text-green-600' : 'text-yellow-600'}`}>
            {data.summary.savings_rate.toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trend Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Income vs Expense</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.monthly_trend} onClick={handleMonthClick} style={{ cursor: 'pointer' }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip 
                  formatter={(value: number) => `₹${value.toLocaleString('en-IN')}`}
                />
                <Legend />
                <Bar dataKey="income" name="Income" fill="#10B981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="expense" name="Expense" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Spend Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Spending by Category</h3>
          <div className="h-80 flex items-center justify-center">
            {data.category_spend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.category_spend}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="amount"
                    nameKey="category_name"
                    onClick={handleCategoryClick}
                    style={{ cursor: 'pointer' }}
                  >
                    {data.category_spend.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => `₹${value.toLocaleString('en-IN')}`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500">No expense data for this month</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Recent Transactions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.recent_transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(tx.transaction_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{tx.description}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${
                    tx.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {tx.transaction_type === 'income' ? '+' : '-'}₹{Math.abs(tx.amount).toFixed(2)}
                  </td>
                </tr>
              ))}
              {data.recent_transactions.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                    No recent transactions
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Modal */}
      {detailsModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900">{detailsTitle}</h2>
                <button onClick={() => setDetailsModalOpen(false)} className="text-gray-500 hover:text-gray-700">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <div className="flex-1 overflow-y-auto">
                {loadingDetails ? (
                    <div className="text-center py-8">Loading transactions...</div>
                ) : detailsTransactions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">No transactions found.</div>
                ) : (
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50 sticky top-0">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {detailsTransactions.map((tx) => (
                                <tr key={tx.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(tx.transaction_date).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900">{tx.description}</td>
                                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${
                                        tx.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                                    }`}>
                                        {tx.transaction_type === 'income' ? '+' : '-'}₹{Math.abs(tx.amount).toFixed(2)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
