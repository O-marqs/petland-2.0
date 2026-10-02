import { localEmailUrl } from '../lib/local-email';
import { Alert } from './Feedback';

export function LocalEmailNotice() {
  const url = localEmailUrl();
  if (!url) return null;
  return (
    <Alert title="Seus e-mails de teste estão aqui">
      <p>
        Neste ambiente local, as mensagens ficam na caixa de teste e não chegam à sua caixa pessoal.
        Procure a mensagem destinada ao e-mail que você cadastrou.
      </p>
      <a className="text-link" href={url} target="_blank" rel="noopener noreferrer">
        Abrir e-mails de teste
      </a>
    </Alert>
  );
}
