import AuthService, { UserInfo } from '../authService';

describe('AuthService', () => {
  const originalFetch = global.fetch;
  const originalLocation = window.location;
  let auth: AuthService;

  beforeEach(() => {
    // Fresh singleton state
    // @ts-ignore
    AuthService['instance'] = undefined;
    auth = AuthService.getInstance();

    // Mock fetch
    global.fetch = jest.fn() as any;

    // Make window.location.href writable for tests
    // @ts-ignore
    delete (window as any).location;
    (window as any).location = { href: '' } as Location & { href: string };
  });

  afterEach(() => {
    global.fetch = originalFetch as any;
    // @ts-ignore
    delete (window as any).location;
    (window as any).location = originalLocation;
  });

  function mockAuthMeResponse(data: any, ok = true, status = 200) {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok,
      status,
      statusText: ok ? 'OK' : 'ERR',
      json: async () => data,
    });
  }

  it('getUserInfo returns mapped user when clientPrincipal present', async () => {
    const cp = {
      identityProvider: 'aad',
      userId: 'u1',
      userDetails: 'user@example.com',
      userRoles: ['authenticated', 'admin'],
    };
    mockAuthMeResponse({ clientPrincipal: cp });

    const res = await auth.getUserInfo();
    expect(res).toEqual<UserInfo>({
      userId: 'u1',
      userDetails: 'user@example.com',
      userRoles: ['authenticated', 'admin'],
      identityProvider: 'aad',
    });
  });

  it('getUserInfo returns null when clientPrincipal missing', async () => {
    mockAuthMeResponse({});
    const res = await auth.getUserInfo();
    expect(res).toBeNull();
  });

  it('getUserInfo handles non-OK by returning null', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false, status: 500, statusText: 'ERR' });
    const res = await auth.getUserInfo();
    expect(res).toBeNull();
  });

  it('isAuthenticated reflects presence of user', async () => {
    mockAuthMeResponse({ clientPrincipal: { identityProvider: 'aad', userId: 'u1', userDetails: 'u', userRoles: [] } });
    expect(await auth.isAuthenticated()).toBe(true);

    auth.clearCache();
    mockAuthMeResponse({});
    expect(await auth.isAuthenticated()).toBe(false);
  });

  it('hasRole and hasAllRoles evaluate correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => ({ clientPrincipal: { identityProvider: 'aad', userId: 'u1', userDetails: 'u', userRoles: ['a', 'b'] } })
    });
    expect(await auth.hasRole(['x', 'b'])).toBe(true);
    expect(await auth.hasRole(['x', 'y'])).toBe(false);
    expect(await auth.hasAllRoles(['a', 'b'])).toBe(true);
    expect(await auth.hasAllRoles(['a', 'c'])).toBe(false);
  });

  it('getAuthHeaders returns {} when unauthenticated', async () => {
    mockAuthMeResponse({});
    const headers = await auth.getAuthHeaders();
    expect(headers).toEqual({});
  });

  it('getAuthHeaders builds headers when authenticated', async () => {
    mockAuthMeResponse({ clientPrincipal: { identityProvider: 'aad', userId: 'u1', userDetails: 'u', userRoles: ['r1','r2'] } });
    const headers = await auth.getAuthHeaders();
    expect(headers).toEqual({
      'X-User-ID': 'u1',
      'X-User-Details': 'u',
      'X-User-Roles': 'r1,r2',
    });
  });

  it('authenticatedFetch merges headers and calls fetch', async () => {
    mockAuthMeResponse({ clientPrincipal: { identityProvider: 'aad', userId: 'u1', userDetails: 'u', userRoles: ['r'] } });
    (global.fetch as jest.Mock).mockResolvedValueOnce(new Response());

    const res = await auth.authenticatedFetch('/api/x', { headers: { 'X-Extra': '1' }, method: 'POST' });
    expect(global.fetch).toHaveBeenCalledWith('/api/x', expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'X-User-ID': 'u1',
        'X-User-Details': 'u',
        'X-User-Roles': 'r',
        'X-Extra': '1',
      })
    }));
    expect(res).toBeInstanceOf(Response);
  });

  it('login sets window.location.href correctly', () => {
    auth.login('/after');
    expect(window.location.href).toContain('/.auth/login/aad?post_login_redirect_uri=%2Fafter');

    auth.login();
    expect(window.location.href).toBe('/.auth/login/aad');
  });

  it('logout sets window.location.href correctly', () => {
    auth.logout('/bye');
    expect(window.location.href).toContain('/.auth/logout?post_logout_redirect_uri=%2Fbye');

    auth.logout();
    expect(window.location.href).toBe('/.auth/logout');
  });
});
