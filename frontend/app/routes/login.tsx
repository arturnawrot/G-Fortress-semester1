import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router';
import { useDispatch } from 'react-redux';
import { toast } from 'react-toastify';
import { api } from '../services/api'; 
import { setCredentials } from '../features/auth/authSlice';
import { generateKeyPair, deriveSharedSecret } from '../utils/crypto';

// Define the login mutation
const authApi = api.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: '/api/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
  }),
  overrideExisting: true,
});

const { useLoginMutation } = authApi;

export default function Login() {
  const [email, setEmail] = useState('admin');
  const [password, setPassword] = useState('admin');
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [login, { isLoading }] = useLoginMutation();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      // 1. Generate client key pair
      const { publicKey: clientPublicKey, privateKey: clientPrivateKey } = await generateKeyPair();

      // 2. Call login endpoint
      const loginResponse: any = await login({
        username: email,
        password: password,
        client_public_key: clientPublicKey,
      }).unwrap();
      
      const { access_token, server_public_key } = loginResponse;

      // 3. Derive AES session key
      // --- THIS LINE IS NOW CORRECT ---
      const aesKey = await deriveSharedSecret(clientPublicKey, clientPrivateKey, server_public_key);

      // 4. Store credentials in Redux
      dispatch(setCredentials({ token: access_token, aesKey }));
      
      toast.success("Login successful!");
      navigate('/dashboard');

    } catch (err: any) {
      console.error('Failed to login:', err);
    }
  };

    return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,#fff,rgba(255,255,255,0.6))] -z-10"></div>
      
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center mb-4 shadow-lg">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 tracking-tight">
            Welcome back
          </h2>
        </div>

        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                  Username
                </label>
                <input
                    id="email"
                    name="email"
                    type="text"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full px-4 py-3.5 text-gray-900 placeholder-gray-400 bg-white border border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Enter your username"
                  />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                  Password
                </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full px-4 py-3.5 text-gray-900 placeholder-gray-400 bg-white border border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Enter your password"
                  />
              </div>

            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center items-center py-3.5 px-4 text-sm font-semibold rounded-xl text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transform transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
            </form>
          </div>
        </div>
    </div>
  );
}