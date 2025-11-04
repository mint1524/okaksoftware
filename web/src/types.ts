export interface TokenDetails {
  token: string;
  status: string;
  expires_at: string;
  delivered_at?: string | null;
  product_type: string;
  product_title: string;
  support_contact?: string | null;
  domain: string;
  metadata?: Record<string, unknown> | null;
}

export interface TokenResponse {
  data: TokenDetails;
}

export interface TokenActionResponse {
  status: string;
  message?: string;
}
