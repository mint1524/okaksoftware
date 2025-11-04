import type { TokenDetails } from "../types";

type Props = {
  token: TokenDetails;
  expiresIn: string;
  supportContact?: string | null;
};

const DefaultPage = ({ token, expiresIn, supportContact }: Props) => {
  return (
    <main>
      <div className="card">
        <div className="status">Данные токена</div>
        <h1>{token.product_title}</h1>
        <p>Срок действия ссылки: {expiresIn}</p>
        <p>Статус: {token.status}</p>
        {supportContact && (
          <a className="support-link" href={`https://t.me/${supportContact.replace(/^@/, "")}`}>
            Нужна помощь? Напишите нам
          </a>
        )}
      </div>
    </main>
  );
};

export default DefaultPage;
