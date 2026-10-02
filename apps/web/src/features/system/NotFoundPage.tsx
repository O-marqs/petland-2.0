import { Link } from 'react-router-dom';
export default function NotFoundPage() {
  return (
    <div className="container not-found">
      <span className="eyebrow">PÁGINA NÃO ENCONTRADA</span>
      <h1>
        Vamos voltar
        <br />
        para um lugar conhecido?
      </h1>
      <p>Este endereço não está disponível. A nova experiência está sendo construída por etapas.</p>
      <Link className="button button--primary" to="/">
        Voltar ao início
      </Link>
    </div>
  );
}
