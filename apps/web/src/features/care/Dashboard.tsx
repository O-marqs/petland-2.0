import { Link, useOutletContext } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PawPrint, ArrowRight, UserRound, Sparkles } from 'lucide-react';
import type { Account } from '../identity/api';
import { careApi } from './api';
import { LoadError } from './Feedback';
import { EmptyState, Skeleton } from '../../shared/ui/Feedback';
import { bookingApi, dateTime } from '../booking/api';
import { statusLabels } from '../booking/operations-api';

export default function Dashboard() {
  const account = useOutletContext<Account>();
  const profile = useQuery({
    queryKey: ['care', 'customer', 'me'],
    queryFn: ({ signal }) => careApi.profile(signal),
  });
  const pets = useQuery({
    queryKey: ['care', 'pets', 'me', false, 0],
    queryFn: ({ signal }) => careApi.pets(undefined, false, 0, signal),
    enabled: !!profile.data,
  });
  const upcoming = useQuery({
    queryKey: ['schedule', 'next'],
    queryFn: ({ signal }) => bookingApi.list(false, 0, signal, { period: 'upcoming' }),
    enabled: !!profile.data,
  });
  return (
    <div className="care-stack">
      <header className="area-heading">
        <span className="eyebrow">BEM-VINDO AO SEU ESPAÇO</span>
        <h1>Olá, {account.display_name.split(' ')[0]}.</h1>
        <p>Um lugar para seus companheiros e os cuidados de cada dia.</p>
      </header>
      {profile.data && (
        <section className="identity-card">
          <h2>Próximo cuidado</h2>
          {upcoming.isPending ? (
            <Skeleton label="Carregando próximo cuidado" />
          ) : upcoming.isError ? (
            <LoadError error={upcoming.error} retry={() => void upcoming.refetch()} />
          ) : upcoming.data.items[0] ? (
            <>
              <h3>
                {upcoming.data.items[0].offer.pet_name} ·{' '}
                {upcoming.data.items[0].offer.service_name}
              </h3>
              <p>
                {dateTime(upcoming.data.items[0].starts_at, upcoming.data.items[0].timezone)} ·{' '}
                {statusLabels[upcoming.data.items[0].status]}
              </p>
              <Link to={'/app/reservas/' + upcoming.data.items[0].id}>Acompanhar cuidado</Link>
            </>
          ) : (
            <p>Quando você reservar um cuidado, ele aparecerá aqui.</p>
          )}
          <p>
            <Link className="button button--primary" to="/app/agendar">
              Agendar um cuidado
            </Link>
          </p>
        </section>
      )}
      <section className="care-welcome">
        <div>
          <span className="eyebrow">CUIDAR COMEÇA POR CONHECER</span>
          <h2>
            Pequenos detalhes.
            <br />
            Mais cuidado.
          </h2>
          <p>Mantenha as informações dos seus pets por perto e conheça os serviços disponíveis.</p>
          <Link className="button button--primary" to="/app/pets">
            Ver meus pets <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </div>
        <PawPrint className="welcome-paw" aria-hidden="true" />
      </section>
      {profile.isPending ? (
        <Skeleton label="Carregando cadastro" />
      ) : profile.isError ? (
        <LoadError error={profile.error} retry={() => void profile.refetch()} />
      ) : !profile.data ? (
        <section className="identity-card">
          <h2>Vamos nos conhecer?</h2>
          <p>
            Complete seu cadastro de contato antes de adicionar o primeiro pet. Se a equipe já fez
            seu cadastro, peça o link de vínculo.
          </p>
          <Link className="button button--secondary" to="/app/perfil">
            Completar meu cadastro
          </Link>
        </section>
      ) : (
        <section className="care-stack">
          <div className="care-toolbar">
            <h2>Seus pets</h2>
            <Link to="/app/pets">Ver todos →</Link>
          </div>
          {pets.isPending ? (
            <Skeleton label="Carregando pets" />
          ) : pets.isError ? (
            <LoadError error={pets.error} retry={() => void pets.refetch()} />
          ) : pets.data.total === 0 ? (
            <EmptyState title="Seu primeiro companheiro por aqui.">
              Adicione um pet e compartilhe as informações que ajudam no cuidado.
            </EmptyState>
          ) : (
            <ul className="dashboard-pets">
              {pets.data.items.slice(0, 3).map((p) => (
                <li key={p.id}>
                  <PawPrint aria-hidden="true" />
                  <div>
                    <h3>{p.name}</h3>
                    <p>{p.species_id === 'CAT' ? 'Gato' : 'Cachorro'}</p>
                  </div>
                  <Link to="/app/pets" aria-label={'Ver informações de ' + p.name}>
                    <ArrowRight aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
      <div className="care-cards">
        <Link className="dashboard-link" to="/app/perfil">
          <UserRound aria-hidden="true" />
          <h2>Meu cadastro</h2>
          <p>Informações para manter o contato.</p>
        </Link>
        <Link className="dashboard-link" to="/servicos">
          <Sparkles aria-hidden="true" />
          <h2>Conhecer serviços</h2>
          <p>Preço e duração por porte.</p>
        </Link>
      </div>
      <Link className="button button--primary" to="/app/agendar">
        Agendar um cuidado
      </Link>
      <Link to="/app/reservas">Acompanhar minhas reservas</Link>
    </div>
  );
}
