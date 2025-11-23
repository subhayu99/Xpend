import React, { useState, useEffect } from 'react';
import { budgetService, BudgetProgress } from '../services/budgetService';
import { categoryService, Category } from '../services/categoryService';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export const BudgetsPage: React.FC = () => {
  const [budgets, setBudgets] = useState<BudgetProgress[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingBudget, setEditingBudget] = useState<BudgetProgress | null>(null);

  // Period selection
  const currentDate = new Date();
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());

  // Form state
  const [selectedCategory, setSelectedCategory] = useState('');
  const [amount, setAmount] = useState('');

  useEffect(() => {
    loadData();
  }, [selectedMonth, selectedYear]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [budgetData, categoryData] = await Promise.all([
        budgetService.getAll(selectedMonth, selectedYear),
        categoryService.getAll()
      ]);
      setBudgets(budgetData);
      setCategories(categoryData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await budgetService.create({
        category_id: selectedCategory,
        amount: parseFloat(amount),
        month: selectedMonth,
        year: selectedYear
      });
      setShowAddModal(false);
      setAmount('');
      setSelectedCategory('');
      loadData();
    } catch (error) {
      console.error('Failed to create budget:', error);
      alert('Failed to create budget');
    }
  };

  const handleUpdateBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingBudget) return;
    try {
      await budgetService.update(editingBudget.id, parseFloat(amount));
      setEditingBudget(null);
      setAmount('');
      loadData();
    } catch (error) {
      console.error('Failed to update budget:', error);
      alert('Failed to update budget');
    }
  };

  const handleDeleteBudget = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this budget?')) return;
    try {
      await budgetService.delete(id);
      loadData();
    } catch (error) {
      console.error('Failed to delete budget:', error);
    }
  };

  const openEditModal = (budget: BudgetProgress) => {
    setEditingBudget(budget);
    setAmount(budget.amount.toString());
  };

  const getCategoryName = (id: string) => {
    return categories.find(c => c.id === id)?.name || 'Unknown Category';
  };

  const getCategoryIcon = (id: string) => {
    return categories.find(c => c.id === id)?.icon || '📊';
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

  // Calculate summary
  const totalBudget = budgets.reduce((sum, b) => sum + b.amount, 0);
  const totalSpent = budgets.reduce((sum, b) => sum + b.spent, 0);
  const overallPercentage = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0;

  // Filter categories that don't have budgets yet
  const availableCategories = categories.filter(
    cat => !budgets.some(b => b.category_id === cat.id)
  );

  if (loading) return <div className="p-8 text-center">Loading budgets...</div>;

  return (
    <div className="space-y-6">
      {/* Header with Month Navigation */}
      <div className="flex justify-between items-center flex-wrap gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Monthly Budgets</h1>

        <div className="flex items-center gap-4">
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

          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
          >
            + Set Budget
          </button>
        </div>
      </div>

      {/* Summary Card */}
      {budgets.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex flex-wrap gap-8 items-center">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Budget</p>
              <p className="text-2xl font-bold text-gray-900">₹{totalBudget.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Spent</p>
              <p className={`text-2xl font-bold ${totalSpent > totalBudget ? 'text-red-600' : 'text-gray-900'}`}>
                ₹{totalSpent.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">Remaining</p>
              <p className={`text-2xl font-bold ${totalBudget - totalSpent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ₹{(totalBudget - totalSpent).toLocaleString()}
              </p>
            </div>
            <div className="flex-1 min-w-[200px]">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-500">Overall Usage</span>
                <span className="font-medium">{overallPercentage.toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    overallPercentage > 100 ? 'bg-red-500' :
                    overallPercentage > 80 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(overallPercentage, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Budget Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {budgets.map(budget => (
          <div key={budget.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow group">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{getCategoryIcon(budget.category_id)}</span>
                <div>
                  <h3 className="font-semibold text-gray-900">{getCategoryName(budget.category_id)}</h3>
                  <p className="text-sm text-gray-500">Monthly Limit</p>
                </div>
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => openEditModal(budget)}
                  className="p-1 text-gray-400 hover:text-primary-600"
                  title="Edit budget"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <button
                  onClick={() => handleDeleteBudget(budget.id)}
                  className="p-1 text-gray-400 hover:text-red-500"
                  title="Delete budget"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="mb-2">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">₹{budget.spent.toLocaleString()} spent</span>
                <span className="font-medium">₹{budget.amount.toLocaleString()}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    budget.percentage > 100 ? 'bg-red-500' :
                    budget.percentage > 80 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(budget.percentage, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">{budget.percentage.toFixed(0)}% used</span>
              {budget.remaining >= 0 ? (
                <span className="text-green-600 font-medium">₹{budget.remaining.toLocaleString()} left</span>
              ) : (
                <span className="text-red-600 font-medium">Over by ₹{Math.abs(budget.remaining).toLocaleString()}</span>
              )}
            </div>
          </div>
        ))}

        {budgets.length === 0 && (
          <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <p className="text-gray-500 mb-2">No budgets set for {MONTHS[selectedMonth - 1]} {selectedYear}</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Set your first budget
            </button>
          </div>
        )}
      </div>

      {/* Add Budget Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-xl font-bold mb-4">Set Category Budget</h2>
            <form onSubmit={handleCreateBudget} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                  required
                >
                  <option value="">Select Category</option>
                  {availableCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                  ))}
                </select>
                {availableCategories.length === 0 && (
                  <p className="text-sm text-yellow-600 mt-1">All categories have budgets set</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Limit</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    required
                    min="1"
                    placeholder="10000"
                  />
                </div>
              </div>

              <p className="text-sm text-gray-500">
                For: {MONTHS[selectedMonth - 1]} {selectedYear}
              </p>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setShowAddModal(false); setAmount(''); setSelectedCategory(''); }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  disabled={availableCategories.length === 0}
                >
                  Save Budget
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Budget Modal */}
      {editingBudget && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-xl font-bold mb-4">Edit Budget</h2>
            <form onSubmit={handleUpdateBudget} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <p className="text-lg font-medium text-gray-900">
                  {getCategoryIcon(editingBudget.category_id)} {getCategoryName(editingBudget.category_id)}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Limit</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
                    required
                    min="1"
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => { setEditingBudget(null); setAmount(''); }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Update Budget
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
