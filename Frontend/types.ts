export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  id?: string;
  email?: string;
  full_name?: string;
}

export interface Document {
  id: string;
  filename: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
  num_chunks?: number;
}

export interface ChatSource {
  id: string;
  document_id: string;
  filename: string;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  used_agent_mode: 'default' | 'research' | 'summarizer' | 'brainstorm';
  token_usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  latency_ms: number;
  conversation_id: string;
  created_at: string;
}

export interface AnalyticsOverview {
  total_users: number;
  total_documents: number;
  total_queries: number;
  avg_response_time_ms: number;
  top_documents: Array<{
    document_id: string;
    filename: string;
    query_count: number;
  }>;
  top_queries: Array<{
    query: string;
    count: number;
  }>;
  last_7d: Array<{
    date: string;
    query_count: number;
    avg_latency_ms: number;
  }>;
}

export interface UserAnalytics {
  user_id: string;
  email: string;
  total_queries: number;
  total_documents: number;
  avg_response_time_ms: number;
  last_activity_at: string;
}

export enum AgentMode {
  DEFAULT = 'default',
  RESEARCH = 'research',
  SUMMARIZER = 'summarizer',
  BRAINSTORM = 'brainstorm',
}