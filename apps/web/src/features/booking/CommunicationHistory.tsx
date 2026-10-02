import type { components } from '@petland/api-contract';
import { dateTime } from './api';

const labels: Record<string, string> = {
  book: 'Confirmação',
  reschedule: 'Reagendamento',
  cancel: 'Cancelamento',
  cancel_exception: 'Cancelamento pela equipe',
  complete: 'Pet pronto',
  reminder: 'Lembrete',
  legacy: 'Mensagem anterior',
};

export function CommunicationHistory({
  messages,
  timezone,
}: {
  messages: components['schemas']['CommunicationResponse'][];
  timezone: string;
}) {
  return (
    <section className="communication-history" aria-label="Comunicação da reserva">
      <h2>Comunicação</h2>
      <p>
        Aceito pelo servidor de e-mail indica envio SMTP; não confirma leitura ou entrega na caixa
        pessoal.
      </p>
      {!messages.length ? (
        <p>Nenhuma mensagem registrada.</p>
      ) : (
        <ol className="booking-history">
          {messages.map((m) => (
            <li key={m.id}>
              <strong>{labels[m.kind] || 'Aviso da reserva'}</strong>
              <span>
                {m.delivered_at
                  ? 'Aceito pelo servidor de e-mail'
                  : m.suppressed_at
                    ? 'Descartado após alteração da reserva'
                    : m.attempts
                      ? 'Reenvio agendado'
                      : 'Envio agendado'}
              </span>
              <small>
                {dateTime(m.delivered_at || m.suppressed_at || m.available_at, timezone)}
              </small>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
