// Common types for the application

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
  permissions: string[];
}

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  metadata?: {
    tokens?: number;
    model?: string;
    confidence?: number;
  };
}

export interface InventoryItem {
  id: string;
  name: string;
  sku: string;
  description?: string;
  quantity: number;
  price: number;
  category: string;
  supplier?: string;
  location?: string;
  lastUpdated: Date;
  createdAt: Date;
}

export interface Task {
  id: string;
  type: 'email' | 'document' | 'query' | 'inventory';
  title: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | 'failed';
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  approvedBy?: string;
  metadata?: Record<string, any>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// Configuration types
export interface AppConfig {
  apiBaseUrl: string;
  features: {
    nlSqlEnabled: boolean;
    emailEnabled: boolean;
    documentGenerationEnabled: boolean;
    telemetryEnabled: boolean;
  };
  ui: {
    theme: 'light' | 'dark';
    language: string;
  };
}
