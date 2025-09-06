/**
 * Authentication service for Azure AD integration with Static Web Apps
 * @author cascade-01
 */

export interface UserInfo {
  userId: string;
  userDetails: string;
  userRoles: string[];
  identityProvider: string;
}

export interface ClientPrincipal {
  identityProvider: string;
  userId: string;
  userDetails: string;
  userRoles: string[];
}

export class AuthService {
  private static instance: AuthService;
  private userInfo: UserInfo | null = null;
  private isLoading: boolean = false;

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Get current user information from Static Web Apps authentication
   */
  async getUserInfo(): Promise<UserInfo | null> {
    if (this.isLoading) {
      return this.userInfo;
    }

    try {
      this.isLoading = true;
      const response = await fetch('/.auth/me');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.clientPrincipal) {
        this.userInfo = {
          userId: data.clientPrincipal.userId,
          userDetails: data.clientPrincipal.userDetails,
          userRoles: data.clientPrincipal.userRoles || [],
          identityProvider: data.clientPrincipal.identityProvider
        };
      } else {
        this.userInfo = null;
      }

      return this.userInfo;
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        // eslint-disable-next-line no-console
        console.error('Failed to get user info:', error);
      }
      this.userInfo = null;
      return null;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const user = await this.getUserInfo();
    return user !== null;
  }

  /**
   * Check if user has any of the required roles
   */
  async hasRole(requiredRoles: string[]): Promise<boolean> {
    const user = await this.getUserInfo();
    if (!user) return false;

    return requiredRoles.some(role => user.userRoles.includes(role));
  }

  /**
   * Check if user has all required roles
   */
  async hasAllRoles(requiredRoles: string[]): Promise<boolean> {
    const user = await this.getUserInfo();
    if (!user) return false;

    return requiredRoles.every(role => user.userRoles.includes(role));
  }

  /**
   * Initiate Azure AD login
   */
  login(redirectUrl?: string): void {
    const loginUrl = '/.auth/login/aad';
    const finalUrl = redirectUrl 
      ? `${loginUrl}?post_login_redirect_uri=${encodeURIComponent(redirectUrl)}`
      : loginUrl;
    
    window.location.href = finalUrl;
  }

  /**
   * Logout and redirect to home page
   */
  logout(redirectUrl?: string): void {
    const logoutUrl = '/.auth/logout';
    const finalUrl = redirectUrl 
      ? `${logoutUrl}?post_logout_redirect_uri=${encodeURIComponent(redirectUrl)}`
      : logoutUrl;
    
    window.location.href = finalUrl;
  }

  /**
   * Get authentication headers for API calls
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    const user = await this.getUserInfo();
    if (!user) {
      return {};
    }

    return {
      'X-User-ID': user.userId,
      'X-User-Details': user.userDetails,
      'X-User-Roles': user.userRoles.join(',')
    };
  }

  /**
   * Make authenticated API call
   */
  async authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const authHeaders = await this.getAuthHeaders();
    
    const finalOptions: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...options.headers
      }
    };

    return fetch(url, finalOptions);
  }

  /**
   * Clear cached user info (useful for testing or manual refresh)
   */
  clearCache(): void {
    this.userInfo = null;
  }
}

export default AuthService;
