import React, { useState, useEffect } from 'react';
import { transactionService, Transaction, TransactionCreate, TransactionFilters } from '../services/transactionService';
import { accountService, Account } from '../services/accountService';
import { categoryService, Category } from '../services/categoryService';
import { transferService, PotentialTransfer } from '../services/transferService';
import { EditTransactionModal } from '../components/EditTransactionModal';
import { AddTransactionModal } from '../components/AddTransactionModal';

export const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  
  // Parsing State
  const [parsedTransactions, setParsedTransactions] = useState<any[]>([]);
  const [detectedStructure, setDetectedStructure] = useState<any>(null);
  const [templateFound, setTemplateFound] = useState(false);
  const [saveTemplate, setSaveTemplate] = useState(false);
  const [uploadedFileType, setUploadedFileType] = useState<string>('');
  
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  
  // Transfer Detection State
  const [potentialTransfers, setPotentialTransfers] = useState<PotentialTransfer[]>([]);
  const [showTransfers, setShowTransfers] = useState(false);
  const [detectingTransfers, setDetectingTransfers] = useState(false);
  
  // Filter State
  const [filters, setFilters] = useState<TransactionFilters>({
    account_id: undefined,
    category_id: undefined,
    transaction_type: undefined,
    start_date: undefined,
    end_date: undefined,
    search: undefined,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [txData, accData, catData] = await Promise.all([
        transactionService.getAll(filters),
        accountService.getAll(),
        categoryService.getAll(),
      ]);
      setTransactions(txData);
      setAccounts(accData);
      setCategories(catData);
      if (accData.length > 0 && !selectedAccount) {
        setSelectedAccount(accData[0].id);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Reload when filters change
  useEffect(() => {
    if (!loading) {
      loadData();
    }
  }, [filters]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    if (!selectedAccount) {
        alert("Please select an account first");
        return;
    }
    
    const file = e.target.files[0];
    const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
    setUploadedFileType(fileExt);
    
    setUploading(true);
    try {
      const result = await transactionService.uploadStatement(file, selectedAccount);
      setParsedTransactions(result.transactions);
      setDetectedStructure(result.detected_structure);
      setTemplateFound(result.template_found);
      
      if (!result.template_found && result.detected_structure) {
        setSaveTemplate(true);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to parse file');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveParsed = async () => {
    if (!selectedAccount) return;

    try {
      const transactionsToCreate: TransactionCreate[] = parsedTransactions.map(tx => ({
        ...tx,
        account_id: selectedAccount,
      }));
      
      await transactionService.createBulk(transactionsToCreate);
      
      if (saveTemplate && detectedStructure) {
        await transactionService.saveTemplate(selectedAccount, uploadedFileType, detectedStructure);
      }
      
      setParsedTransactions([]);
      setDetectedStructure(null);
      loadData(); 
      alert('Transactions saved successfully!');
    } catch (error) {
      console.error('Failed to save transactions:', error);
      alert('Failed to save transactions');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) return;
    try {
      await transactionService.delete(id);
      loadData();
    } catch (error) {
      console.error('Failed to delete transaction:', error);
    }
  };

  const handleUpdateSuccess = () => {
    setEditingTransaction(null);
    loadData();
  };
  
  const handleDetectTransfers = async () => {
    setDetectingTransfers(true);
    try {
      const detected = await transferService.detectPotential(2);
      setPotentialTransfers(detected);
      setShowTransfers(true);
      if (detected.length === 0) {
        alert('No potential transfers found!');
      }
    } catch (error) {
      console.error('Failed to detect transfers:', error);
      alert('Failed to detect transfers');
    } finally {
      setDetectingTransfers(false);
    }
  };
  
  const handleConfirmTransfer = async (transfer: PotentialTransfer) => {
    try {
      await transferService.createTransfer(
        transfer.debit_transaction.id,
        transfer.credit_transaction.id,
        transfer.confidence_score
      );
      alert('Transfer linked successfully!');
      loadData();
      handleDetectTransfers(); // Refresh potential transfers
    } catch (error) {
      console.error('Failed to link transfer:', error);
      alert('Failed to link transfer');
    }
  };
  
  const handleExportCSV = async () => {
    try {
      const { exportService } = await import('../services/exportService');
      await exportService.exportTransactionsCSV({
        account_id: filters.account_id,
        category_id: filters.category_id,
        start_date: filters.start_date,
        end_date: filters.end_date,
      });
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export transactions');
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading transactions...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>

      {/* Upload Section */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Manage Transactions</h2>
          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
            >
              📥 Export CSV
            </button>
            <button
              onClick={handleDetectTransfers}
              disabled={detectingTransfers}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium flex items-center gap-2 disabled:opacity-50"
            >
              🔄 {detectingTransfers ? 'Detecting...' : 'Detect Transfers'}
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium flex items-center gap-2"
            >
              <span>+</span> Add Transaction
            </button>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Account</label>
            <select 
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Select Account</option>
              {accounts.map(acc => (
                <option key={acc.id} value={acc.id}>{acc.name} ({acc.bank_name})</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Upload Statement (CSV, Excel, PDF)</label>
            <input 
              type="file" 
              accept=".csv,.xlsx,.xls,.pdf"
              onChange={handleFileUpload}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
            />
          </div>
        </div>
        
        {uploading && (
          <div className="mt-4 text-primary-600 flex items-center gap-2">
            <svg className="animate-spin h-5 w-5 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Parsing statement with AI...
          </div>
        )}

        {parsedTransactions.length > 0 && (
          <div className="mt-8 border-t border-gray-100 pt-6">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-medium text-gray-900">Preview ({parsedTransactions.length} transactions)</h3>
                
                {!templateFound && detectedStructure && (
                    <div className="flex items-center gap-2 bg-yellow-50 px-3 py-2 rounded-lg border border-yellow-100">
                        <input 
                            type="checkbox" 
                            id="saveTemplate"
                            checked={saveTemplate}
                            onChange={(e) => setSaveTemplate(e.target.checked)}
                            className="rounded text-yellow-600 focus:ring-yellow-500"
                        />
                        <label htmlFor="saveTemplate" className="text-sm text-yellow-800 cursor-pointer">
                            Save parsing structure for future uploads
                        </label>
                    </div>
                )}
                
                {templateFound && (
                    <span className="text-sm text-green-700 bg-green-50 px-3 py-1 rounded-full border border-green-100 flex items-center gap-1">
                        <span>✓</span> Used saved template
                    </span>
                )}
            </div>
            
            <div className="max-h-80 overflow-auto border border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {parsedTransactions.map((tx, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tx.transaction_date}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{tx.description}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {tx.amount}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">{tx.transaction_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 flex gap-3">
              <button 
                onClick={handleSaveParsed}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors shadow-sm font-medium"
              >
                Confirm & Save
              </button>
              <button 
                onClick={() => {
                    setParsedTransactions([]);
                    setDetectedStructure(null);
                }}
                className="text-red-600 hover:text-red-800 px-4 py-2 font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>


      {/* Filters */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={filters.start_date || ''}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={filters.end_date || ''}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={filters.category_id || ''}
              onChange={(e) => setFilters({ ...filters, category_id: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
          
          {/* Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              value={filters.transaction_type || ''}
              onChange={(e) => setFilters({ ...filters, transaction_type: e.target.value as any || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
              <option value="transfer">Transfer</option>
            </select>
          </div>
          
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <input
              type="text"
              placeholder="Search description or merchant..."
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value || undefined })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          {/* Clear Filters */}
          <div className="flex items-end">
            <button
              onClick={() => setFilters({
                account_id: undefined,
                category_id: undefined,
                transaction_type: undefined,
                start_date: undefined,
                end_date: undefined,
                search: undefined,
              })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>


      {/* Potential Transfers */}
      {showTransfers && potentialTransfers.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Potential Transfers ({potentialTransfers.length})
            </h3>
            <button
              onClick={() => setShowTransfers(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="space-y-4">
            {potentialTransfers.map((transfer, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        {(transfer.confidence_score * 100).toFixed(0)}% Match
                      </span>
                      <span className="text-sm text-gray-500">
                        ₹{transfer.amount.toFixed(2)}
                      </span>
                      {transfer.date_diff_days > 0 && (
                        <span className="text-xs text-gray-400">
                          {transfer.date_diff_days} day(s) apart
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="font-medium text-red-600">From (Debit)</div>
                        <div className="text-gray-700">{transfer.debit_transaction.description}</div>
                        <div className="text-gray-500 text-xs">{transfer.debit_transaction.date}</div>
                      </div>
                      <div>
                        <div className="font-medium text-green-600">To (Credit)</div>
                        <div className="text-gray-700">{transfer.credit_transaction.description}</div>
                        <div className="text-gray-500 text-xs">{transfer.credit_transaction.date}</div>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleConfirmTransfer(transfer)}
                    className="ml-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
                  >
                    Link as Transfer
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transactions List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Merchant</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(tx.transaction_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 font-medium">{tx.description}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{tx.merchant_name || '-'}</td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${
                    tx.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {tx.transaction_type === 'income' ? '+' : '-'}₹{Math.abs(tx.amount).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${
                      tx.transaction_type === 'income' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {tx.transaction_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => setEditingTransaction(tx)}
                      className="text-primary-600 hover:text-primary-900 mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(tx.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    <p className="text-lg font-medium mb-1">No transactions found</p>
                    <p className="text-sm">Upload a bank statement to get started.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {editingTransaction && (
        <EditTransactionModal
          transaction={editingTransaction}
          onClose={() => setEditingTransaction(null)}
          onSave={handleUpdateSuccess}
        />
      )}
      
      <AddTransactionModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={loadData}
      />
    </div>
  );
};
