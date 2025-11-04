export interface ProductVariant {
  id: number;
  name: string;
  price: number;
  currency: string;
  digiseller_product_id?: string | null;
  payment_url?: string | null;
  sort_order: number;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  title: string;
  slug: string;
  type: string;
  description?: string | null;
  support_contact?: string | null;
  domain_hint?: string | null;
  is_active: boolean;
  metadata?: Record<string, unknown> | null;
  variants: ProductVariant[];
  created_at: string;
  updated_at: string;
}

export interface AdminSummary {
  users_total: number;
  products_total: number;
  active_products: number;
  purchases_total: number;
  purchases_pending: number;
  purchases_paid: number;
  purchases_delivered: number;
  tokens_active: number;
}

export interface Purchase {
  id: number;
  status: string;
  digiseller_order_id?: string | null;
  invoice_url?: string | null;
  token?: string | null;
  domain_type?: string | null;
  expires_at?: string | null;
  delivered_at?: string | null;
  metadata?: Record<string, unknown> | null;
  product_title: string;
  product_type: string;
  variant_name: string;
  token_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FileAsset {
  id: number;
  product_type: string;
  label: string;
  path: string;
  os_type?: string | null;
  checksum?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
