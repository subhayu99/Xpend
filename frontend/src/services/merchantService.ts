import api from './api';

export interface Merchant {
  id: string;
  user_id: string;
  normalized_name: string;
  patterns: string[];
  category_id: string | null;
  fuzzy_threshold: number;
  is_public: boolean;
  usage_count: number;
  category: {
    id: string;
    name: string;
  } | null;
  created_at: string;
  updated_at: string;
}

export interface MerchantCreate {
  normalized_name: string;
  patterns?: string[];
  category_id?: string;
  fuzzy_threshold?: number;
  is_public?: boolean;
}

export interface MerchantUpdate {
  normalized_name?: string;
  patterns?: string[];
  category_id?: string;
  fuzzy_threshold?: number;
  is_public?: boolean;
}

export interface MerchantListResponse {
  items: Merchant[];
  total: number;
  page: number;
  limit: number;
}

export interface UnmappedMerchant {
  raw_name: string;
  transaction_count: number;
  total_amount: number;
  first_seen: string;
  last_seen: string;
  sample_descriptions: string[];
}

export interface UnmappedMerchantsResponse {
  items: UnmappedMerchant[];
  total: number;
}

export interface MerchantSuggestion {
  category_name: string;
  category_id: string | null;
  confidence: number;
  reasoning: string | null;
}

export interface MerchantSuggestionsResponse {
  merchant_name: string;
  suggestions: MerchantSuggestion[];
}

export interface NormalizeResponse {
  original: string;
  normalized: string | null;
  existing_match: {
    merchant_id: string;
    normalized_name: string;
    category_id: string | null;
    match_score: number;
    matched_pattern: string | null;
  } | null;
}

export const merchantService = {
  getAll: async (params?: {
    page?: number;
    limit?: number;
    search?: string;
  }): Promise<MerchantListResponse> => {
    const response = await api.get('/merchants', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Merchant> => {
    const response = await api.get(`/merchants/${id}`);
    return response.data;
  },

  create: async (
    data: MerchantCreate,
    applyToExisting: boolean = true
  ): Promise<Merchant> => {
    const response = await api.post('/merchants', data, {
      params: { apply_to_existing: applyToExisting },
    });
    return response.data;
  },

  update: async (
    id: string,
    data: MerchantUpdate,
    applyToExisting: boolean = false
  ): Promise<Merchant> => {
    const response = await api.put(`/merchants/${id}`, data, {
      params: { apply_to_existing: applyToExisting },
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/merchants/${id}`);
  },

  getUnmapped: async (limit: number = 50): Promise<UnmappedMerchantsResponse> => {
    const response = await api.get('/merchants/unmapped', {
      params: { limit },
    });
    return response.data;
  },

  normalize: async (description: string): Promise<NormalizeResponse> => {
    const response = await api.get('/merchants/normalize', {
      params: { description },
    });
    return response.data;
  },

  getSuggestions: async (merchantName: string): Promise<MerchantSuggestionsResponse> => {
    const response = await api.get('/merchants/suggestions', {
      params: { merchant_name: merchantName },
    });
    return response.data;
  },

  applyMapping: async (
    id: string,
    updateCategory: boolean = true
  ): Promise<{ message: string; transactions_updated: number }> => {
    const response = await api.post(`/merchants/${id}/apply`, null, {
      params: { update_category: updateCategory },
    });
    return response.data;
  },
};
