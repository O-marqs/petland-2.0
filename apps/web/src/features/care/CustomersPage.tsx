import { useState } from 'react';
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, ArrowRight, UserRound } from 'lucide-react';
import { careApi, type Customer } from './api';
import { LoadError, Pagination, SaveError } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { TextArea } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, EmptyState, Skeleton } from '../../shared/ui/Feedback';
import type { Account } from '../identity/api';

const schema = z.object({
  name: z.string().trim().min(2, 'Informe o nome completo.').max(100),
  email: z.email('Informe um e-mail válido.'),
  phone: z
    .string()
    .max(25)
    .refine(
      (v) =>
        !v ||
        (/^[0-9+() .-]+$/.test(v) &&
          v.replace(/\D/g, '').length >= 10 &&
          v.replace(/\D/g, '').length <= 15),
      'Informe telefone com DDD.',
    ),
  address: z.string().trim().max(500, 'Use até 500 caracteres.'),
});
type Fields = z.infer<typeof schema>;

export function CustomerForm({
  existing,
  staff,
  reload,
}: {
  existing?: Customer | null;
  staff: boolean;
  reload: () => void;
}) {
  const account = useOutletContext<Account>();
  const cache = useQueryClient();
  const navigate = useNavigate();
  const [saved, setSaved] = useState(false);
  const [baseline, setBaseline] = useState(existing);
  const form = useForm<Fields>({
    resolver: zodResolver(schema),
    defaultValues: existing || {
      name: staff ? '' : account.display_name,
      email: staff ? '' : account.email,
      phone: '',
      address: '',
    },
  });
  const mutation = useMutation({
    mutationFn: (data: Fields) => careApi.saveCustomer(data, staff, baseline),
    onSuccess: async (data) => {
      setBaseline(data);
      await cache.invalidateQueries({ queryKey: ['care'] });
      form.reset(data);
      setSaved(true);
      if (staff && !existing) navigate('/operacao/clientes/' + data.id, { replace: true });
    },
  });
  const invitation = useMutation({ mutationFn: () => careApi.invite(existing!.id) });
  return (
    <div className="care-stack">
      {saved && (
        <Alert tone="success" title="Cadastro salvo">
          As informações foram atualizadas.
        </Alert>
      )}
      <section className="identity-card">
        <h2>{staff ? 'Dados do cliente' : 'Seus dados de contato'}</h2>
        <p>Nome e e-mail identificam o cadastro. Telefone e endereço são opcionais.</p>
        <form
          noValidate
          onSubmit={form.handleSubmit((data) => {
            setSaved(false);
            mutation.mutate(data);
          })}
        >
          <Input
            label="Nome completo"
            required
            autoComplete="name"
            {...form.register('name')}
            error={form.formState.errors.name?.message}
          />
          <Input
            label="E-mail"
            type="email"
            required
            autoComplete="email"
            readOnly={!staff || existing?.linked}
            {...form.register('email')}
            error={form.formState.errors.email?.message}
            hint={
              !staff || existing?.linked
                ? 'Este é o e-mail confirmado da conta.'
                : 'Um e-mail igual ao de uma conta não vincula os cadastros automaticamente.'
            }
          />
          <Input
            label="Telefone com DDD"
            type="tel"
            autoComplete="tel"
            {...form.register('phone')}
            error={form.formState.errors.phone?.message}
          />
          <TextArea
            label="Endereço"
            autoComplete="street-address"
            rows={3}
            maxLength={500}
            {...form.register('address')}
            error={form.formState.errors.address?.message}
          />
          {mutation.isError && <SaveError error={mutation.error} reload={reload} />}
          <div className="care-actions">
            <Button busy={mutation.isPending} type="submit">
              Salvar cadastro
            </Button>
            {staff && <Link to="/operacao/clientes">Voltar para clientes</Link>}
          </div>
        </form>
      </section>
      {existing && (
        <section className="identity-card">
          <Badge>{existing.linked ? 'CONTA VINCULADA' : 'CADASTRO DA EQUIPE'}</Badge>
          <h2>Companheiros de cada dia</h2>
          <p>Cadastre e mantenha as informações que ajudam no cuidado dos pets.</p>
          <Link
            className="button button--secondary"
            to={staff ? '/operacao/clientes/' + existing.id + '/pets' : '/app/pets'}
          >
            Ver pets <ArrowRight size={18} aria-hidden="true" />
          </Link>
          <Link
            className="button button--primary"
            to={staff ? '/operacao/clientes/' + existing.id + '/agendar' : '/app/agendar'}
          >
            Agendar um cuidado
          </Link>
          {staff && !existing.linked && (
            <div className="care-stack">
              <p>
                Envie um link para o cliente acessar este cadastro e seus pets pela própria conta. O
                vínculo exige o mesmo e-mail confirmado e uma confirmação do cliente.
              </p>
              <Button
                variant="secondary"
                busy={invitation.isPending}
                onClick={() => invitation.mutate()}
              >
                Enviar link de vínculo
              </Button>
              {invitation.isSuccess && (
                <Alert tone="success" title="Link solicitado">
                  {invitation.data.message}
                </Alert>
              )}
              {invitation.isError && <SaveError error={invitation.error} />}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default function CustomersPage({ profile = false }: { profile?: boolean }) {
  const { customerId } = useParams();
  const editing = profile || !!customerId;
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [reset, setReset] = useState(0);
  const query = useQuery({
    queryKey: ['care', 'customer', profile ? 'me' : customerId],
    queryFn: ({ signal }) =>
      profile ? careApi.profile(signal) : careApi.customer(customerId!, signal),
    enabled: editing && customerId !== 'novo',
  });
  const list = useQuery({
    queryKey: ['care', 'customers', search, offset],
    queryFn: ({ signal }) => careApi.customers(search, offset, signal),
    enabled: !editing,
  });
  if (editing)
    return (
      <>
        <header className="area-heading">
          <span className="eyebrow">{profile ? 'SEU ESPAÇO' : 'CADASTRO ASSISTIDO'}</span>
          <h1>
            {profile
              ? 'Meu cadastro'
              : customerId === 'novo'
                ? 'Novo cliente'
                : 'Cadastro do cliente'}
          </h1>
          <p>
            {profile
              ? 'Informações para manter o cuidado por perto.'
              : 'Contato e pets reunidos no mesmo lugar.'}
          </p>
        </header>
        {customerId !== 'novo' && query.isPending ? (
          <Skeleton label="Carregando cadastro" />
        ) : query.isError ? (
          <LoadError error={query.error} retry={() => void query.refetch()} />
        ) : (
          <>
            <CustomerForm
              key={String(reset) + (customerId || 'me')}
              existing={query.data}
              staff={!profile}
              reload={() => {
                void query.refetch().then(() => setReset((v) => v + 1));
              }}
            />
            {profile && !query.data && (
              <p className="care-note">
                Já tem cadastro na loja? Peça à equipe o link de vínculo antes de criar outro
                cadastro.
              </p>
            )}
          </>
        )}
      </>
    );
  return (
    <>
      <header className="area-heading">
        <span className="eyebrow">EQUIPE PETLAND</span>
        <h1>Clientes</h1>
        <p>Cada cuidado começa por conhecer quem está do outro lado.</p>
      </header>
      <div className="care-toolbar">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSearch(q);
            setOffset(0);
          }}
        >
          <Input
            label="Buscar cliente"
            value={q}
            maxLength={100}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Nome, e-mail ou telefone"
          />
          <Button variant="secondary" type="submit">
            Buscar
          </Button>
        </form>
        <Link className="button button--primary" to="/operacao/clientes/novo">
          <Plus size={18} aria-hidden="true" /> Novo cliente
        </Link>
      </div>
      {list.isPending ? (
        <Skeleton label="Carregando clientes" />
      ) : list.isError ? (
        <LoadError error={list.error} retry={() => void list.refetch()} />
      ) : (
        <>
          {list.data.items.length === 0 ? (
            <EmptyState
              title={search ? 'Nenhum cliente encontrado' : 'Vamos conhecer seus clientes?'}
            >
              {search
                ? 'Tente outro nome, e-mail ou telefone.'
                : 'O primeiro cadastro pode ser feito aqui pela equipe.'}
            </EmptyState>
          ) : (
            <ul className="care-list">
              {list.data.items.map((c) => (
                <li key={c.id}>
                  <div className="care-avatar">
                    <UserRound aria-hidden="true" />
                  </div>
                  <div>
                    <h2>
                      <Link to={'/operacao/clientes/' + c.id}>{c.name}</Link>
                    </h2>
                    <p>{c.email}</p>
                    <small>{c.phone || 'Telefone não informado'}</small>
                  </div>
                  <Badge>{c.linked ? 'VINCULADO' : 'SEM CONTA'}</Badge>
                  <Link
                    className="care-row-link"
                    to={'/operacao/clientes/' + c.id}
                    aria-label={'Abrir cadastro de ' + c.name}
                  >
                    <ArrowRight aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <Pagination offset={offset} total={list.data.total} change={setOffset} />
        </>
      )}
    </>
  );
}
