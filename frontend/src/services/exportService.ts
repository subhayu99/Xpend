import api from './api';

export const exportService = {
  exportTransactionsCSV: async (params?: {
    start_date?: string;
    end_date?: string;
    account_id?: string;
    category_id?: string;
  }): Promise<void> => {
    const response = await api.get('/export/transactions/csv', {
      params,
      responseType: 'blob'
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = `transactions_${new Date().toISOString().slice(0, 10)}.csv`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=(.+)/);
      if (match) {
        filename = match[1];
      }
    }

    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  exportMonthlyReportCSV: async (month?: number, year?: number): Promise<void> => {
    const params: any = {};
    if (month) params.month = month;
    if (year) params.year = year;

    const response = await api.get('/export/monthly-report/csv', {
      params,
      responseType: 'blob'
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    const now = new Date();
    const m = month || now.getMonth() + 1;
    const y = year || now.getFullYear();
    link.setAttribute('download', `monthly_report_${y}_${m.toString().padStart(2, '0')}.csv`);

    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};
