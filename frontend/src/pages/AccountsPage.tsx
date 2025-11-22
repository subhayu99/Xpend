import React, { useState, useEffect } from 'react';
import { accountService, Account, AccountCreate } from '../services/accountService';

export const AccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAccount, setNewAccount] = useState<AccountCreate>({
    name: '',
    account_type: 'savings',
    bank_name: '',
    last_4_digits: '',
    opening_balance: 0
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const data = await accountService.getAll();
      setAccounts(data);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await accountService.create(newAccount);
      setShowAddForm(false);
      setNewAccount({ name: '', account_type: 'savings', bank_name: '', last_4_digits: '', opening_balance: 0 });
      loadAccounts();
    } catch (error) {
      console.error('Failed to create account:', error);
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading accounts...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Accounts</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors shadow-sm flex items-center gap-2"
        >
          <span>+</span> Add Account
        </button>
      </div>

      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-md">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Add New Account</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account Name</label>
                <input
                  type="text"
                  value={newAccount.name}
                  onChange={e => setNewAccount({...newAccount, name: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g. Main Savings"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Bank Name</label>
                  <input
                    type="text"
                    value={newAccount.bank_name}
                    onChange={e => setNewAccount({...newAccount, bank_name: e.target.value})}
                    className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    placeholder="e.g. HDFC"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={newAccount.account_type}
                    onChange={e => setNewAccount({...newAccount, account_type: e.target.value as 'savings' | 'current' | 'credit_card' | 'wallet'})}
                    className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="savings">Savings</option>
                    <option value="current">Current</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="wallet">Wallet</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Account Number (Last 4)</label>
                <input
                  type="text"
                  value={newAccount.last_4_digits}
                  onChange={e => setNewAccount({...newAccount, last_4_digits: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  placeholder="1234"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Opening Balance</label>
                <input
                  type="number"
                  value={newAccount.opening_balance}
                  onChange={e => setNewAccount({...newAccount, opening_balance: parseFloat(e.target.value)})}
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
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map(account => (
          <div key={account.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-lg text-gray-900">{account.name}</h3>
                <p className="text-sm text-gray-500">{account.bank_name} •••• {account.last_4_digits}</p>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                account.account_type === 'credit_card' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
              }`}>
                {account.account_type.replace('_', ' ')}
              </span>
            </div>
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-1">Current Balance</p>
              <p className={`text-2xl font-bold ${account.current_balance < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                ₹{Math.abs(account.current_balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                {account.current_balance < 0 && <span className="text-sm font-normal text-red-500 ml-1">(Dr)</span>}
              </p>
            </div>
          </div>
        ))}
        
        {accounts.length === 0 && (
          <div className="col-span-full text-center py-12 bg-white rounded-xl border border-dashed border-gray-300">
            <p className="text-gray-500 mb-2">No accounts found</p>
            <button 
              onClick={() => setShowAddForm(true)}
              className="text-primary-600 font-medium hover:text-primary-700"
            >
              Create your first account
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
