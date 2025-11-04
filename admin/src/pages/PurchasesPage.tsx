import { useEffect, useState } from "react";
import dayjs from "dayjs";

import { fetchPurchases } from "../api/client";
import type { Purchase } from "../types";

const statuses = [
  { value: "", label: "Все" },
  { value: "pending", label: "Ожидает оплаты" },
  { value: "paid", label: "Оплачено" },
  { value: "delivered", label: "Доставлено" },
  { value: "failed", label: "Ошибка" },
  { value: "expired", label: "Просрочено" },
  { value: "refunded", label: "Возврат" }
];

const PurchasesPage = () => {
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchPurchases({
          status: statusFilter || undefined,
          product_type: typeFilter || undefined
        });
        setPurchases(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError("Не удалось загрузить покупки");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [statusFilter, typeFilter]);

  return (
    <div className="card">
      <h2>Покупки</h2>
      {error && <div className="alert">{error}</div>}
      <div className="inline-form" style={{ marginBottom: "1rem" }}>
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          {statuses.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <input
          placeholder="Тип товара (gpt/vpn)"
          value={typeFilter}
          onChange={(event) => setTypeFilter(event.target.value)}
        />
      </div>

      {loading ? (
        <p>Загрузка...</p>
      ) : purchases.length === 0 ? (
        <p>Записей не найдено.</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Статус</th>
                <th>Платёж</th>
                <th>Товар</th>
                <th>Тариф</th>
                <th>Token URL</th>
                <th>Создано</th>
                <th>Expires</th>
              </tr>
            </thead>
            <tbody>
              {purchases.map((purchase) => (
                <tr key={purchase.id}>
                  <td>{purchase.id}</td>
                  <td>{purchase.status}</td>
                  <td>
                    <div>{purchase.payment_provider}</div>
                    {purchase.payment_label && <small>Label: {purchase.payment_label}</small>}
                    {purchase.payment_amount != null && (
                      <small>
                        {purchase.payment_amount} {purchase.payment_currency || "RUB"}
                      </small>
                    )}
                  </td>
                  <td>
                    {purchase.product_title}
                    <br />
                    <small>{purchase.product_type}</small>
                  </td>
                  <td>{purchase.variant_name}</td>
                  <td>
                    {purchase.token_url ? (
                      <a href={purchase.token_url} target="_blank" rel="noreferrer">
                        Открыть
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{dayjs(purchase.created_at).format("DD.MM.YYYY HH:mm")}</td>
                  <td>
                    {purchase.expires_at
                      ? dayjs(purchase.expires_at).format("DD.MM.YYYY HH:mm")
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PurchasesPage;
