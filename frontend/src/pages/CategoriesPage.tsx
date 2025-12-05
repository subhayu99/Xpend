import React, { useState, useEffect } from 'react';
import { categoryService, Category, CategoryCreate } from '../services/categoryService';

export const CategoriesPage: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCategory, setNewCategory] = useState<CategoryCreate>({
    name: '',
    type: 'expense',
    icon: '',
    color: '#000000'
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await categoryService.getAll();
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await categoryService.create(newCategory);
      setShowAddForm(false);
      setNewCategory({ name: '', type: 'expense', icon: '', color: '#000000' });
      loadCategories();
    } catch (error) {
      console.error('Failed to create category:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this category?')) {
      try {
        await categoryService.delete(id);
        loadCategories();
      } catch (error) {
        console.error('Failed to delete category:', error);
      }
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading categories...</div>;

  const expenseCategories = categories.filter(c => c.type === 'expense');
  const incomeCategories = categories.filter(c => c.type === 'income');

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors shadow-sm flex items-center gap-2"
        >
          <span>+</span> Add Category
        </button>
      </div>

      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded-xl shadow-xl w-full max-w-md">
            <h2 className="text-xl font-bold mb-4 text-gray-900">New Category</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newCategory.name}
                  onChange={e => setNewCategory({...newCategory, name: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  required
                  placeholder="e.g. Groceries"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={newCategory.type}
                  onChange={e => setNewCategory({...newCategory, type: e.target.value as 'income' | 'expense'})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Icon (Emoji)</label>
                <input
                  type="text"
                  value={newCategory.icon || ''}
                  onChange={e => setNewCategory({...newCategory, icon: e.target.value})}
                  className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g. 🍔"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={newCategory.color || '#000000'}
                    onChange={e => setNewCategory({...newCategory, color: e.target.value})}
                    className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-500">{newCategory.color}</span>
                </div>
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
                  Create Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Expense Categories */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4 text-red-600 flex items-center gap-2">
            <span>📉</span> Expense Categories
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {expenseCategories.map(category => (
              <div key={category.id} className="p-3 rounded-lg border border-gray-100 hover:border-gray-300 hover:shadow-sm transition-all flex items-center justify-between group">
                <div className="flex items-center gap-3">
                  <span className="text-2xl bg-gray-50 w-10 h-10 flex items-center justify-center rounded-full">{category.icon || '📝'}</span>
                  <span className="font-medium text-gray-900" style={{ color: category.color || 'inherit' }}>
                    {category.name}
                  </span>
                </div>
                <button
                    onClick={() => handleDelete(category.id)}
                    className="text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                    title="Delete category"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
              </div>
            ))}
          </div>
        </div>

        {/* Income Categories */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold mb-4 text-green-600 flex items-center gap-2">
            <span>📈</span> Income Categories
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {incomeCategories.map(category => (
              <div key={category.id} className="p-3 rounded-lg border border-gray-100 hover:border-gray-300 hover:shadow-sm transition-all flex items-center justify-between group">
                <div className="flex items-center gap-3">
                  <span className="text-2xl bg-gray-50 w-10 h-10 flex items-center justify-center rounded-full">{category.icon || '💰'}</span>
                  <span className="font-medium text-gray-900" style={{ color: category.color || 'inherit' }}>
                    {category.name}
                  </span>
                </div>
                <button
                    onClick={() => handleDelete(category.id)}
                    className="text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity p-1"
                    title="Delete category"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
