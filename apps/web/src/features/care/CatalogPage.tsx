import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Clock3, Plus, Sparkles } from 'lucide-react';
import {
  careApi,
  money,
  sizes,
  sizeLabels,
  type Service,
  type ServiceInput,
  type Size,
} from './api';
import { LoadError, Pagination, SaveError } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Select, TextArea } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, EmptyState, Skeleton } from '../../shared/ui/Feedback';

const schema = z
  .object({
    name: z.string().trim().min(2, 'Informe o nome do serviço.').max(100),
    description: z.string().trim().max(1500),
    species_ids: z.array(z.string()).min(1, 'Selecione pelo menos uma espécie.'),
    active: z.boolean(),
    options: z.array(
      z.object({
        size: z.enum(['SMALL', 'MEDIUM', 'LARGE']),
        enabled: z.boolean(),
        price: z.string(),
        duration: z.string(),
      }),
    ),
  })
  .superRefine((data, ctx) => {
    if (!data.options.some((o) => o.enabled))
      ctx.addIssue({ code: 'custom', path: ['options'], message: 'Ofereça pelo menos um porte.' });
    data.options.forEach((o, i) => {
      if (!o.enabled) return;
      if (!/^\d{1,7}([.,]\d{1,2})?$/.test(o.price))
        ctx.addIssue({
          code: 'custom',
          path: ['options', i, 'price'],
          message: 'Informe um valor positivo ou zero, com até 2 casas decimais.',
        });
      if (!/^\d+$/.test(o.duration) || +o.duration < 1 || +o.duration > 1440)
        ctx.addIssue({
          code: 'custom',
          path: ['options', i, 'duration'],
          message: 'Informe de 1 a 1.440 minutos.',
        });
    });
  });
type Fields = z.infer<typeof schema>;

function ServiceForm({
  existing,
  done,
  cancel,
}: {
  existing?: Service;
  done: () => void;
  cancel: () => void;
}) {
  const species = useQuery({
    queryKey: ['care', 'species'],
    queryFn: ({ signal }) => careApi.species(signal),
  });
  const form = useForm<Fields>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: existing?.name || '',
      description: existing?.description || '',
      species_ids: existing?.species_ids || [],
      active: existing?.active || false,
      options: sizes.map((size) => {
        const o = existing?.options.find((o) => o.size === size);
        return {
          size,
          enabled: !!o,
          price: o?.price?.toString() || '',
          duration: o?.duration_minutes?.toString() || '',
        };
      }),
    },
  });
  const options = form.watch('options');
  const mutation = useMutation({
    mutationFn: (data: Fields) => {
      const body: ServiceInput = {
        name: data.name,
        description: data.description,
        active: data.active,
        species_ids: data.species_ids,
        options: data.options
          .filter((o) => o.enabled)
          .map((o) => ({
            size: o.size,
            price: o.price.replace(',', '.'),
            duration_minutes: Number(o.duration),
          })),
      };
      return careApi.saveService(body, existing);
    },
    onSuccess: done,
  });
  return (
    <section className="identity-card care-editor">
      <h2>{existing ? 'Editar serviço' : 'Novo serviço'}</h2>
      <p>
        Defina as condições de cada porte. Ative o serviço quando ele estiver pronto para aparecer
        no catálogo.
      </p>
      <form noValidate onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
        <Input
          label="Nome do serviço"
          required
          autoFocus
          maxLength={100}
          {...form.register('name')}
          error={form.formState.errors.name?.message}
        />
        <TextArea label="Descrição" rows={3} maxLength={1500} {...form.register('description')} />
        <fieldset className="care-fieldset">
          <legend>Espécies atendidas (obrigatório)</legend>
          {species.isPending ? (
            <Skeleton label="Carregando espécies" />
          ) : species.isError ? (
            <LoadError error={species.error} retry={() => void species.refetch()} />
          ) : (
            species.data.map((s) => (
              <label className="care-check" key={s.id}>
                <input type="checkbox" value={s.id} {...form.register('species_ids')} />
                {s.name}
              </label>
            ))
          )}
          {form.formState.errors.species_ids && (
            <p className="field-error" role="alert">
              {form.formState.errors.species_ids.message}
            </p>
          )}
        </fieldset>
        <fieldset className="care-fieldset">
          <legend>Preço e duração por porte</legend>
          <p>Marque os portes oferecidos e preencha as condições de cada um.</p>
          {options.map((o, i) => (
            <div className="service-option-edit" key={o.size}>
              <label className="care-check">
                <input type="checkbox" {...form.register(`options.${i}.enabled`)} />
                Oferecer porte {sizeLabels[o.size].toLowerCase()}
              </label>
              {o.enabled && (
                <div className="care-form-grid">
                  <Input
                    label={'Preço — ' + sizeLabels[o.size] + ' (R$)'}
                    required
                    inputMode="decimal"
                    {...form.register(`options.${i}.price`)}
                    error={form.formState.errors.options?.[i]?.price?.message}
                  />
                  <Input
                    label={'Duração — ' + sizeLabels[o.size] + ' (minutos)'}
                    required
                    inputMode="numeric"
                    {...form.register(`options.${i}.duration`)}
                    error={form.formState.errors.options?.[i]?.duration?.message}
                  />
                </div>
              )}
            </div>
          ))}
          {form.formState.errors.options?.message && (
            <p className="field-error" role="alert">
              {form.formState.errors.options.message}
            </p>
          )}
        </fieldset>
        <label className="care-check">
          <input type="checkbox" {...form.register('active')} />
          Serviço ativo no catálogo público
        </label>
        {mutation.isError && <SaveError error={mutation.error} />}
        <div className="care-actions">
          <Button type="submit" busy={mutation.isPending} disabled={!species.data}>
            Salvar serviço
          </Button>
          <Button variant="secondary" disabled={mutation.isPending} onClick={cancel}>
            Voltar para serviços
          </Button>
        </div>
      </form>
    </section>
  );
}

