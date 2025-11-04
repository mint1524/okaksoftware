import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import dayjs from "dayjs";

import { fetchTokenDetails } from "../api/client";
import type { TokenDetails } from "../types";
import DefaultPage from "./DefaultPage";
import GptPage from "./gpt/GptPage";
import VpnPage from "./vpn/VpnPage";

interface TokenState {
  loading: boolean;
  error?: string;
  data?: TokenDetails;
}

const TokenPage = () => {
  const { token } = useParams();
  const [state, setState] = useState<TokenState>({ loading: true });

  const load = useCallback(() => {
    if (!token) {
      setState({ loading: false, error: "Токен не найден" });
      return;
    }
    setState((prev) => ({ ...prev, loading: true }));
    fetchTokenDetails(token)
      .then((data) => setState({ loading: false, data }))
      .catch((error) => {
        setState({ loading: false, error: error?.response?.data?.detail || "Ошибка загрузки" });
      });
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const expiresIn = useMemo(() => {
    if (!state.data || !state.data.expires_at) return "-";
    return dayjs(state.data.expires_at).format("DD.MM.YYYY HH:mm");
  }, [state.data]);

  if (state.loading) {
    return (
      <main>
        <div className="card">
          <div className="status">Загрузка…</div>
          <p>Проверяем данные токена.</p>
        </div>
      </main>
    );
  }

  if (state.error || !state.data) {
    return (
      <main>
        <div className="card">
          <div className="status">Ошибка</div>
          <p>{state.error || "Не удалось загрузить токен."}</p>
          <a className="button secondary" href="https://t.me">
            Написать в поддержку
          </a>
        </div>
      </main>
    );
  }

  const { product_type: productType, support_contact: supportContact } = state.data;

  const baseProps = {
    token: state.data,
    expiresIn,
    supportContact
  };

  switch (productType) {
    case "gpt":
      return <GptPage {...baseProps} refresh={load} />;
    case "vpn":
      return <VpnPage {...baseProps} refresh={load} />;
    default:
      return <DefaultPage {...baseProps} />;
  }
};

export default TokenPage;
