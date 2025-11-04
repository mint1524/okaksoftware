import { useEffect, useState } from "react";
import dayjs from "dayjs";

import { fetchSummary } from "../api/client";
import type { AdminSummary } from "../types";

const DashboardPage = () => {
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [loadedAt, setLoadedAt] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchSummary();
        setSummary(data);
        setLoadedAt(dayjs().format("DD.MM.YYYY HH:mm"));
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Не удалось загрузить статистику");
      }
    };
    load();
  }, []);

  return (
    <div className="card">
      <h2>Статистика</h2>
      {error && <div className="alert">{error}</div>}
      {summary ? (
        <div className="grid cols-4">
          <div className="stat">
            <span>Пользователи</span>
            <strong>{summary.users_total}</strong>
          </div>
          <div className="stat">
            <span>Товары</span>
            <strong>{summary.products_total}</strong>
            <small>Активных: {summary.active_products}</small>
          </div>
          <div className="stat">
            <span>Покупки</span>
            <strong>{summary.purchases_total}</strong>
            <small>
              {`ожидание ${summary.purchases_pending}, оплачено ${summary.purchases_paid}, доставлено ${summary.purchases_delivered}`}
            </small>
          </div>
          <div className="stat">
            <span>Активные токены</span>
            <strong>{summary.tokens_active}</strong>
          </div>
        </div>
      ) : (
        <p>Загрузка...</p>
      )}
      {loadedAt && <p>Обновлено: {loadedAt}</p>}
    </div>
  );
};

export default DashboardPage;
