import { useState } from "react";

import { confirmToken } from "../../api/client";
import type { TokenDetails } from "../../types";

type Props = {
  token: TokenDetails;
  expiresIn: string;
  supportContact?: string | null;
  refresh: () => void;
};

type DownloadItem = {
  label: string;
  url: string;
};

type ActivationField = {
  placeholder: string;
  value?: string;
};

const VpnPage = ({ token, expiresIn, supportContact, refresh }: Props) => {
  const [isProcessing, setProcessing] = useState(false);
  const productMeta = (token.metadata?.product as { instructions?: string }) || {};
  const downloads = Array.isArray(token.metadata?.downloads)
    ? (token.metadata?.downloads as DownloadItem[])
    : [];
  const productInstructions = typeof productMeta.instructions === "string" ? productMeta.instructions : undefined;
  const instructions =
    (token.metadata?.instructions as string) ||
    productInstructions ||
    "Скачайте конфигурацию и используйте учётные данные, которые придут после подтверждения оплаты.";
  const activations = Array.isArray(token.metadata?.activation)
    ? (token.metadata?.activation as ActivationField[])
    : [{ placeholder: "Ключ активации" }];

  const handleConfirm = async () => {
    setProcessing(true);
    try {
      await confirmToken(token.token);
      refresh();
    } catch (err) {
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <main>
      <div className="card">
        <div className="status">VPN доступ</div>
        <h1>{token.product_title}</h1>
        <p>{instructions}</p>
        {downloads.length > 0 && (
          <div>
            <h2>Скачайте клиент</h2>
            <ul>
              {downloads.map((item) => (
                <li key={item.label}>
                  <a className="support-link" href={item.url}>
                    {item.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
        <div>
          <h2>Данные активации</h2>
          {activations.map((field, index) => (
            <input key={index} value={field.value || ""} placeholder={field.placeholder} readOnly />
          ))}
        </div>
        <p>Ссылка активна до {expiresIn}</p>
        <div className="actions">
          <button onClick={handleConfirm} disabled={isProcessing}>
            Товар получен
          </button>
        </div>
        {supportContact && (
          <a className="support-link" href={`https://t.me/${supportContact.replace(/^@/, "")}`}>
            Нужна помощь? Напишите нам
          </a>
        )}
      </div>
    </main>
  );
};

export default VpnPage;
