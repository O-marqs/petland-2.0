import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowRight, Check, RotateCcw } from 'lucide-react';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';
import { Alert, Badge, EmptyState, Skeleton } from '../../shared/ui/Feedback';

const schema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Informe um nome para testar o campo.')
    .max(60, 'Use até 60 caracteres.'),
});
type Values = z.infer<typeof schema>;
const palette = [
  ['Marca', 'brand-700', '#1F5D50'],
  ['Marfim', 'canvas', '#F7F5EF'],
  ['Superfície', 'surface', '#FFFFFF'],
  ['Terracota', 'accent-600', '#A94F2D'],
  ['Texto', 'text', '#243A35'],
  ['Suave', 'brand-50', '#E8F2EC'],
];

export default function DesignSystemPage() {
  const [validated, setValidated] = useState(false);
  const [feedback, setFeedback] = useState<'success' | 'error' | 'loading' | 'empty'>('empty');
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { name: '' } });
  return (
    <div className="container gallery">
      <header className="gallery-heading">
        <Badge>DESIGN SYSTEM · P01</Badge>
        <h1>
          Cuidar também
          <br />
          está nos detalhes.
        </h1>
        <p>
          Uma identidade acolhedora. Componentes claros, acessíveis e prontos para crescer juntos.
        </p>
      </header>
      <section className="gallery-section" aria-labelledby="palette-title">
        <div className="section-heading">
          <div>
            <span className="eyebrow">01 / IDENTIDADE</span>
            <h2 id="palette-title">As cores do cuidado.</h2>
          </div>
          <p>Verde profundo, marfim e um toque de terracota.</p>
        </div>
        <div className="palette">
          {palette.map(([name, token, hex]) => (
            <div key={token}>
              <div className="swatch" style={{ backgroundColor: `var(--${token})` }} />
              <strong>{name}</strong>
              <span>{hex}</span>
            </div>
          ))}
        </div>
      </section>
      <div className="gallery-columns">
        <section className="gallery-card" aria-labelledby="actions-title">
          <span className="eyebrow">02 / AÇÕES</span>
          <h2 id="actions-title">Um próximo passo claro.</h2>
          <p>Botões com foco visível, estados distintos e alvos confortáveis.</p>
          <div className="button-samples">
            <Button onClick={() => setFeedback('success')}>
              Confirmar exemplo <Check size={18} aria-hidden="true" />
            </Button>
            <Button variant="secondary" onClick={() => setFeedback('empty')}>
              Ver estado vazio <ArrowRight size={18} aria-hidden="true" />
            </Button>
            <Button variant="danger" onClick={() => setFeedback('error')}>
              Mostrar erro
            </Button>
            <Button busy>Carregando</Button>
            <Button disabled>Indisponível</Button>
          </div>
        </section>
        <section className="gallery-card" aria-labelledby="fields-title">
          <span className="eyebrow">03 / FORMULÁRIOS</span>
          <h2 id="fields-title">Clareza em cada campo.</h2>
          <p>Exemplo interativo: não cadastra um pet nem salva dados.</p>
          <form
            noValidate
            onSubmit={handleSubmit(() => setValidated(true))}
            onChange={() => setValidated(false)}
          >
            {errors.name && <Alert tone="error" title="Revise o campo indicado abaixo." />}
            <Input
              label="Nome de exemplo"
              required
              hint="Use um nome fictício. Até 60 caracteres."
              autoComplete="off"
              error={errors.name?.message}
              {...register('name')}
            />
            <div className="form-actions">
              <Button type="submit">Validar exemplo</Button>
              <Button
                variant="secondary"
                aria-label="Limpar exemplo"
                onClick={() => {
                  reset();
                  setValidated(false);
                }}
              >
                <RotateCcw size={18} aria-hidden="true" />
                Limpar
              </Button>
            </div>
            {validated && (
              <Alert tone="success" title="Exemplo validado.">
                Nenhum dado foi salvo.
              </Alert>
            )}
          </form>
        </section>
      </div>
      <section className="gallery-section" aria-labelledby="feedback-title">
        <div className="section-heading">
          <div>
            <span className="eyebrow">04 / FEEDBACK</span>
            <h2 id="feedback-title">Sempre um caminho de volta.</h2>
          </div>
          <p>Estados demonstrativos, identificados por texto e forma.</p>
        </div>
        <div className="state-picker" role="group" aria-label="Escolha um estado de demonstração">
          {(
            [
              { key: 'empty', label: 'Vazio' },
              { key: 'loading', label: 'Carregando' },
              { key: 'error', label: 'Erro' },
              { key: 'success', label: 'Sucesso' },
            ] as const
          ).map(({ key, label }) => (
            <button key={key} aria-pressed={feedback === key} onClick={() => setFeedback(key)}>
              {label}
            </button>
          ))}
        </div>
        <div className="feedback-preview">
          {feedback === 'empty' && (
            <EmptyState title="Um espaço para os próximos cuidados.">
              Este é um exemplo de estado vazio, sem consulta a pets ou agendamentos.
            </EmptyState>
          )}
          {feedback === 'loading' && <Skeleton label="Exemplo de carregamento" />}
          {feedback === 'error' && (
            <Alert tone="error" title="Não foi possível concluir agora.">
              <p>Exemplo de falha. Suas escolhas devem ser preservadas.</p>
              <Button variant="secondary" onClick={() => setFeedback('empty')}>
                Voltar ao exemplo
              </Button>
            </Alert>
          )}
          {feedback === 'success' && (
            <Alert tone="success" title="Ação de exemplo confirmada.">
              Demonstração visual. Nenhuma reserva foi criada.
            </Alert>
          )}
        </div>
      </section>
      <section className="typography-note">
        <span className="eyebrow">05 / TIPOGRAFIA & ACESSIBILIDADE</span>
        <h2>
          Gentileza para ler.
          <br />
          Simplicidade para usar.
        </h2>
        <p>
          Manrope nos títulos. Inter no corpo. Fontes locais, foco visível, navegação por teclado e
          respeito à redução de movimento.
        </p>
        <p className="muted">
          WCAG 2.2 AA é a meta do produto. Esta galeria não representa uma certificação de
          conformidade.
        </p>
      </section>
    </div>
  );
}
