import React, { useState, useEffect } from 'react';
import { analyticsService, RecurringTransaction } from '../services/analyticsService';

export const RecurringPage: React.FC = () => {
  const [recurring, setRecurring] = useState<RecurringTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await analyticsService.getRecurring();
      setRecurring(data);
    } catch (error) {
      console.error('Failed to load recurring transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => `₹${Math.abs(amount).toLocaleString()}`;

  const getIntervalColor = (interval: string) => {
    switch (interval.toLowerCase()) {
      case 'weekly': return 'bg-purple-100 text-purple-700';
      case 'monthly': return 'bg-blue-100 text-blue-700';
      case 'quarterly': return 'bg-orange-100 text-orange-700';
      case 'yearly': return 'bg-green-100 text-green-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getDaysUntil = (nextDate: string) => {
    const next = new Date(nextDate);
    const today = new Date();
    const diff = Math.ceil((next.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const totalMonthly = recurring.reduce((sum, item) => {
    let multiplier = 1;
    switch (item.interval.toLowerCase()) {
      case 'weekly': multiplier = 4.33; break;
      case 'monthly': multiplier = 1; break;
      case 'quarterly': multiplier = 1/3; break;
      case 'yearly': multiplier = 1/12; break;
    }
    return sum + (item.amount * multiplier);
  }, 0);

  if (loading) {
    return <div className="p-8 text-center">Loading recurring transactions...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Recurring Subscriptions & Bills</h1>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Total Subscriptions</p>
          <p className="text-3xl font-bold text-gray-900">{recurring.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Est. Monthly Cost</p>
          <p className="text-3xl font-bold text-red-600">{formatCurrency(totalMonthly)}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Est. Yearly Cost</p>
          <p className="text-3xl font-bold text-red-600">{formatCurrency(totalMonthly * 12)}</p>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-sm text-blue-800 font-medium">How it works</p>
            <p className="text-sm text-blue-700">
              We automatically detect recurring payments by analyzing your transaction history.
              Transactions with similar amounts to the same merchant that occur at regular intervals
              are identified as subscriptions or recurring bills.
            </p>
          </div>
        </div>
      </div>

      {/* Recurring List */}
      {recurring.length === 0 ? (
        <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center">
          <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <p className="text-gray-500 mb-2">No recurring transactions detected yet.</p>
          <p className="text-sm text-gray-400">
            Add more transactions and we'll automatically detect recurring patterns.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Merchant</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Amount</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Frequency</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Last Paid</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Next Due</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {recurring.map((item, index) => {
                const daysUntil = getDaysUntil(item.next_date);
                const isUpcoming = daysUntil >= 0 && daysUntil <= 7;
                const isOverdue = daysUntil < 0;

                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                          <span className="text-primary-700 font-bold text-lg">
                            {item.merchant.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{item.merchant}</p>
                          <p className="text-xs text-gray-500">{item.transaction_count} transactions</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold text-gray-900">{formatCurrency(item.amount)}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getIntervalColor(item.interval)}`}>
                        {item.interval}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-gray-600">
                      {new Date(item.last_date).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`${isOverdue ? 'text-red-600' : isUpcoming ? 'text-orange-600' : 'text-gray-900'}`}>
                          {new Date(item.next_date).toLocaleDateString()}
                        </span>
                        {isOverdue && (
                          <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">
                            {Math.abs(daysUntil)}d overdue
                          </span>
                        )}
                        {isUpcoming && !isOverdue && (
                          <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs">
                            in {daysUntil}d
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              item.confidence >= 0.9 ? 'bg-green-500' :
                              item.confidence >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${item.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{Math.round(item.confidence * 100)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Upcoming Payments */}
      {recurring.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4">Upcoming Payments (Next 7 Days)</h2>
          <div className="space-y-3">
            {recurring
              .filter(item => {
                const daysUntil = getDaysUntil(item.next_date);
                return daysUntil >= 0 && daysUntil <= 7;
              })
              .sort((a, b) => new Date(a.next_date).getTime() - new Date(b.next_date).getTime())
              .map((item, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-orange-200 flex items-center justify-center">
                      <span className="text-orange-700 font-bold">
                        {item.merchant.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{item.merchant}</p>
                      <p className="text-xs text-gray-500">
                        Due {new Date(item.next_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <span className="font-bold text-orange-700">{formatCurrency(item.amount)}</span>
                </div>
              ))
            }
            {recurring.filter(item => {
              const daysUntil = getDaysUntil(item.next_date);
              return daysUntil >= 0 && daysUntil <= 7;
            }).length === 0 && (
              <p className="text-gray-500 text-center py-4">No payments due in the next 7 days</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
