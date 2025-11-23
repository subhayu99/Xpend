import api from './api';

export interface UserProfile {
  name: string;
  email: string;
  currency: string;
  timezone: string;
}

export const settingsService = {
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/settings/profile');
    return response.data;
  },

  updateProfile: async (data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await api.put('/settings/profile', data);
    return response.data;
  },

  exportData: async () => {
    const response = await api.get('/settings/export/json', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `finance_backup_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};
