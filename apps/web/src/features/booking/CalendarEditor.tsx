import { type Calendar } from './api';
import { Button } from '../../shared/ui/Button';
import { Input } from '../../shared/ui/Input';

const weekdays = [
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
  'Domingo',
];
const time = (minute: number) =>
  minute < 0
    ? ''
    : String(Math.floor(minute / 60)).padStart(2, '0') + ':' + String(minute % 60).padStart(2, '0');
const minutes = (value: string) => {
  const [h, m] = value.split(':').map(Number);
  return h * 60 + m;
};
type Window = Calendar['weekly'][number]['windows'][number];

function Windows({
  values,
  change,
  label,
}: {
  values: Window[];
  change: (value: Window[]) => void;
  label: string;
}) {
  return (
    <div className="calendar-windows">
      {values.map((w, i) => (
        <div className="calendar-window" key={i}>
          <Input
            label={'Início — ' + label + ' ' + (i + 1)}
            type="time"
            required
            value={time(w.start)}
            onChange={(e) =>
              e.target.value &&
              change(values.map((v, j) => (j === i ? { ...v, start: minutes(e.target.value) } : v)))
            }
          />
          <Input
            label={'Fim — ' + label + ' ' + (i + 1)}
            type="time"
            required
            disabled={w.end === 1440}
            value={time(w.end === 1440 ? 0 : w.end)}
            onChange={(e) =>
              e.target.value &&
              change(values.map((v, j) => (j === i ? { ...v, end: minutes(e.target.value) } : v)))
            }
          />
          <label className="care-check">
            <input
              type="checkbox"
              checked={w.end === 1440}
              onChange={(e) =>
                change(
                  values.map((v, j) => (j === i ? { ...v, end: e.target.checked ? 1440 : -1 } : v)),
                )
              }
            />
            Terminar à meia-noite
            <span className="sr-only">
              {' '}
              — {label}, período {i + 1}
            </span>
          </label>
          <Button
            variant="secondary"
            aria-label={'Remover período ' + (i + 1) + ' de ' + label}
            onClick={() => change(values.filter((_, j) => j !== i))}
          >
            Remover
          </Button>
        </div>
      ))}
      {!values.length && <span className="muted">Fechado</span>}
      <Button
        variant="secondary"
        disabled={values.length >= 4}
        onClick={() => change([...values, { start: -1, end: -1 }])}
      >
        Adicionar período<span className="sr-only"> em {label}</span>
      </Button>
    </div>
  );
}

export function CalendarEditor({
  value,
  change,
}: {
  value: Calendar;
  change: (next: Calendar) => void;
}) {
  return (
    <div className="calendar-editor">
      <h3>Expediente semanal</h3>
      <p>
        Adicione os períodos de atendimento. Separe manhã e tarde para deixar uma pausa entre eles.
        Os horários seguem o fuso da loja.
      </p>
      {weekdays.map((label, weekday) => (
        <fieldset className="care-fieldset" key={weekday}>
          <legend>{label}</legend>
          <Windows
            label={label}
            values={value.weekly.find((d) => d.weekday === weekday)?.windows || []}
            change={(windows) =>
              change({
                ...value,
                weekly: [
                  ...value.weekly.filter((d) => d.weekday !== weekday),
                  { weekday, windows },
                ],
              })
            }
          />
        </fieldset>
      ))}
      <h3>Datas especiais</h3>
      <p>
        Uma data especial substitui todo o expediente daquele dia. Deixe sem períodos para fechar a
        data.
      </p>
      {value.exceptions.map((exception, i) => (
        <fieldset className="care-fieldset" key={i}>
          <legend>Data especial {i + 1}</legend>
          <Input
            label={'Data especial ' + (i + 1)}
            type="date"
            required
            value={exception.date}
            onChange={(e) =>
              change({
                ...value,
                exceptions: value.exceptions.map((v, j) =>
                  j === i ? { ...v, date: e.target.value } : v,
                ),
              })
            }
          />
          <Windows
            label={'data especial ' + (i + 1)}
            values={exception.windows}
            change={(windows) =>
              change({
                ...value,
                exceptions: value.exceptions.map((v, j) => (j === i ? { ...v, windows } : v)),
              })
            }
          />
          <Button
            variant="secondary"
            onClick={() =>
              change({ ...value, exceptions: value.exceptions.filter((_, j) => j !== i) })
            }
          >
            Remover data especial {i + 1}
          </Button>
        </fieldset>
      ))}
      <Button
        variant="secondary"
        disabled={value.exceptions.length >= 100}
        onClick={() =>
          change({ ...value, exceptions: [...value.exceptions, { date: '', windows: [] }] })
        }
      >
        Adicionar data especial
      </Button>
    </div>
  );
}
