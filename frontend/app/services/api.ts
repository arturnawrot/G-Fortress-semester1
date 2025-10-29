import {
  createApi,
  fetchBaseQuery,
} from '@reduxjs/toolkit/query/react';
import type {
    BaseQueryFn,
    FetchArgs,
    FetchBaseQueryError,
} from '@reduxjs/toolkit/query';
import type { RootState } from '../store';
import { logout } from '../features/auth/authSlice';
import { encryptData, decryptData } from '../utils/crypto';
import { toast } from 'react-toastify';

const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    const enforceAes = (getState() as RootState).auth.enforceAes;
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    // Turned off for development purposes
    headers.set('X-ENFORCE-AES256', '0');
    return headers;
  },
});

const baseQueryWithCrypto: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const { getState, dispatch } = api;
  const state = getState() as RootState;
  const { aesKey, enforceAes } = state.auth;
  
  let finalArgs = typeof args === 'string' ? { url: args } : args;

  // if (enforceAes && aesKey && finalArgs.body) {
  //   try {
  //       const encryptedBody = await encryptData(aesKey, finalArgs.body as any);
  //       finalArgs = { ...finalArgs, body: encryptedBody, headers: { ...finalArgs.headers, 'Content-Type': 'text/plain' } };
  //   } catch (error) {
  //       toast.error("Encryption failed!");
  //       console.error('Encryption error:', error);
  //       return { error: { status: 'CUSTOM_ERROR', error: 'Encryption failed' } as any };
  //   }
  // }

  let result = await baseQuery(finalArgs, api, extraOptions);

  // --- THIS IS THE CORRECTED ERROR HANDLING LOGIC ---
  if (result.error) {
    // If we get a 401 and it's NOT the login endpoint, it's an expired session.
    if (result.error.status === 401 && api.endpoint !== 'login') {
        toast.error('Session expired. Please login again.');
        dispatch(logout());
    } 
    // For all other errors (including login failure), display the message from the API.
    else {
        const errorData = result.error.data as any;
        if (errorData?.message) {
           toast.error(errorData.message);
        } else {
           toast.error("An unknown error occurred.");
        }
    }
  }
  // --- END OF CORRECTION ---

  // if (!result.error && result.data && enforceAes && aesKey) {
  //   try {
  //       const decryptedData = await decryptData(aesKey, result.data as string);
  //       result = { ...result, data: decryptedData };
  //   } catch (error) {
  //       toast.error("Decryption failed!");
  //       console.error('Decryption error:', error);
  //       return { error: { status: 'CUSTOM_ERROR', error: 'Decryption failed' } as any };
  //   }
  // }
  
  return result;
};


export const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithCrypto,
  tagTypes: ['Reports', 'ScheduledScans'],
  endpoints: (builder) => ({
    // Endpoints are injected from other files
  }),
});