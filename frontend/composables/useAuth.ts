interface UserResponse {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

interface AuthResponse {
  message: string;
  user: UserResponse;
}

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  error: string | null;
}

export const useAuth = () => {
  const userCookie = useCookie<UserResponse | null>('user');

  // Use useState for persistent state across page reloads
  const state = useState<AuthState>('auth', () => ({
    token: null,
    user: userCookie.value ?? null,
    error: null,
  }));

  const router = useRouter();
  const config = useRuntimeConfig();

  // Computed properties for easier access
  const token = computed(() => state.value.token);
  const user = computed(() => state.value.user);
  const error = computed(() => state.value.error);
  const isAuthenticated = computed(() => !!state.value.user);

  watch(
    () => state.value.user,
    (val) => {
      userCookie.value = val;
    }
  );

  // Login function
  const login = async (username: string, password: string) => {
    state.value.error = null;

    try {
      const response = await $fetch<AuthResponse>('users/login/', {
        baseURL: config.public.apiBase,
        method: 'POST',
        body: { username, password },
        credentials: 'include'
      });

      state.value.user = response.user;
      userCookie.value = response.user;
      // Store user info in localStorage for persistence
      if (process.client) {
        localStorage.setItem('user', JSON.stringify(response.user));
      }
      await router.push('/');
    } catch (err: any) {
      state.value.error = err?.data?.message || 'Erro desconhecido';
      console.error('Login error:', err);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await useFetch('/users/logout/', {
        baseURL: config.public.apiBase,
        method: 'POST',
      });
    } catch (err) {
      console.error('Logout error:', err);
      // Continue with logout even if API call fails
    } finally {
      state.value.token = null;
      state.value.user = null;
      state.value.error = null;

      userCookie.value = null;

      if (process.client) {
        localStorage.removeItem('user');
      }

      await router.push('/login');
    }
  };

  // Initialize auth state from localStorage
  const initAuth = () => {
    if (userCookie.value) {
      state.value.user = userCookie.value;
    }

    if (process.client) {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          state.value.user = JSON.parse(storedUser);
          userCookie.value = state.value.user;
        } catch (err) {
          console.error('Error parsing stored user:', err);
          localStorage.removeItem('user');
        }
      }
    }
  };

  // Auto-initialize on client side
  if (process.client) {
    initAuth();
  }

  return {
    login,
    logout,
    initAuth,
    token,
    user,
    error,
    isAuthenticated,
  };
};
