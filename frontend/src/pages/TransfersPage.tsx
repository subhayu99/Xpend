import React, { useState, useEffect } from 'react';
import { transferService, PotentialTransfer } from '../services/transferService';
import { accountService, Account } from '../services/accountService';

interface LinkedTransfer {
  id: string;
  amount: number;
  transfer_date: string;
  confidence_score: number;
  is_confirmed: boolean;
  debit_transaction: { id: string; description: string; account_id: string } | null;
  credit_transaction: { id: string; description: string; account_id: string } | null;
}

export const TransfersPage: React.FC = () => {
  const [potentialTransfers, setPotentialTransfers] = useState<PotentialTransfer[]>([]);
  const [linkedTransfers, setLinkedTransfers] = useState<LinkedTransfer[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [daysWindow, setDaysWindow] = useState(2);
  const [activeTab, setActiveTab] = useState<'detect' | 'linked'>('detect');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [potentialData, linkedData, accountsData] = await Promise.all([
        transferService.detectPotential(daysWindow),
        transferService.getAll(),
        accountService.getAll()
      ]);
      setPotentialTransfers(potentialData);
      setLinkedTransfers(linkedData);
      setAccounts(accountsData);
    } catch (error) {
      console.error('Failed to load transfers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDetect = async () => {
    setLoading(true);
    try {
      const data = await transferService.detectPotential(daysWindow);
      setPotentialTransfers(data);
    } catch (error) {
      console.error('Failed to detect transfers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLink = async (transfer: PotentialTransfer) => {
    try {
      await transferService.createTransfer(
        transfer.debit_transaction.id,
        transfer.credit_transaction.id,
        transfer.confidence_score
      );
      await loadData();
    } catch (error) {
      console.error('Failed to link transfer:', error);
      alert('Failed to link transfer');
    }
  };

  const handleUnlink = async (transferId: string) => {
    if (!window.confirm('Are you sure you want to unlink this transfer?')) return;
    try {
      await transferService.deleteTransfer(transferId);
      await loadData();
    } catch (error) {
      console.error('Failed to unlink transfer:', error);
      alert('Failed to unlink transfer');
    }
  };

  const getAccountName = (accountId: string) => {
    const account = accounts.find(a => a.id === accountId);
    return account?.name || 'Unknown Account';
  };

  const formatCurrency = (amount: number) => `₹${Math.abs(amount).toLocaleString()}`;
  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString();

  if (loading) {
    return <div className="p-8 text-center">Loading transfers...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Self Transfers</h1>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('detect')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'detect'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Detect Transfers
            {potentialTransfers.length > 0 && (
              <span className="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded-full">
                {potentialTransfers.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('linked')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'linked'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Linked Transfers
            {linkedTransfers.length > 0 && (
              <span className="ml-2 bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full">
                {linkedTransfers.length}
              </span>
            )}
          </button>
        </nav>
      </div>

      {activeTab === 'detect' && (
        <div className="space-y-4">
          {/* Detection Controls */}
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
            <label className="text-sm text-gray-600">Days window:</label>
            <select
              value={daysWindow}
              onChange={(e) => setDaysWindow(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value={1}>1 day</option>
              <option value={2}>2 days</option>
              <option value={3}>3 days</option>
              <option value={5}>5 days</option>
              <option value={7}>7 days</option>
            </select>
            <button
              onClick={handleDetect}
              className="px-4 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
            >
              Detect Transfers
            </button>
          </div>

          {/* Potential Transfers List */}
          {potentialTransfers.length === 0 ? (
            <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center text-gray-500">
              No potential self-transfers detected. Try increasing the days window or add more transactions.
            </div>
          ) : (
            <div className="space-y-3">
              {potentialTransfers.map((transfer, index) => (
                <div
                  key={index}
                  className="bg-white p-4 rounded-xl shadow-sm border border-gray-100"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4">
                        {/* Debit Side */}
                        <div className="flex-1 p-3 bg-red-50 rounded-lg">
                          <p className="text-xs text-red-600 font-medium">FROM</p>
                          <p className="font-semibold text-gray-900">{getAccountName(transfer.debit_transaction.account_id)}</p>
                          <p className="text-sm text-gray-600 truncate">{transfer.debit_transaction.description}</p>
                          <p className="text-lg font-bold text-red-600">-{formatCurrency(transfer.amount)}</p>
                        </div>

                        {/* Arrow */}
                        <div className="flex flex-col items-center">
                          <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                          </svg>
                          <span className="text-xs text-gray-500">{transfer.date_diff_days}d</span>
                        </div>

                        {/* Credit Side */}
                        <div className="flex-1 p-3 bg-green-50 rounded-lg">
                          <p className="text-xs text-green-600 font-medium">TO</p>
                          <p className="font-semibold text-gray-900">{getAccountName(transfer.credit_transaction.account_id)}</p>
                          <p className="text-sm text-gray-600 truncate">{transfer.credit_transaction.description}</p>
                          <p className="text-lg font-bold text-green-600">+{formatCurrency(transfer.amount)}</p>
                        </div>
                      </div>

                      {/* Confidence */}
                      <div className="mt-3 flex items-center gap-2">
                        <span className="text-xs text-gray-500">Confidence:</span>
                        <div className="flex-1 max-w-[100px] bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              transfer.confidence_score >= 0.9 ? 'bg-green-500' :
                              transfer.confidence_score >= 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${transfer.confidence_score * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium">{Math.round(transfer.confidence_score * 100)}%</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="ml-4">
                      <button
                        onClick={() => handleLink(transfer)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium flex items-center gap-2"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                        Link
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'linked' && (
        <div className="space-y-3">
          {linkedTransfers.length === 0 ? (
            <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 text-center text-gray-500">
              No linked transfers yet. Go to "Detect Transfers" to find and link self-transfers.
            </div>
          ) : (
            linkedTransfers.map((transfer) => (
              <div
                key={transfer.id}
                className="bg-white p-4 rounded-xl shadow-sm border border-gray-100"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1">
                    {/* From */}
                    <div className="flex-1">
                      <p className="text-xs text-gray-500">From</p>
                      <p className="font-medium text-gray-900">
                        {transfer.debit_transaction ? getAccountName(transfer.debit_transaction.account_id) : 'Unknown'}
                      </p>
                      <p className="text-sm text-gray-600 truncate">
                        {transfer.debit_transaction?.description}
                      </p>
                    </div>

                    {/* Arrow & Amount */}
                    <div className="text-center">
                      <svg className="w-6 h-6 text-gray-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                      <p className="font-bold text-primary-600">{formatCurrency(transfer.amount)}</p>
                    </div>

                    {/* To */}
                    <div className="flex-1">
                      <p className="text-xs text-gray-500">To</p>
                      <p className="font-medium text-gray-900">
                        {transfer.credit_transaction ? getAccountName(transfer.credit_transaction.account_id) : 'Unknown'}
                      </p>
                      <p className="text-sm text-gray-600 truncate">
                        {transfer.credit_transaction?.description}
                      </p>
                    </div>

                    {/* Date */}
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Date</p>
                      <p className="text-sm font-medium">{formatDate(transfer.transfer_date)}</p>
                    </div>
                  </div>

                  {/* Unlink Button */}
                  <button
                    onClick={() => handleUnlink(transfer.id)}
                    className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    title="Unlink transfer"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
