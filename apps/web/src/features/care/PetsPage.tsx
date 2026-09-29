import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Cat, Dog, Plus, PawPrint } from 'lucide-react';
import { careApi, sizes, sizeLabels, type Pet, type PetInput } from './api';
import { LoadError, Pagination, SaveError } from './Feedback';
import { Input } from '../../shared/ui/Input';
import { Select, TextArea } from '../../shared/ui/Select';
import { Button } from '../../shared/ui/Button';
import { Alert, Badge, EmptyState, Skeleton } from '../../shared/ui/Feedback';

const schema = z
  .object({
    name: z.string().trim().min(1, 'Informe o nome do pet.').max(80),
    species_id: z.string().min(1, 'Selecione a espécie.'),
    breed_id: z.string(),
    size: z.enum(['SMALL', 'MEDIUM', 'LARGE']),
    sex: z.enum(['UNKNOWN', 'FEMALE', 'MALE']),
    birth_date: z.string(),
    birth_estimated: z.boolean(),
    care_notes: z.string().max(1000, 'Use até 1.000 caracteres.'),
  })
  .superRefine((v, ctx) => {
    const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo' }).format(
      new Date(),
    );
    if (v.birth_date && v.birth_date > today)
      ctx.addIssue({
        code: 'custom',
        path: ['birth_date'],
        message: 'A data não pode estar no futuro.',
      });
    if (!v.birth_date && v.birth_estimated)
      ctx.addIssue({
        code: 'custom',
        path: ['birth_date'],
        message: 'Informe a data estimada ou desmarque a estimativa.',
      });
  });
type Fields = z.infer<typeof schema>;

