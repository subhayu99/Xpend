import api from './api';

export interface PotentialTransfer {
  debit_transaction: {
    id: string;
    date: string;
    amount: number;
    description: string;
    account_id: string;
  };
  credit_transaction: {
    id: string;
    date: string;
    amount: number;
    description: string;
    account_id: string;
  };
  confidence_score: number;
  date_diff_days: number;
  amount: number;
}

export const transferService = {
  detectPotential: async (daysWindow: number = 2): Promise<PotentialTransfer[]> => {
    const response = await api.get('/transfers/detect', {
      params: { days_window: daysWindow }
    });
    return response.data;
  },

  createTransfer: async (debitTxId: string, creditTxId: string, confidenceScore?: number): Promise<void> => {
    await api.post('/transfers', {
      debit_transaction_id: debitTxId,
      credit_transaction_id: creditTxId,
      confidence_score: confidenceScore
    });
  },

  deleteTransfer: async (transferId: string): Promise<void> => {
    await api.delete(`/transfers/${transferId}`);
  },

  getAll: async (): Promise<any[]> => {
    const response = await api.get('/transfers');
    return response.data;
  }
};
