import type { components } from '@petland/api-contract';
import { client, result } from '../../shared/lib/api';

export type Account = components['schemas']['AccountResponse'];
export type Role = components['schemas']['Role'];
export type Session = components['schemas']['SessionResponse'];
type Schemas = components['schemas'];

export const identityApi = {
  async me(signal?: AbortSignal) {
    const response = await client.GET('/api/v1/auth/me', { signal });
    return response.response.status === 401 ? null : result(response);
  },
  async login(body: Schemas['LoginInput']) {
    return result(await client.POST('/api/v1/auth/login', { body }));
  },
  async register(body: Schemas['RegisterInput']) {
    return result(await client.POST('/api/v1/auth/register', { body }));
  },
  async logout() {
    result(await client.POST('/api/v1/auth/logout'));
  },
  async requestReset(body: Schemas['EmailInput']) {
    return result(await client.POST('/api/v1/auth/password-reset-requests', { body }));
  },
  async requestVerification(body: Schemas['EmailInput']) {
    return result(await client.POST('/api/v1/auth/email-verification-requests', { body }));
  },
  async verify(body: Schemas['TokenInput']) {
    return result(await client.POST('/api/v1/auth/email-verifications', { body }));
  },
  async reset(body: Schemas['ResetInput']) {
    return result(await client.POST('/api/v1/auth/password-resets', { body }));
  },
  async acceptInvitation(body: Schemas['InvitationInput']) {
    return result(await client.POST('/api/v1/auth/invitations/accept', { body }));
  },
  async sessions(signal?: AbortSignal) {
    return result(await client.GET('/api/v1/auth/sessions', { signal }));
  },
  async revokeSession(id: string) {
    result(
      await client.DELETE('/api/v1/auth/sessions/{session_id}', {
        params: { path: { session_id: id } },
      }),
    );
  },
  async changePassword(body: Schemas['ChangePasswordInput']) {
    return result(await client.POST('/api/v1/me/password-changes', { body }));
  },
  async users(offset = 0, signal?: AbortSignal) {
    return result(
      await client.GET('/api/v1/management/users', {
        params: { query: { offset, limit: 20 } },
        signal,
      }),
    );
  },
  async invite(body: Schemas['InviteEmployeeInput']) {
    return result(await client.POST('/api/v1/management/employee-invitations', { body }));
  },
  async roles(id: string, body: Schemas['RolesInput']) {
    result(
      await client.PUT('/api/v1/management/users/{user_id}/roles', {
        params: { path: { user_id: id } },
        body,
      }),
    );
  },
  async status(id: string, body: Schemas['StatusInput']) {
    result(
      await client.PATCH('/api/v1/management/users/{user_id}/status', {
        params: { path: { user_id: id } },
        body,
      }),
    );
  },
};
