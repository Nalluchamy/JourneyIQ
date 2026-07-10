import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, UserPlus, Eye, EyeOff } from 'lucide-react';
import { authApi } from '../services/api';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (isRegister) {
        const data = await authApi.register({
          email,
          password,
          full_name: fullName,
          phone: phone || null,
        });
        // Auto-login: store tokens and redirect
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        window.dispatchEvent(new Event('storage'));
        navigate('/');
      } else {
        const data = await authApi.login({ email, password });
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        navigate('/');
        // Force header re-render
        window.dispatchEvent(new Event('storage'));
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during submission.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-border bg-card p-8 shadow-xl backdrop-blur-sm">
        <div>
          <h2 className="mt-2 text-center text-3xl font-extrabold tracking-tight text-white">
            {isRegister ? 'Create an Account' : 'Sign In to Your Account'}
          </h2>
          <p className="mt-2 text-center text-sm text-muted-foreground">
            {isRegister ? 'Join JourneyIQ storefront' : 'Access your cart, wishlist, and profile'}
          </p>
        </div>

        {/* Tab Selection */}
        <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted p-1">
          <button
            onClick={() => {
              setIsRegister(false);
              setError('');
              setSuccessMsg('');
            }}
            className={`flex items-center justify-center space-x-2 rounded-md py-2 text-sm font-medium transition-all ${
              !isRegister ? 'bg-primary text-white shadow-sm' : 'text-muted-foreground hover:text-white'
            }`}
          >
            <LogIn className="h-4 w-4" />
            <span>Sign In</span>
          </button>
          <button
            onClick={() => {
              setIsRegister(true);
              setError('');
              setSuccessMsg('');
            }}
            className={`flex items-center justify-center space-x-2 rounded-md py-2 text-sm font-medium transition-all ${
              isRegister ? 'bg-primary text-white shadow-sm' : 'text-muted-foreground hover:text-white'
            }`}
          >
            <UserPlus className="h-4 w-4" />
            <span>Sign Up</span>
          </button>
        </div>

        {error && (
          <div className="rounded-lg bg-destructive/15 border border-destructive/20 p-4 text-sm text-red-400">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="rounded-lg bg-emerald-500/15 border border-emerald-500/20 p-4 text-sm text-emerald-400">
            {successMsg}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4 rounded-md shadow-sm">
            {isRegister && (
              <>
                <div>
                  <label htmlFor="full-name" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Full Name
                  </label>
                  <input
                    id="full-name"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full rounded-lg border border-border bg-black/30 px-4 py-3 text-white placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label htmlFor="phone" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                    Phone (Optional)
                  </label>
                  <input
                    id="phone"
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full rounded-lg border border-border bg-black/30 px-4 py-3 text-white placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="+1 555-555-5555"
                  />
                </div>
              </>
            )}

            <div>
              <label htmlFor="email-address" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Email Address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-border bg-black/30 px-4 py-3 text-white placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="you@example.com"
              />
            </div>

            <div className="relative">
              <label htmlFor="password" className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                Password
              </label>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-black/30 px-4 py-3 pr-12 text-white placeholder-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 bottom-3 text-muted-foreground hover:text-white"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative flex w-full justify-center rounded-lg border border-transparent bg-primary py-3 px-4 text-sm font-semibold text-white transition-all hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? 'Please wait...' : isRegister ? 'Register' : 'Sign In'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