function Prices({ service }: { service: Service }) {
  return (
    <dl className="service-prices">
      {sizes.flatMap((size) => {
        const option = service.options.find((o) => o.size === size);
        return option
          ? [
              <div key={size}>
                <dt>Porte {sizeLabels[size].toLowerCase()}</dt>
                <dd>
                  <strong>{money(option.price)}</strong>
                  <span>
                    <Clock3 size={14} aria-hidden="true" />
                    {option.duration_minutes} min
                  </span>
                </dd>
              </div>,
            ]
          : [];
      })}
    </dl>
  );
}

export default function CatalogPage({ staff = false }: { staff?: boolean }) {
  const { serviceId } = useParams();
  const cache = useQueryClient();
  const [speciesId, setSpeciesId] = useState('');
  const [size, setSize] = useState<Size | ''>('');
  const [offset, setOffset] = useState(0);
  const [editor, setEditor] = useState<Service | 'new' | null>(null);
  const [saved, setSaved] = useState(false);
  const species = useQuery({
    queryKey: ['care', 'species'],
    queryFn: ({ signal }) => careApi.species(signal),
  });
  const list = useQuery({
    queryKey: ['care', 'services', staff, offset, speciesId, size],
    queryFn: ({ signal }) =>
      careApi.services(staff, offset, speciesId || undefined, size || undefined, signal),
    enabled: !serviceId,
  });
  const detail = useQuery({
    queryKey: ['care', 'service', serviceId],
    queryFn: ({ signal }) => careApi.service(serviceId!, signal),
    enabled: !!serviceId,
  });
  const refresh = async () => {
    await cache.invalidateQueries({ queryKey: ['care', 'services'] });
    await cache.invalidateQueries({ queryKey: ['care', 'service'] });
  };
  return (
    <div className={staff ? 'care-stack' : 'container care-public care-stack'}>
      <header className="area-heading">
        <span className="eyebrow">{staff ? 'EQUIPE PETLAND' : 'CUIDADO COM CLAREZA'}</span>
        <h1>{staff ? 'Serviços' : 'Um cuidado para cada pet.'}</h1>
        <p>
          {staff
            ? 'Preço, tempo e compatibilidade sempre atualizados.'
            : 'Conheça os serviços, os portes atendidos e o tempo previsto para cada cuidado.'}
        </p>
      </header>
      {editor ? (
        <ServiceForm
          existing={editor === 'new' ? undefined : editor}
          done={() => {
            void refresh().then(() => {
              setEditor(null);
              setSaved(true);
            });
          }}
          cancel={() => {
            setEditor(null);
            void refresh();
          }}
        />
      ) : serviceId ? (
        detail.isPending ? (
          <Skeleton label="Carregando serviço" />
        ) : detail.isError ? (
          <LoadError error={detail.error} retry={() => void detail.refetch()} />
        ) : (
          <section className="identity-card service-detail">
            <Sparkles size={36} aria-hidden="true" />
            <h2>{detail.data.name}</h2>
            <p>{detail.data.description || 'Confira abaixo as condições por porte.'}</p>
            <p>
              Espécies:{' '}
              {detail.data.species_ids
                .map((id) => species.data?.find((s) => s.id === id)?.name || id)
                .join(', ')}
            </p>
            <Prices service={detail.data} />
            <p className="care-note">
              O agendamento online estará disponível em uma próxima etapa.
            </p>
            <Link className="button button--secondary" to="/servicos">
              Voltar aos serviços
            </Link>
          </section>
        )
      ) : (
        <>
          {saved && (
            <Alert tone="success" title="Serviço salvo">
              As condições do catálogo foram atualizadas.
            </Alert>
          )}
          {staff ? (
            <div className="care-toolbar">
              <p>Serviços ativos e inativos</p>
              <Button
                onClick={() => {
                  setEditor('new');
                  setSaved(false);
                }}
              >
                <Plus size={18} aria-hidden="true" /> Novo serviço
              </Button>
            </div>
          ) : (
            <div className="catalog-filters">
              <Select
                label="Espécie"
                value={speciesId}
                onChange={(e) => {
                  setSpeciesId(e.target.value);
                  setOffset(0);
                }}
              >
                <option value="">Todas as espécies</option>
                {species.data?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
              <Select
                label="Porte"
                value={size}
                onChange={(e) => {
                  setSize(e.target.value as Size | '');
                  setOffset(0);
                }}
              >
                <option value="">Todos os portes</option>
                {sizes.map((s) => (
                  <option key={s} value={s}>
                    {sizeLabels[s]}
                  </option>
                ))}
              </Select>
            </div>
          )}
          {species.isError && (
            <LoadError error={species.error} retry={() => void species.refetch()} />
          )}
          {list.isPending ? (
            <Skeleton label="Carregando serviços" />
          ) : list.isError ? (
            <LoadError error={list.error} retry={() => void list.refetch()} />
          ) : (
            <>
              {list.data.items.length === 0 ? (
                <EmptyState
                  title={
                    staff ? 'Seu catálogo começa aqui.' : 'Nenhum serviço disponível neste momento.'
                  }
                >
                  {staff
                    ? 'Cadastre os serviços com preço e duração por porte. Ative-os para exibir no catálogo.'
                    : speciesId || size
                      ? 'Tente outra espécie ou porte.'
                      : 'Os serviços aparecerão aqui quando forem disponibilizados pela equipe.'}
                </EmptyState>
              ) : (
                <ul className="care-cards service-cards">
                  {list.data.items.map((s) => (
                    <li className="service-card" key={s.id}>
                      <div className="pet-card-top">
                        <span className="service-mark">
                          <Sparkles aria-hidden="true" />
                        </span>
                        {staff && <Badge>{s.active ? 'ATIVO' : 'INATIVO'}</Badge>}
                      </div>
                      <h2>{s.name}</h2>
                      <p>{s.description || 'Condições para cada porte, com clareza.'}</p>
                      <small>
                        {s.species_ids
                          .map((id) => species.data?.find((x) => x.id === id)?.name || id)
                          .join(' · ')}
                      </small>
                      <Prices service={s} />
                      {staff ? (
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setEditor(s);
                            setSaved(false);
                          }}
                        >
                          Editar {s.name}
                        </Button>
                      ) : (
                        <Link className="button button--secondary" to={'/servicos/' + s.id}>
                          Ver detalhes de {s.name}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              <Pagination offset={offset} total={list.data.total} change={setOffset} />
            </>
          )}
          {!staff && (
            <div className="catalog-note">
              <PawNote />
              <div>
                <h2>Seus pets também têm um espaço por aqui.</h2>
                <p>Crie sua conta e organize as informações que ajudam a equipe a cuidar deles.</p>
                <Link to="/app/pets">Conhecer minha área →</Link>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
function PawNote() {
  return <Sparkles size={32} aria-hidden="true" />;
}
