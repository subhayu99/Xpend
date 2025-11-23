import React, { useState, useEffect } from 'react';
import {
  merchantService,
  Merchant,
  MerchantCreate,
  UnmappedMerchant,
} from '../services/merchantService';
import { categoryService, Category } from '../services/categoryService';

export const MerchantsPage: React.FC = () => {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [unmappedMerchants, setUnmappedMerchants] = useState<UnmappedMerchant[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'mapped' | 'unmapped'>('unmapped');
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedUnmapped, setSelectedUnmapped] = useState<UnmappedMerchant | null>(null);
  const [newMerchant, setNewMerchant] = useState<MerchantCreate>({
    normalized_name: '',
    patterns: [],
    category_id: undefined,
    fuzzy_threshold: 0.85,
  });
  const [patternInput, setPatternInput] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [merchantsRes, unmappedRes, categoriesData] = await Promise.all([
        merchantService.getAll({ limit: 100 }),
        merchantService.getUnmapped(50),
        categoryService.getAll(),
      ]);
      setMerchants(merchantsRes.items);
      setUnmappedMerchants(unmappedRes.items);
      setCategories(categoriesData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFromUnmapped = (unmapped: UnmappedMerchant) => {
    setSelectedUnmapped(unmapped);
    setNewMerchant({
      normalized_name: unmapped.raw_name,
      patterns: [unmapped.raw_name],
      category_id: undefined,
      fuzzy_threshold: 0.85,
    });
    setPatternInput(unmapped.raw_name);
    setShowAddForm(true);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await merchantService.create(newMerchant, true);
      setShowAddForm(false);
      setSelectedUnmapped(null);
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
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading)
    return <div className="p-8 text-center text-gray-500">Loading merchants...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Merchant Mappings</h1>
        <button
          onClick={() => {
            setSelectedUnmapped(null);
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

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('unmapped')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'unmapped'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Unmapped ({unmappedMerchants.length})
        </button>
        <button
          onClick={() => setActiveTab('mapped')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'mapped'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Mapped ({merchants.length})
        </button>
      </div>

      {/* Unmapped Merchants */}
      {activeTab === 'unmapped' && (
        <div className="space-y-4">
          {unmappedMerchants.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              All merchants are mapped! Great job.
            </div>
          ) : (
            unmappedMerchants.map((unmapped) => (
              <div
                key={unmapped.raw_name}
                className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{unmapped.raw_name}</h3>
                    <div className="flex gap-4 mt-1 text-sm text-gray-500">
                      <span>{unmapped.transaction_count} transactions</span>
                      <span>{formatCurrency(unmapped.total_amount)} total</span>
                    </div>
                    {unmapped.sample_descriptions.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-gray-400">Sample descriptions:</p>
                        <ul className="text-xs text-gray-600 mt-1">
                          {unmapped.sample_descriptions.slice(0, 2).map((desc, i) => (
                            <li key={i} className="truncate">
                              {desc}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => handleCreateFromUnmapped(unmapped)}
                    className="bg-primary-100 text-primary-700 px-3 py-1 rounded-lg hover:bg-primary-200 transition-colors text-sm font-medium"
                  >
                    Create Mapping
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Mapped Merchants */}
      {activeTab === 'mapped' && (
        <div className="space-y-4">
          {merchants.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No merchant mappings yet. Create one from the Unmapped tab.
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

      {/* Add/Edit Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4 text-gray-900">
              {selectedUnmapped ? 'Create Merchant Mapping' : 'New Merchant Mapping'}
            </h2>
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
                  onClick={() => {
                    setShowAddForm(false);
                    setSelectedUnmapped(null);
                  }}
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
