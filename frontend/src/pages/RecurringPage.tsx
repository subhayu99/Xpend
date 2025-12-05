import React, { useState, useEffect } from 'react';
import {
  analyticsService,
  RecurringTransaction,
  RecurringListResponse,
} from '../services/analyticsService';

export const RecurringPage: React.FC = () => {
  const [data, setData] = useState<RecurringListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'suggestions' | 'confirmed'>('suggestions');
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [editingItem, setEditingItem] = useState<RecurringTransaction | null>(null);

  // Edit form state
  const [editForm, setEditForm] = useState({
    expected_amount: 0,
    interval: '',
    next_expected_date: '',
  });

  // Manual Rule State
  const [showAddForm, setShowAddForm] = useState(false);
  const [newRule, setNewRule] = useState({
    merchant_name: '',
    expected_amount: 0,
    interval: 'Monthly',
    next_expected_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await analyticsService.getRecurring();
      setData(result);
    } catch (error) {
      console.error('Failed to load recurring transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (item: RecurringTransaction) => {
    // If editing, use edited values, otherwise use item values
    const isEditing = editingItem?.merchant === item.merchant;
    const amount = isEditing ? editForm.expected_amount : item.amount;
    const interval = isEditing ? editForm.interval : item.interval;
    const nextDate = isEditing ? editForm.next_expected_date : item.next_date;

    try {
      await analyticsService.confirmRecurring({
        merchant_name: item.merchant,
        expected_amount: amount,
        amount_min: item.amount_min,
        amount_max: item.amount_max,
        is_variable_amount: item.is_variable_amount,
        interval: interval,
        avg_days: item.avg_days,
        confidence: item.confidence,
        last_transaction_date: item.last_date,
        next_expected_date: nextDate,
        transaction_count: item.transaction_count,
      });
      setEditingItem(null);
      loadData();
    } catch (error) {
      console.error('Failed to confirm recurring:', error);
    }
  };

  const handleCreateManual = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await analyticsService.confirmRecurring({
        merchant_name: newRule.merchant_name,
        expected_amount: newRule.expected_amount,
        amount_min: newRule.expected_amount,
        amount_max: newRule.expected_amount,
        is_variable_amount: false,
        interval: newRule.interval,
        avg_days: 30, // Default
        confidence: 1.0,
        transaction_count: 0,
        next_expected_date: newRule.next_expected_date,
      });
      setShowAddForm(false);
      setNewRule({
        merchant_name: '',
        expected_amount: 0,
        interval: 'Monthly',
        next_expected_date: new Date().toISOString().split('T')[0],
      });
      loadData();
    } catch (error) {
      console.error('Failed to create recurring rule:', error);
    }
  };

  const handleDismiss = async (merchantName: string) => {
    try {
      await analyticsService.dismissRecurring(merchantName);
      loadData();
    } catch (error) {
      console.error('Failed to dismiss recurring:', error);
    }
  };

  const handleDelete = async (ruleId: string) => {
    try {
      await analyticsService.deleteRecurringRule(ruleId);
      loadData();
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const startEditing = (item: RecurringTransaction) => {
    setEditingItem(item);
    setEditForm({
      expected_amount: item.amount,
      interval: item.interval,
      next_expected_date: item.next_date,
    });
  };

  const cancelEditing = () => {
    setEditingItem(null);
  };

  const toggleExpand = (merchant: string) => {
    if (expandedItem === merchant) {
      setExpandedItem(null);
    } else {
      setExpandedItem(merchant);
    }
  };

  const formatCurrency = (amount: number) => `₹${Math.abs(amount).toLocaleString()}`;

  const getIntervalColor = (interval: string) => {
    switch (interval.toLowerCase()) {
      case 'weekly': return 'bg-purple-100 text-purple-700';
      case 'bi-weekly': return 'bg-indigo-100 text-indigo-700';
      case 'monthly': return 'bg-blue-100 text-blue-700';
      case 'quarterly': return 'bg-orange-100 text-orange-700';
      case 'yearly': return 'bg-green-100 text-green-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Confirmed</span>;
      case 'suggested':
        return <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">Suggested</span>;
      default: return null;
    }
  };

  const getDaysUntil = (nextDate: string) => {
    const next = new Date(nextDate);
    const today = new Date();
    const diff = Math.ceil((next.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const confirmedItems = data?.confirmed || [];
  const suggestions = data?.suggestions.filter((s) => s.status !== 'confirmed') || [];

  const totalMonthly = confirmedItems.reduce((sum, item) => {
    let multiplier = 1;
    switch (item.interval.toLowerCase()) {
      case 'weekly': multiplier = 4.33; break;
      case 'bi-weekly': multiplier = 2.17; break;
      case 'monthly': multiplier = 1; break;
      case 'quarterly': multiplier = 1 / 3; break;
      case 'yearly': multiplier = 1 / 12; break;
    }
    return sum + item.expected_amount * multiplier;
  }, 0);

  if (loading) return <div className="p-8 text-center">Loading recurring transactions...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Recurring Subscriptions & Bills</h1>
        <div className="flex gap-2">
            <button 
                onClick={() => setShowAddForm(true)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
            >
                <span>+</span> Add Manual Rule
            </button>
            <button onClick={loadData} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
            </button>
        </div>
      </div>

      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-md">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Add Recurring Rule</h2>
            <form onSubmit={handleCreateManual} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Merchant Name</label>
                <input
                  type="text"
                  value={newRule.merchant_name}
                  onChange={e => setNewRule({...newRule, merchant_name: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  required
                  placeholder="e.g. Netflix"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expected Amount</label>
                <input
                  type="number"
                  value={newRule.expected_amount}
                  onChange={e => setNewRule({...newRule, expected_amount: parseFloat(e.target.value)})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
                <select
                  value={newRule.interval}
                  onChange={e => setNewRule({...newRule, interval: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="Weekly">Weekly</option>
                  <option value="Bi-weekly">Bi-weekly</option>
                  <option value="Monthly">Monthly</option>
                  <option value="Quarterly">Quarterly</option>
                  <option value="Yearly">Yearly</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Next Due Date</label>
                <input
                  type="date"
                  value={newRule.next_expected_date}
                  onChange={e => setNewRule({...newRule, next_expected_date: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  required
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm"
                >
                  Create Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Confirmed Subscriptions</p>
          <p className="text-3xl font-bold text-green-600">{confirmedItems.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Pending Review</p>
          <p className="text-3xl font-bold text-amber-600">{suggestions.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Est. Monthly Cost</p>
          <p className="text-3xl font-bold text-red-600">{formatCurrency(totalMonthly)}</p>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <p className="text-sm text-gray-500">Dismissed</p>
          <p className="text-3xl font-bold text-gray-400">{data?.dismissed_count || 0}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('suggestions')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'suggestions' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Suggestions ({suggestions.length})
        </button>
        <button
          onClick={() => setActiveTab('confirmed')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'confirmed' ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Confirmed ({confirmedItems.length})
        </button>
      </div>

      {/* Suggestions Tab */}
      {activeTab === 'suggestions' && (
        <div className="space-y-3">
          {suggestions.length === 0 ? (
            <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center">
              <p className="text-gray-500">No pending suggestions!</p>
            </div>
          ) : (
            suggestions.map((item, index) => {
              const daysUntil = getDaysUntil(item.next_date);
              const isEditing = editingItem?.merchant === item.merchant;
              const isExpanded = expandedItem === item.merchant;

              return (
                <div key={index} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                        <span className="text-amber-700 font-bold text-xl">{item.merchant.charAt(0).toUpperCase()}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-gray-900">{item.merchant}</p>
                          {getStatusBadge(item.status)}
                        </div>
                        
                        {isEditing ? (
                          <div className="mt-3 space-y-3 bg-gray-50 p-3 rounded-lg border border-gray-200">
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Amount</label>
                                <input
                                  type="number"
                                  value={editForm.expected_amount}
                                  onChange={(e) => setEditForm({...editForm, expected_amount: parseFloat(e.target.value)})}
                                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Frequency</label>
                                <select
                                  value={editForm.interval}
                                  onChange={(e) => setEditForm({...editForm, interval: e.target.value})}
                                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                                >
                                  <option value="Weekly">Weekly</option>
                                  <option value="Bi-weekly">Bi-weekly</option>
                                  <option value="Monthly">Monthly</option>
                                  <option value="Quarterly">Quarterly</option>
                                  <option value="Yearly">Yearly</option>
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Next Due Date</label>
                                <input
                                  type="date"
                                  value={editForm.next_expected_date}
                                  onChange={(e) => setEditForm({...editForm, next_expected_date: e.target.value})}
                                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded"
                                />
                              </div>
                            </div>
                            <div className="flex justify-end gap-2 mt-2">
                              <button onClick={cancelEditing} className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                              <button onClick={() => handleConfirm(item)} className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">Save & Confirm</button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-lg font-bold text-gray-900">
                                {item.is_variable_amount
                                  ? `${formatCurrency(item.amount_min)}-${formatCurrency(item.amount_max)}`
                                  : formatCurrency(item.amount)}
                              </span>
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getIntervalColor(item.interval)}`}>
                                {item.interval}
                              </span>
                            </div>
                            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                              <button onClick={() => toggleExpand(item.merchant)} className="text-blue-600 hover:underline flex items-center gap-1">
                                {item.transaction_count} transactions
                                <svg className={`w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                              </button>
                              <span>Next: {new Date(item.next_date).toLocaleDateString()}</span>
                            </div>
                          </>
                        )}

                        {/* Transaction History */}
                        {isExpanded && (
                          <div className="mt-3 bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Transaction History</p>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                              {item.transactions?.map((tx) => (
                                <div key={tx.id} className="flex justify-between text-sm">
                                  <span className="text-gray-600">{new Date(tx.date).toLocaleDateString()}</span>
                                  <span className="font-medium text-gray-900">{formatCurrency(tx.amount)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {!isEditing && (
                      <div className="flex items-center gap-2 ml-4">
                         <button onClick={() => startEditing(item)} className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50" title="Edit">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button onClick={() => handleConfirm(item)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg" title="Confirm">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </button>
                        <button onClick={() => handleDismiss(item.merchant)} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Dismiss">
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Confirmed Tab */}
      {activeTab === 'confirmed' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {confirmedItems.length === 0 ? (
             <div className="p-8 text-center text-gray-500">No confirmed recurring expenses yet.</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Merchant</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Amount</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Frequency</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Next Due</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {confirmedItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                          <span className="text-green-700 font-bold text-lg">{item.merchant_name.charAt(0).toUpperCase()}</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{item.merchant_name}</p>
                          <p className="text-xs text-gray-500">{item.transaction_count} transactions</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4 font-semibold text-gray-900">
                      {item.is_variable_amount && item.amount_min && item.amount_max
                        ? `${formatCurrency(item.amount_min)}-${formatCurrency(item.amount_max)}`
                        : formatCurrency(item.expected_amount)}
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getIntervalColor(item.interval)}`}>
                        {item.interval}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      {item.next_expected_date ? new Date(item.next_expected_date).toLocaleDateString() : '-'}
                    </td>
                    <td className="py-4 px-4">
                      <button onClick={() => handleDelete(item.id)} className="text-gray-400 hover:text-red-600">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
