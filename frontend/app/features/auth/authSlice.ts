import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
// Import RootState from the store file where it's correctly defined
import type { RootState } from '../../store';

interface AuthState {
  token: string | null;
  aesKey: string | null;
  enforceAes: boolean;
  isAuthenticated: boolean;
}

// Safely get initial state by checking if we are in a browser environment
const getInitialState = (): AuthState => {
  const isBrowser = typeof window !== 'undefined';
  if (!isBrowser) {
    return {
      token: null,
      aesKey: null,
      enforceAes: false,
      isAuthenticated: false,
    };
  }

  const token = localStorage.getItem('token');
  const aesKey = localStorage.getItem('aesKey');
  const enforceAes = localStorage.getItem('enforceAes') === 'true';

  return {
    token,
    aesKey,
    enforceAes,
    isAuthenticated: !!token,
  };
};

const initialState: AuthState = getInitialState();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ token: string; aesKey:string }>
    ) => {
      state.token = action.payload.token;
      state.aesKey = action.payload.aesKey;
      state.isAuthenticated = true;
      // Only write to localStorage in the browser
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', action.payload.token);
        localStorage.setItem('aesKey', action.payload.aesKey);
      }
    },
    logout: (state) => {
      state.token = null;
      state.aesKey = null;
      state.isAuthenticated = false;
      // Only write to localStorage in the browser
      if (typeof window !== 'undefined') {
        localStorage.clear();
      }
    },
    toggleAes: (state) => {
        state.enforceAes = !state.enforceAes;
        // Only write to localStorage in the browser
        if (typeof window !== 'undefined') {
            localStorage.setItem('enforceAes', state.enforceAes.toString());
        }
    }
  },
});

export const { setCredentials, logout, toggleAes } = authSlice.actions;

export default authSlice.reducer;

// Selectors now correctly use the imported RootState type
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
export const selectAuthToken = (state: RootState) => state.auth.token;
export const selectAesKey = (state: RootState) => state.auth.aesKey;
export const selectEnforceAes = (state: RootState) => state.auth.enforceAes;