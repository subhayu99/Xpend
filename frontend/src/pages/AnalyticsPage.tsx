import React, { useState, useEffect } from 'react';
import { analyticsService, RecurringTransaction, TopMerchant } from '../services/analyticsService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const AnalyticsPage: React.FC = () => {
  const [recurring, setRecurring] = useState<RecurringTransaction[]>([]);
  const [topMerchants, setTopMerchants] = useState<TopMerchant[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [recurringData, merchantsData] = await Promise.all([
          analyticsService.getRecurring(),
          analyticsService.getTopMerchants(5)
        ]);
        setRecurring(recurringData);
        setTopMerchants(merchantsData);
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <div className="p-8 text-center">Loading insights...</div>;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Spending Insights</h1>

      {/* Top Merchants Chart */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold mb-6">Top Merchants</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topMerchants} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="merchant" width={100} tick={{fontSize: 12}} />
              <Tooltip 
                formatter={(value: number) => [`₹${value.toFixed(2)}`, 'Spent']}
                cursor={{fill: 'transparent'}}
              />
              <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                {topMerchants.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
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
                    <td className="py-3 text-gray-600">₹{item.amount.toFixed(2)}</td>
                    <td className="py-3">
                      <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">
                        {item.interval}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600">{item.next_date}</td>
                    <td className="py-3">
                      <div className="w-24 bg-gray-200 rounded-full h-1.5">
                        <div 
                          className="bg-green-500 h-1.5 rounded-full" 
                          style={{ width: `${item.confidence * 100}%` }}
                        ></div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
