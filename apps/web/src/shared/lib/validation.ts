import { z } from 'zod';

// Forms must also work when the page blocks dynamic code evaluation.
z.config({ jitless: true });
export { z };
