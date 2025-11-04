import { FormEvent, useState } from "react";

import { confirmToken, submitTokenPayload } from "../../api/client";
import type { TokenDetails } from "../../types";

type Props = {
  token: TokenDetails;
  expiresIn: string;
  supportContact?: string | null;
  refresh: () => void;
};

const GptPage = ({ token, expiresIn, supportContact, refresh }: Props) => {
  const [login, setLogin] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const metadataStatus = (token.metadata?.status as string | undefined) || "pending";

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!login) {
      setError("Введите логин");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitTokenPayload(token.token, { login });
      setFeedback("Логин передан. Ожидайте проверку.");
    } catch (err) {
      setError("Не удалось отправить данные. Попробуйте позже.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirm = async () => {
    setSubmitting(true);
    try {
      await confirmToken(token.token);
      refresh();
      setFeedback("Спасибо! Товар подтвержден.");
    } catch (err) {
      setError("Не удалось подтвердить получение.");
    } finally {
      setSubmitting(false);
    }
  };

  if (metadataStatus === "success") {
    return (
      <main>
        <div className="card">
          <div className="status">Готово</div>
          <h1>{token.product_title}</h1>
          <p>Подключение успешно завершено. Вы можете закрыть страницу.</p>
          <p>Срок действия ссылки: {expiresIn}</p>
          <div className="actions">
            <button onClick={handleConfirm} disabled={isSubmitting}>
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
  }

  if (metadataStatus === "error") {
    return (
      <main>
        <div className="card">
          <div className="status">Ошибка</div>
          <h1>{token.product_title}</h1>
          <p>Произошла ошибка при обработке. Обратитесь в поддержку.</p>
          {supportContact && (
            <a className="button" href={`https://t.me/${supportContact.replace(/^@/, "")}`}>
              Написать в поддержку
            </a>
          )}
        </div>
      </main>
    );
  }

  return (
    <main>
      <div className="card">
        <div className="status">Подтвердите данные</div>
        <h1>{token.product_title}</h1>
        <p>Введите логин аккаунта, который нужно подключить.</p>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Логин"
            value={login}
            onChange={(event) => setLogin(event.target.value)}
            disabled={isSubmitting}
          />
          <button type="submit" disabled={isSubmitting}>
            Отправить
          </button>
        </form>
        {feedback && <p>{feedback}</p>}
        {error && <p>{error}</p>}
        <p>Срок действия ссылки: {expiresIn}</p>
        {supportContact && (
          <a className="support-link" href={`https://t.me/${supportContact.replace(/^@/, "")}`}>
            Связаться с поддержкой
          </a>
        )}
      </div>
    </main>
  );
};

export default GptPage;
