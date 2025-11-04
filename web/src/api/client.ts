import axios from "axios";

import type { TokenActionResponse, TokenDetails } from "../types";

const baseURL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "/api";

export const api = axios.create({
  baseURL,
  timeout: 10000
});

export const fetchTokenDetails = async (token: string): Promise<TokenDetails> => {
  const { data } = await api.get<TokenDetails>(`/tokens/${token}`);
  return data;
};

export const submitTokenPayload = async (
  token: string,
  payload: Record<string, unknown>
): Promise<TokenActionResponse> => {
  const { data } = await api.post<TokenActionResponse>(`/tokens/${token}/submit`, {
    data: payload
  });
  return data;
};

export const completeToken = async (token: string): Promise<TokenActionResponse> => {
  const { data } = await api.post<TokenActionResponse>(`/tokens/${token}/complete`);
  return data;
};

export const failToken = async (token: string): Promise<TokenActionResponse> => {
  const { data } = await api.post<TokenActionResponse>(`/tokens/${token}/fail`);
  return data;
};

export const confirmToken = async (token: string): Promise<TokenActionResponse> => {
  const { data } = await api.post<TokenActionResponse>(`/tokens/${token}/confirm`);
  return data;
};
