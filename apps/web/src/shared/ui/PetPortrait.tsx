import portrait from '../assets/petland-editorial.webp';

/** Brand photograph generated for this project; it depicts no real client or shop. */
export function PetPortrait({
  className,
  priority = false,
}: {
  className?: string;
  priority?: boolean;
}) {
  return (
    <img
      src={portrait}
      width={1536}
      height={1024}
      alt="Retrato editorial gerado: um cachorro de pelo dourado e um gato juntos."
      className={className}
      loading={priority ? 'eager' : 'lazy'}
      fetchPriority={priority ? 'high' : 'auto'}
      decoding="async"
    />
  );
}
