/**
 * In-memory auth token store.
 * Intentionally does NOT use localStorage or sessionStorage.
 * Token lives only for the current browser session (lost on page reload).
 * The auth module will call setToken/clearToken when the user logs in/out.
 */

let _authToken: string | null = null;

export const tokenStore = {
  getToken(): string | null {
    return _authToken;
  },
  setToken(token: string | null): void {
    _authToken = token;
  },
  clearToken(): void {
    _authToken = null;
  },
};
