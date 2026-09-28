import { Link } from 'react-router-dom';
import { ArrowRight, HeartHandshake, CalendarDays, ClipboardCheck, Sparkles } from 'lucide-react';
import { Badge } from '../../shared/ui/Feedback';
import { ConnectionStatus } from './ConnectionStatus';
import { PetIllustration } from './PetIllustration';

export default function HomePage() {
  return (
    <div className="container">
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <span className="eyebrow">
            <span className="little-line" /> CUIDADO QUE CONECTA
          </span>
          <h1 id="hero-title">
            Mais cuidado.
            <br />
            <span>Menos preocupação.</span>
          </h1>
          <p>
            Uma nova forma de organizar os cuidados do seu pet. Do primeiro agendamento ao próximo
            reencontro.
          </p>
          <div className="hero-actions">
            <Link className="button button--primary" to="/criar-conta">
              Criar minha conta <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link className="text-link" to="/entrar">
              Já tenho uma conta
            </Link>
          </div>
          <div className="hero-note">
            <HeartHandshake size={20} aria-hidden="true" />
            <span>Pensado para quem cuida. E para quem é família.</span>
          </div>
        </div>
        <div className="hero-art">
          <PetIllustration />
          <div className="art-caption">
            <span className="caption-line" /> JUNTOS, EM CADA ETAPA
          </div>
        </div>
      </section>
      <section className="journey-section" id="proposta" aria-labelledby="journey-title">
        <div className="section-heading">
          <div>
            <span className="eyebrow">UMA EXPERIÊNCIA MAIS SIMPLES</span>
            <h2 id="journey-title">O cuidado tem um caminho.</h2>
          </div>
          <p>
            Estamos construindo uma jornada que aproxima
            <br className="desktop-only" /> você, seu pet e a equipe.
          </p>
        </div>
        <div className="journey-grid">
          {[
            {
              icon: HeartHandshake,
              number: '01',
              title: 'Seu pet, em primeiro lugar',
              text: 'Informações e cuidados reunidos para conhecer quem faz parte da sua família.',
            },
            {
              icon: CalendarDays,
              number: '02',
              title: 'Um horário que funciona',
              text: 'Serviço, data e confirmação com clareza em cada escolha.',
            },
            {
              icon: ClipboardCheck,
              number: '03',
              title: 'Cuidado que continua',
              text: 'Acompanhe cada etapa do atendimento e volte ao histórico quando precisar.',
            },
          ].map(({ icon: Icon, number, title, text }) => (
            <article className="journey-card" key={number}>
              <div className="journey-card-top">
                <Icon size={26} strokeWidth={1.6} aria-hidden="true" />
                <span>{number}</span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
              <span className="planned-label">Planejado para as próximas etapas</span>
            </article>
          ))}
        </div>
      </section>
      <section className="foundation-panel" aria-labelledby="foundation-title">
        <div className="foundation-icon">
          <Sparkles size={28} aria-hidden="true" />
        </div>
        <div>
          <Badge>SEU ESPAÇO PETLAND</Badge>
          <h2 id="foundation-title">Seu cuidado começa com um acesso.</h2>
          <p>
            Crie sua conta, confirme seu e-mail e acesse seu espaço com segurança. Pets, serviços e
            agendamentos serão disponibilizados nas próximas entregas.
          </p>
        </div>
        <Link className="button button--secondary" to="/entrar">
          Acessar minha conta <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </section>
      <ConnectionStatus />
    </div>
  );
}