function PetForm({
  existing,
  customerId,
  done,
  cancel,
}: {
  existing?: Pet;
  customerId?: string;
  done: () => void;
  cancel: () => void;
}) {
  const form = useForm<Fields>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: existing?.name || '',
      species_id: existing?.species_id || '',
      breed_id: existing?.breed_id || '',
      size: existing?.size || 'SMALL',
      sex: existing?.sex || 'UNKNOWN',
      birth_date: existing?.birth_date || '',
      birth_estimated: existing?.birth_estimated || false,
      care_notes: existing?.care_notes || '',
    },
  });
  const speciesId = form.watch('species_id');
  const species = useQuery({
    queryKey: ['care', 'species'],
    queryFn: ({ signal }) => careApi.species(signal),
  });
  const breeds = useQuery({
    queryKey: ['care', 'breeds', speciesId],
    queryFn: ({ signal }) => careApi.breeds(speciesId, signal),
    enabled: !!speciesId,
  });
  const mutation = useMutation({
    mutationFn: (data: Fields) => {
      const body: PetInput = {
        ...data,
        breed_id: data.breed_id || null,
        birth_date: data.birth_date || null,
      };
      return careApi.savePet(body, customerId, existing);
    },
    onSuccess: done,
  });
  return (
    <section className="identity-card care-editor" aria-labelledby="pet-form-title">
      <h2 id="pet-form-title">
        {existing ? 'Editar ' + existing.name : 'Vamos conhecer seu companheiro?'}
      </h2>
      <p>
        Espécie e porte ajudam a encontrar os cuidados adequados. Raça e nascimento podem ficar em
        branco.
      </p>
      <form noValidate onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
        <Input
          label="Nome do pet"
          required
          autoFocus
          maxLength={80}
          {...form.register('name')}
          error={form.formState.errors.name?.message}
        />
        <div className="care-form-grid">
          <Select
            label="Espécie"
            required
            {...form.register('species_id', { onChange: () => form.setValue('breed_id', '') })}
            error={form.formState.errors.species_id?.message}
          >
            <option value="">Selecione a espécie</option>
            {species.data?.map((s) => (
              <option value={s.id} key={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
          <Select
            label="Raça"
            disabled={!speciesId || breeds.isPending}
            {...form.register('breed_id')}
            hint="Não sabe? Deixe como desconhecida."
          >
            <option value="">Desconhecida / não listada</option>
            {breeds.data?.map((b) => (
              <option value={b.id} key={b.id}>
                {b.name}
              </option>
            ))}
          </Select>
          <Select
            label="Porte"
            required
            {...form.register('size')}
            error={form.formState.errors.size?.message}
          >
            {sizes.map((s) => (
              <option value={s} key={s}>
                {sizeLabels[s]}
              </option>
            ))}
          </Select>
          <Select label="Sexo" {...form.register('sex')}>
            <option value="UNKNOWN">Não informado</option>
            <option value="FEMALE">Fêmea</option>
            <option value="MALE">Macho</option>
          </Select>
        </div>
        {species.isError && (
          <LoadError error={species.error} retry={() => void species.refetch()} />
        )}
        {breeds.isError && <LoadError error={breeds.error} retry={() => void breeds.refetch()} />}
        <Input
          label="Data de nascimento"
          type="date"
          {...form.register('birth_date')}
          error={form.formState.errors.birth_date?.message}
        />
        <label className="care-check">
          <input type="checkbox" {...form.register('birth_estimated')} /> Esta é uma data estimada
        </label>
        <TextArea
          label="Cuidados importantes"
          rows={3}
          maxLength={1000}
          {...form.register('care_notes')}
          hint="Compartilhe apenas o que ajuda no cuidado. Estas informações são visíveis ao cliente e à equipe."
          error={form.formState.errors.care_notes?.message}
        />
        {mutation.isError && <SaveError error={mutation.error} />}
        <div className="care-actions">
          <Button
            type="submit"
            busy={mutation.isPending}
            disabled={!species.data || breeds.isError}
          >
            Salvar pet
          </Button>
          <Button variant="secondary" onClick={cancel} disabled={mutation.isPending}>
            Voltar para pets
          </Button>
        </div>
      </form>
    </section>
  );
}

export default function PetsPage() {
  const { customerId } = useParams();
  const cache = useQueryClient();
  const [archived, setArchived] = useState(false);
  const [offset, setOffset] = useState(0);
  const [editor, setEditor] = useState<Pet | 'new' | null>(null);
  const [confirm, setConfirm] = useState<Pet | null>(null);
  const [message, setMessage] = useState('');
  const profile = useQuery({
    queryKey: ['care', 'customer', customerId || 'me'],
    queryFn: ({ signal }) =>
      customerId ? careApi.customer(customerId, signal) : careApi.profile(signal),
  });
  const list = useQuery({
    queryKey: ['care', 'pets', customerId || 'me', archived, offset],
    queryFn: ({ signal }) => careApi.pets(customerId, archived, offset, signal),
    enabled: !!profile.data,
  });
  const species = useQuery({
    queryKey: ['care', 'species'],
    queryFn: ({ signal }) => careApi.species(signal),
  });
  const refresh = async () => {
    await cache.invalidateQueries({ queryKey: ['care'] });
  };
  const archive = useMutation({
    mutationFn: (pet: Pet) => careApi.archive(pet, !pet.archived_at, customerId),
    onSuccess: async (pet) => {
      await refresh();
      setConfirm(null);
      setMessage(
        pet.archived_at ? 'Pet arquivado. Suas informações foram preservadas.' : 'Pet restaurado.',
      );
    },
  });
  return (
    <>
      <header className="area-heading">
        <span className="eyebrow">{customerId ? 'CADASTRO ASSISTIDO' : 'SEU ESPAÇO'}</span>
        <h1>{customerId ? 'Pets do cliente' : 'Meus pets'}</h1>
        <p>
          {customerId && profile.data ? profile.data.name + ' · ' : ''}Seus companheiros, em um só
          lugar.
        </p>
      </header>
      {customerId && (
        <Link to={'/operacao/clientes/' + customerId}>Voltar ao cadastro do cliente</Link>
      )}
      {profile.isPending ? (
        <Skeleton label="Carregando cadastro" />
      ) : profile.isError ? (
        <LoadError error={profile.error} retry={() => void profile.refetch()} />
      ) : !profile.data ? (
        <section className="identity-card">
          <h2>Primeiro, vamos nos conhecer.</h2>
          <p>
            Complete seu cadastro de contato para adicionar seus pets. Se a equipe já fez seu
            cadastro, peça o link de vínculo.
          </p>
          <Link className="button button--primary" to="/app/perfil">
            Completar meu cadastro
          </Link>
        </section>
      ) : editor ? (
        <PetForm
          existing={editor === 'new' ? undefined : editor}
          customerId={customerId}
          cancel={() => {
            setEditor(null);
            void refresh();
          }}
          done={() => {
            void refresh().then(() => {
              setEditor(null);
              setMessage('Pet salvo com sucesso.');
            });
          }}
        />
      ) : (
        <div className="care-stack">
          {message && (
            <Alert tone="success" title="Tudo certo">
              {message}
            </Alert>
          )}
          <div className="care-toolbar">
            <div className="care-actions" role="group" aria-label="Situação dos pets">
              <Button
                variant={archived ? 'secondary' : 'primary'}
                aria-pressed={!archived}
                onClick={() => {
                  setArchived(false);
                  setOffset(0);
                  setConfirm(null);
                }}
              >
                Ativos
              </Button>
              <Button
                variant={archived ? 'primary' : 'secondary'}
                aria-pressed={archived}
                onClick={() => {
                  setArchived(true);
                  setOffset(0);
                  setConfirm(null);
                }}
              >
                Arquivados
              </Button>
            </div>
            <Button
              onClick={() => {
                setEditor('new');
                setMessage('');
              }}
            >
              <Plus size={18} aria-hidden="true" /> Adicionar pet
            </Button>
          </div>
          {list.isPending ? (
            <Skeleton label="Carregando pets" />
          ) : list.isError ? (
            <LoadError error={list.error} retry={() => void list.refetch()} />
          ) : (
            <>
              {list.data.items.length === 0 ? (
                <EmptyState
                  title={archived ? 'Nenhum pet arquivado' : 'Vamos conhecer seu companheiro?'}
                >
                  {archived
                    ? 'Os pets arquivados aparecerão aqui.'
                    : 'Adicione seu primeiro pet com as informações que ajudam no cuidado.'}
                </EmptyState>
              ) : (
                <ul className="care-cards">
                  {list.data.items.map((p) => (
                    <li className="pet-card" key={p.id}>
                      <div className="pet-card-top">
                        <span className="pet-mark">
                          {p.species_id === 'CAT' ? (
                            <Cat aria-hidden="true" />
                          ) : p.species_id === 'DOG' ? (
                            <Dog aria-hidden="true" />
                          ) : (
                            <PawPrint aria-hidden="true" />
                          )}
                        </span>
                        <Badge>{p.archived_at ? 'ARQUIVADO' : sizeLabels[p.size]}</Badge>
                      </div>
                      <h2>{p.name}</h2>
                      <p>
                        {species.data?.find((s) => s.id === p.species_id)?.name || p.species_id} ·
                        Porte {sizeLabels[p.size].toLowerCase()}
                      </p>
                      {p.birth_date && (
                        <small>
                          Nascimento {p.birth_estimated ? 'estimado' : ''}:{' '}
                          {new Intl.DateTimeFormat('pt-BR', { timeZone: 'UTC' }).format(
                            new Date(p.birth_date + 'T12:00:00Z'),
                          )}
                        </small>
                      )}
                      <p className="pet-notes">
                        {p.care_notes || 'Nenhum cuidado adicional informado.'}
                      </p>
                      <div className="care-actions">
                        {!p.archived_at && (
                          <Button
                            variant="secondary"
                            onClick={() => {
                              setEditor(p);
                              setMessage('');
                            }}
                          >
                            Editar {p.name}
                          </Button>
                        )}
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setConfirm(p);
                            archive.reset();
                          }}
                        >
                          {p.archived_at ? 'Restaurar' : 'Arquivar'} {p.name}
                        </Button>
                      </div>
                      {confirm?.id === p.id && (
                        <div className="care-confirm">
                          <p>
                            {p.archived_at
                              ? 'Restaurar este pet para os próximos cuidados?'
                              : 'Arquivar este pet? Seus dados serão preservados e você poderá restaurá-lo.'}
                          </p>
                          <div className="care-actions">
                            <Button busy={archive.isPending} onClick={() => archive.mutate(p)}>
                              Confirmar {p.archived_at ? 'restauração' : 'arquivamento'}
                            </Button>
                            <Button
                              variant="secondary"
                              disabled={archive.isPending}
                              onClick={() => setConfirm(null)}
                            >
                              Voltar
                            </Button>
                          </div>
                          {archive.isError && (
                            <SaveError
                              error={archive.error}
                              reload={() => {
                                setConfirm(null);
                                void refresh();
                              }}
                            />
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              <Pagination offset={offset} total={list.data.total} change={setOffset} />
            </>
          )}
        </div>
      )}
    </>
  );
}
