import React, { useState, useEffect } from 'react';
import {
  merchantService,
  Merchant,
  MerchantCreate,
  MerchantGroup,
  UnextractedAccountInfo,
} from '../services/merchantService';
import { categoryService, Category } from '../services/categoryService';

export const MerchantsPage: React.FC = () => {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [uncategorizedGroups, setUncategorizedGroups] = useState<MerchantGroup[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'uncategorized' | 'mappings'>('uncategorized');
  const [showAddForm, setShowAddForm] = useState(false);
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);
  const [categorizingGroup, setCategorizingGroup] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [newMerchant, setNewMerchant] = useState<MerchantCreate>({
    normalized_name: '',
    patterns: [],
    category_id: undefined,
    fuzzy_threshold: 0.85,
  });
  const [patternInput, setPatternInput] = useState('');
  const [totalUncategorized, setTotalUncategorized] = useState(0);
  const [unextractedAccounts, setUnextractedAccounts] = useState<UnextractedAccountInfo[]>([]);
  const [showExtractDropdown, setShowExtractDropdown] = useState(false);
  const [extracting, setExtracting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [merchantsRes, groupsRes, categoriesData, unextractedRes] = await Promise.all([
        merchantService.getAll({ limit: 100 }),
        merchantService.getUncategorizedGroups(true, 100),
        categoryService.getAll(),
        merchantService.getUnextractedAccounts(),
      ]);
      setMerchants(merchantsRes.items);
      setUncategorizedGroups(groupsRes.groups);
      setTotalUncategorized(groupsRes.total_transactions);
      setCategories(categoriesData);
      setUnextractedAccounts(unextractedRes.accounts);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractMerchants = async (accountId: string) => {
    setExtracting(true);
    setShowExtractDropdown(false);
    try {
      const result = await merchantService.extractMerchants(accountId);
      if (result.transactions_updated > 0) {
        alert(`Extracted merchants for ${result.transactions_updated} transactions from ${result.bank_name || 'account'}`);
        loadData();
      } else {
        alert('No new merchants to extract');
      }
    } catch (error) {
      console.error('Failed to extract merchants:', error);
      alert('Failed to extract merchants');
    } finally {
      setExtracting(false);
    }
  };

  const handleCategorize = async (merchantName: string, categoryId: string) => {
    try {
      const result = await merchantService.bulkCategorize({
        merchant_name: merchantName,
        category_id: categoryId,
        create_mapping: true,
      });
      setCategorizingGroup(null);
      setSelectedCategory('');
      loadData();
      alert(`Categorized ${result.transactions_updated} transactions`);
    } catch (error) {
      console.error('Failed to categorize:', error);
      alert('Failed to categorize transactions');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await merchantService.create(newMerchant, true);
      setShowAddForm(false);
      setNewMerchant({
        normalized_name: '',
        patterns: [],
        category_id: undefined,
        fuzzy_threshold: 0.85,
      });
      setPatternInput('');
      loadData();
    } catch (error) {
      console.error('Failed to create merchant:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this merchant mapping?')) {
      try {
        await merchantService.delete(id);
        loadData();
      } catch (error) {
        console.error('Failed to delete merchant:', error);
      }
    }
  };

  const handleApplyMapping = async (id: string) => {
    try {
      const result = await merchantService.applyMapping(id, true);
      alert(result.message);
      loadData();
    } catch (error) {
      console.error('Failed to apply mapping:', error);
    }
  };

  const addPattern = () => {
    if (patternInput.trim() && !newMerchant.patterns?.includes(patternInput.trim())) {
      setNewMerchant({
        ...newMerchant,
        patterns: [...(newMerchant.patterns || []), patternInput.trim()],
      });
      setPatternInput('');
    }
  };

  const removePattern = (pattern: string) => {
    setNewMerchant({
      ...newMerchant,
      patterns: newMerchant.patterns?.filter((p) => p !== pattern) || [],
    });
  };

  const formatCurrency = (amount: number) => {
    const absAmount = Math.abs(amount);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(absAmount);
  };

  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString();

  if (loading)
    return <div className="p-8 text-center text-gray-500">Loading merchants...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Merchant Management</h1>
        <div className="flex items-center gap-3">
          {/* Extract Merchants Dropdown */}
          {unextractedAccounts.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setShowExtractDropdown(!showExtractDropdown)}
                disabled={extracting}
                className="bg-amber-100 text-amber-800 px-4 py-2 rounded-lg hover:bg-amber-200 transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50"
              >
                {extracting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Extracting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Re-extract
                    <span className="bg-amber-200 text-amber-900 px-1.5 py-0.5 rounded text-xs">
                      {unextractedAccounts.reduce((sum, a) => sum + a.count, 0)}
                    </span>
                  </>
                )}
              </button>

              {showExtractDropdown && (
                <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
                  <div className="p-2 border-b border-gray-100">
                    <p className="text-xs text-gray-500 px-2">
                      Select an account to re-extract merchant names
                    </p>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {unextractedAccounts.map((account) => (
                      <button
                        key={account.account_id}
                        onClick={() => handleExtractMerchants(account.account_id)}
                        className="w-full text-left px-4 py-2 hover:bg-gray-50 flex justify-between items-center"
                      >
                        <div>
                          <p className="font-medium text-gray-900">{account.account_name}</p>
                          {account.bank_name && (
                            <p className="text-xs text-gray-500">{account.bank_name}</p>
                          )}
                        </div>
                        <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-sm">
                          {account.count}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          <button
            onClick={() => {
              setNewMerchant({
                normalized_name: '',
                patterns: [],
                category_id: undefined,
                fuzzy_threshold: 0.85,
              });
              setShowAddForm(true);
            }}
            className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors shadow-sm flex items-center gap-2"
          >
            <span>+</span> Add Mapping
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('uncategorized')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'uncategorized'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Uncategorized
          {totalUncategorized > 0 && (
            <span className="ml-2 bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full text-xs">
              {totalUncategorized}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('mappings')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'mappings'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Mappings ({merchants.length})
        </button>
      </div>

      {/* Uncategorized Groups */}
      {activeTab === 'uncategorized' && (
        <div className="space-y-4">
          {uncategorizedGroups.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
              <div className="text-4xl mb-3">🎉</div>
              <h3 className="text-lg font-medium text-gray-900">All transactions categorized!</h3>
              <p className="text-gray-500 mt-1">Great job keeping your finances organized.</p>
            </div>
          ) : (
            <>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                <strong>Tip:</strong> Click on a merchant group to see all transactions, then assign a category.
                A merchant mapping will be created automatically for future transactions.
              </div>

              {uncategorizedGroups.map((group) => (
                <div
                  key={group.merchant_name}
                  className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
                >
                  {/* Group Header */}
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => setExpandedGroup(
                      expandedGroup === group.merchant_name ? null : group.merchant_name
                    )}
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-gray-900 text-lg">
                            {group.merchant_name}
                          </h3>
                          <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-sm">
                            {group.transaction_count} transactions
                          </span>
                        </div>
                        <div className="flex gap-4 mt-1 text-sm text-gray-500">
                          <span className={group.total_amount < 0 ? 'text-red-600' : 'text-green-600'}>
                            {group.total_amount < 0 ? '-' : '+'}{formatCurrency(group.total_amount)}
                          </span>
                          <span>
                            {formatDate(group.first_date)} - {formatDate(group.last_date)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {categorizingGroup === group.merchant_name ? (
                          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                            <select
                              value={selectedCategory}
                              onChange={(e) => setSelectedCategory(e.target.value)}
                              className="border-gray-300 rounded-lg text-sm focus:ring-primary-500 focus:border-primary-500"
                            >
                              <option value="">Select category</option>
                              {categories.map((cat) => (
                                <option key={cat.id} value={cat.id}>
                                  {cat.icon} {cat.name}
                                </option>
                              ))}
                            </select>
                            <button
                              onClick={() => {
                                if (selectedCategory) {
                                  handleCategorize(group.merchant_name, selectedCategory);
                                }
                              }}
                              disabled={!selectedCategory}
                              className="bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Apply
                            </button>
                            <button
                              onClick={() => {
                                setCategorizingGroup(null);
                                setSelectedCategory('');
                              }}
                              className="text-gray-500 hover:text-gray-700 p-1"
                            >
                              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setCategorizingGroup(group.merchant_name);
                              setSelectedCategory('');
                            }}
                            className="bg-primary-100 text-primary-700 px-4 py-2 rounded-lg hover:bg-primary-200 transition-colors text-sm font-medium"
                          >
                            Categorize
                          </button>
                        )}

                        <svg
                          className={`w-5 h-5 text-gray-400 transition-transform ${
                            expandedGroup === group.merchant_name ? 'transform rotate-180' : ''
                          }`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Transactions */}
                  {expandedGroup === group.merchant_name && group.transactions.length > 0 && (
                    <div className="border-t border-gray-100 bg-gray-50 p-4">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-500 border-b border-gray-200">
                              <th className="pb-2 font-medium">Date</th>
                              <th className="pb-2 font-medium">Description</th>
                              <th className="pb-2 font-medium">Account</th>
                              <th className="pb-2 font-medium text-right">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.transactions.map((tx) => (
                              <tr key={tx.id} className="border-b border-gray-100 last:border-0">
                                <td className="py-2 text-gray-600">{formatDate(tx.transaction_date)}</td>
                                <td className="py-2 text-gray-900 max-w-xs truncate">{tx.description}</td>
                                <td className="py-2 text-gray-600">{tx.account_name || 'Unknown'}</td>
                                <td className={`py-2 text-right font-medium ${tx.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                  {tx.amount < 0 ? '-' : '+'}{formatCurrency(tx.amount)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Merchant Mappings */}
      {activeTab === 'mappings' && (
        <div className="space-y-4">
          {merchants.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-100">
              <div className="text-4xl mb-3">📋</div>
              <h3 className="text-lg font-medium text-gray-900">No merchant mappings yet</h3>
              <p className="text-gray-500 mt-1">
                Categorize transactions from the Uncategorized tab to create mappings automatically.
              </p>
            </div>
          ) : (
            merchants.map((merchant) => (
              <div
                key={merchant.id}
                className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">
                        {merchant.normalized_name}
                      </h3>
                      {merchant.category && (
                        <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
                          {merchant.category.name}
                        </span>
                      )}
                    </div>
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {merchant.patterns.map((pattern, i) => (
                        <span
                          key={i}
                          className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs font-mono"
                        >
                          {pattern}
                        </span>
                      ))}
                    </div>
                    <div className="text-xs text-gray-400 mt-2">
                      Used {merchant.usage_count} times
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleApplyMapping(merchant.id)}
                      className="text-primary-600 hover:text-primary-800 p-1"
                      title="Apply to transactions"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDelete(merchant.id)}
                      className="text-gray-400 hover:text-red-600 p-1"
                      title="Delete mapping"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Add Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4 text-gray-900">New Merchant Mapping</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Normalized Name
                </label>
                <input
                  type="text"
                  value={newMerchant.normalized_name}
                  onChange={(e) =>
                    setNewMerchant({ ...newMerchant, normalized_name: e.target.value })
                  }
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  required
                  placeholder="e.g. Swiggy"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Patterns (for matching)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={patternInput}
                    onChange={(e) => setPatternInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addPattern())}
                    className="flex-1 border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    placeholder="e.g. SWIGGY*"
                  />
                  <button
                    type="button"
                    onClick={addPattern}
                    className="bg-gray-100 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Add
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Use * for wildcards. Press Enter to add.
                </p>
                <div className="flex gap-2 mt-2 flex-wrap">
                  {newMerchant.patterns?.map((pattern, i) => (
                    <span
                      key={i}
                      className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-sm font-mono flex items-center gap-1"
                    >
                      {pattern}
                      <button
                        type="button"
                        onClick={() => removePattern(pattern)}
                        className="text-blue-400 hover:text-blue-600"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Default Category
                </label>
                <select
                  value={newMerchant.category_id || ''}
                  onChange={(e) =>
                    setNewMerchant({
                      ...newMerchant,
                      category_id: e.target.value || undefined,
                    })
                  }
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="">No default category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.icon} {cat.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fuzzy Match Threshold ({Math.round((newMerchant.fuzzy_threshold || 0.85) * 100)}%)
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="1"
                  step="0.05"
                  value={newMerchant.fuzzy_threshold || 0.85}
                  onChange={(e) =>
                    setNewMerchant({
                      ...newMerchant,
                      fuzzy_threshold: parseFloat(e.target.value),
                    })
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500">
                  Higher = stricter matching, Lower = more lenient
                </p>
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
                  Create Mapping
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
