import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { ConnectionStatus } from './ConnectionStatus';
import { PetPortrait } from '../../shared/ui/PetPortrait';
import { operationsApi } from '../booking/operations-api';

export default function HomePage() {
  const shop = useQuery({
    queryKey: ['schedule', 'establishment'],
    queryFn: ({ signal }) => operationsApi.establishment(signal),
  });
  return (
    <div className="petland-home">
      <section className="container editorial-hero" aria-labelledby="hero-title">
        <div className="editorial-copy">
          <span className="eyebrow">PETLAND · CUIDADO QUE CONECTA</span>
          <h1 id="hero-title">
            Cada pet.
            <br />
            Um mundo
            <br />
            de <em>cuidado.</em>
          </h1>
          <p>
            Mais cuidado. Menos preocupação. Um lugar para organizar os cuidados de quem faz parte
            da sua família.
          </p>
          <div className="hero-actions">
            <Link className="button button--primary" to="/criar-conta">
              Criar minha conta <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link className="text-link" to="/entrar">
              Já tenho uma conta
            </Link>
          </div>
        </div>
        <figure className="editorial-portrait">
          <span className="portrait-label" aria-hidden="true">
            DE PERTO
            <br />É MAIS BONITO.
          </span>
          <PetPortrait priority />
          <figcaption>
            <span>Companhia para todos os dias.</span>
            <small>Imagem editorial gerada</small>
          </figcaption>
        </figure>
        <div className="hero-footnote">
          <span>DA PRIMEIRA VISITA AO PRÓXIMO REENCONTRO</span>
          <a href="#proposta" className="text-link">
            Conheça o caminho ↓
          </a>
        </div>
      </section>
      <section
        className="container editorial-journey"
        id="proposta"
        aria-labelledby="journey-title"
      >
        <div className="journey-intro">
          <span className="eyebrow">UM CUIDADO, PASSO A PASSO</span>
          <h2 id="journey-title">
            Pequenos detalhes.
            <br />
            <em>Mais perto.</em>
          </h2>
          <p>
            Você, seu pet e a equipe. Cada etapa tem seu lugar, sem perder o que torna cada
            companheiro único.
          </p>
        </div>
        <ol className="journey-ledger">
          {[
            [
              '01',
              'Seu pet, em primeiro lugar',
              'Nome, porte e cuidados importantes. Conhecer seu pet é o começo de um atendimento mais atento.',
              '/app/pets',
              'Organizar meus pets',
            ],
            [
              '02',
              'Um horário que funciona',
              'Escolha o serviço, consulte a disponibilidade e confira preço e duração antes de confirmar.',
              '/servicos',
              'Conhecer os serviços',
            ],
            [
              '03',
              'Cuidado que continua',
              'Consulte a situação do atendimento e reencontre os resumos publicados no histórico do seu pet.',
              '/app/reservas',
              'Acompanhar meus cuidados',
            ],
          ].map(([number, title, text, to, action]) => (
            <li key={number}>
              <span className="ledger-number" aria-hidden="true">
                {number}
              </span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
                <Link className="text-link" to={to}>
                  {action} <ArrowRight size={16} aria-hidden="true" />
                </Link>
              </div>
            </li>
          ))}
        </ol>
      </section>
      <section className="care-feature" aria-labelledby="care-feature-title">
        <div className="container care-feature-inner">
          <div>
            <span className="eyebrow">ANTES DE ESCOLHER</span>
            <h2 id="care-feature-title">
              O cuidado certo.
              <br />
              <em>Às claras.</em>
            </h2>
          </div>
          <div className="care-feature-copy">
            <p>
              Confira os serviços disponíveis, os portes atendidos, os preços e a duração. Um
              cuidado começa com uma escolha bem informada.
            </p>
            <Link className="button button--secondary" to="/servicos">
              Ver serviços <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <div className="feature-index">
              <span>PORTE</span>
              <span>PREÇO</span>
              <span>DURAÇÃO</span>
            </div>
          </div>
        </div>
      </section>
      <section className="container editorial-access" aria-labelledby="access-title">
        <span className="eyebrow">SEU ESPAÇO PETLAND</span>
        <h2 id="access-title">
          Seu cuidado começa
          <br />
          com um <em>acesso.</em>
        </h2>
        <div>
          <p>
            Crie sua conta, confirme seu e-mail e organize seus pets. Do primeiro agendamento ao
            próximo reencontro.
          </p>
          <Link className="text-link" to="/entrar">
            Acessar minha conta <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </div>
      </section>
      {shop.data && (shop.data.shop_phone || shop.data.shop_email || shop.data.shop_address) && (
        <section className="container editorial-contact" aria-labelledby="contact-title">
          <h2 id="contact-title">Fale com {shop.data.shop_name}</h2>
          <div>
            {shop.data.shop_phone && <p>Telefone: {shop.data.shop_phone}</p>}
            {shop.data.shop_email && <p>E-mail: {shop.data.shop_email}</p>}
            {shop.data.shop_address && <p>Endereço: {shop.data.shop_address}</p>}
          </div>
        </section>
      )}
      <ConnectionStatus />
    </div>
  );
}
