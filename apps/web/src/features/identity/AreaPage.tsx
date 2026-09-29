import { Link, useLocation, useOutletContext } from 'react-router-dom';
import { Check, ArrowRight } from 'lucide-react';
import { Badge, EmptyState } from '../../shared/ui/Feedback';
import type { Account } from './api';

export default function AreaPage() {
  const user = useOutletContext<Account>();
  const { pathname } = useLocation();
  const area = pathname.startsWith('/gestao')
    ? 'admin'
    : pathname.startsWith('/operacao')
      ? 'employee'
      : 'customer';
  return (
    <>
      <header className="area-heading">
        <span className="eyebrow">
          {area === 'admin'
            ? 'ADMINISTRAÇÃO'
            : area === 'employee'
              ? 'EQUIPE PETLAND'
              : 'BEM-VINDO AO SEU ESPAÇO'}
        </span>
        <h1>Olá, {user.display_name.split(' ')[0]}.</h1>
        <p>
          {area === 'customer'
            ? 'Sua conta já tem um lugar por aqui. Vamos cuidar dos próximos passos juntos.'
            : 'Seu acesso está pronto para apoiar o cuidado de cada dia.'}
        </p>
      </header>
      <section className="account-ready">
        <div>
          <Badge>
            <Check size={15} aria-hidden="true" /> E-MAIL CONFIRMADO
          </Badge>
          <h2>Um acesso que é só seu.</h2>
          <p>Confira seus dados e gerencie a segurança da sua conta.</p>
        </div>
        <Link className="button button--secondary" to="/app/conta">
          Minha conta
          <ArrowRight size={18} aria-hidden="true" />
        </Link>
      </section>
      {area === 'admin' && (
        <section className="identity-card">
          <h2>Pessoas e permissões</h2>
          <p>Convide a equipe e gerencie os perfis e o acesso das contas cadastradas.</p>
          <Link className="button button--primary" to="/gestao/acessos">
            Gerenciar acessos
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </section>
      )}
      <section className="care-cards">
        <Link className="dashboard-link" to="/operacao/clientes">
          <h2>Clientes e pets</h2>
          <p>Cadastros, contatos e informações para cuidar.</p>
        </Link>
        <Link className="dashboard-link" to="/operacao/servicos">
          <h2>Serviços</h2>
          <p>Configure preço e duração por porte.</p>
        </Link>
      </section>
      <EmptyState
        title={
          area === 'customer' ? 'Mais cuidado está a caminho.' : 'A operação está em construção.'
        }
      >
        {area === 'customer'
          ? 'Organize os pets, conheça os serviços e acompanhe suas reservas.'
          : 'Gerencie clientes, pets, serviços e reservas. Configure a capacidade em Equipe e horários.'}
      </EmptyState>
    </>
  );
}
