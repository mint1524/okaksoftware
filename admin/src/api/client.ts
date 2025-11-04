import axios from "axios";

import type {
  AdminSummary,
  FileAsset,
  LoginResponse,
  Product,
  Purchase
} from "../types";

const baseURL = (
  import.meta.env.VITE_ADMIN_API_BASE_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "/api"
) as string;

const api = axios.create({
  baseURL,
  timeout: 15000
});

export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

export const login = async (password: string): Promise<LoginResponse> => {
  const { data } = await api.post<LoginResponse>("/admin/panel/auth/login", { password });
  return data;
};

export const fetchSummary = async (): Promise<AdminSummary> => {
  const { data } = await api.get<AdminSummary>("/admin/panel/dashboard/summary");
  return data;
};

export const fetchProducts = async (): Promise<Product[]> => {
  const { data } = await api.get<{ items: Product[] }>("/admin/panel/products");
  return data.items;
};

export const createProduct = async (payload: Record<string, unknown>): Promise<Product[]> => {
  const { data } = await api.post<{ items: Product[] }>("/admin/panel/products", payload);
  return data.items;
};

export const updateProduct = async (
  productId: number,
  payload: Record<string, unknown>
): Promise<Product[]> => {
  const { data } = await api.put<{ items: Product[] }>(`/admin/panel/products/${productId}`, payload);
  return data.items;
};

export const deleteProduct = async (productId: number): Promise<Product[]> => {
  const { data } = await api.delete<{ items: Product[] }>(`/admin/panel/products/${productId}`);
  return data.items;
};

export const createVariant = async (
  productId: number,
  payload: Record<string, unknown>
): Promise<Product[]> => {
  const { data } = await api.post<{ items: Product[] }>(
    `/admin/panel/products/${productId}/variants`,
    payload
  );
  return data.items;
};

export const updateVariant = async (
  variantId: number,
  payload: Record<string, unknown>
): Promise<Product[]> => {
  const { data } = await api.put<{ items: Product[] }>(`/admin/panel/variants/${variantId}`, payload);
  return data.items;
};

export const deleteVariant = async (variantId: number): Promise<Product[]> => {
  const { data } = await api.delete<{ items: Product[] }>(`/admin/panel/variants/${variantId}`);
  return data.items;
};

export const fetchPurchases = async (
  params: { status?: string; product_type?: string } = {}
): Promise<Purchase[]> => {
  const { data } = await api.get<{ items: Purchase[] }>("/admin/panel/purchases", { params });
  return data.items;
};

export const fetchFileAssets = async (): Promise<FileAsset[]> => {
  const { data } = await api.get<FileAsset[]>("/admin/panel/files");
  return data;
};

export const createFileAsset = async (payload: Record<string, unknown>): Promise<FileAsset[]> => {
  const { data } = await api.post<FileAsset[]>("/admin/panel/files", payload);
  return data;
};

export const updateFileAsset = async (
  id: number,
  payload: Record<string, unknown>
): Promise<FileAsset[]> => {
  const { data } = await api.put<FileAsset[]>(`/admin/panel/files/${id}`, payload);
  return data;
};

export const deleteFileAsset = async (id: number): Promise<FileAsset[]> => {
  const { data } = await api.delete<FileAsset[]>(`/admin/panel/files/${id}`);
  return data;
};

export default api;
