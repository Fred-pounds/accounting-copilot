import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserSession,
} from 'amazon-cognito-identity-js';

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID;
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID;

const poolData = {
  UserPoolId: userPoolId,
  ClientId: clientId,
};

const userPool = new CognitoUserPool(poolData);

export interface AuthTokens {
  idToken: string;
  accessToken: string;
  refreshToken: string;
}

class AuthService {
  private sessionCheckInterval: NodeJS.Timeout | null = null;
  private lastActivityTime: number = Date.now();
  private readonly SESSION_TIMEOUT = 15 * 60 * 1000; // 15 minutes

  constructor() {
    this.startSessionMonitoring();
    this.setupActivityListeners();
  }

  private setupActivityListeners() {
    const updateActivity = () => {
      this.lastActivityTime = Date.now();
    };

    window.addEventListener('mousedown', updateActivity);
    window.addEventListener('keydown', updateActivity);
    window.addEventListener('scroll', updateActivity);
    window.addEventListener('touchstart', updateActivity);
  }

  private startSessionMonitoring() {
    this.sessionCheckInterval = setInterval(() => {
      const inactiveTime = Date.now() - this.lastActivityTime;
      if (inactiveTime >= this.SESSION_TIMEOUT) {
        this.signOut();
        window.location.href = '/login?timeout=true';
      }
    }, 60000); // Check every minute
  }

  async signIn(email: string, password: string): Promise<CognitoUserSession> {
    const authenticationData = {
      Username: email,
      Password: password,
    };

    const authenticationDetails = new AuthenticationDetails(authenticationData);

    const userData = {
      Username: email,
      Pool: userPool,
    };

    const cognitoUser = new CognitoUser(userData);

    return new Promise((resolve, reject) => {
      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session) => {
          this.lastActivityTime = Date.now();
          resolve(session);
        },
        onFailure: (err) => {
          reject(err);
        },
      });
    });
  }

  async signOut(): Promise<void> {
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
      cognitoUser.signOut();
    }
    if (this.sessionCheckInterval) {
      clearInterval(this.sessionCheckInterval);
    }
  }

  async getCurrentSession(): Promise<CognitoUserSession | null> {
    const cognitoUser = userPool.getCurrentUser();

    if (!cognitoUser) {
      return null;
    }

    return new Promise((resolve, reject) => {
      cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
        if (err) {
          reject(err);
          return;
        }
        if (session && session.isValid()) {
          this.lastActivityTime = Date.now();
          resolve(session);
        } else {
          resolve(null);
        }
      });
    });
  }

  async getTokens(): Promise<AuthTokens | null> {
    const session = await this.getCurrentSession();
    if (!session) {
      return null;
    }

    return {
      idToken: session.getIdToken().getJwtToken(),
      accessToken: session.getAccessToken().getJwtToken(),
      refreshToken: session.getRefreshToken().getToken(),
    };
  }

  async refreshSession(): Promise<CognitoUserSession> {
    const cognitoUser = userPool.getCurrentUser();

    if (!cognitoUser) {
      throw new Error('No user found');
    }

    return new Promise((resolve, reject) => {
      cognitoUser.getSession((err: Error | null, session: CognitoUserSession | null) => {
        if (err) {
          reject(err);
          return;
        }

        if (!session) {
          reject(new Error('No session found'));
          return;
        }

        const refreshToken = session.getRefreshToken();
        cognitoUser.refreshSession(refreshToken, (refreshErr, newSession) => {
          if (refreshErr) {
            reject(refreshErr);
            return;
          }
          resolve(newSession);
        });
      });
    });
  }

  isAuthenticated(): boolean {
    const cognitoUser = userPool.getCurrentUser();
    return cognitoUser !== null;
  }
}

export const authService = new AuthService();
