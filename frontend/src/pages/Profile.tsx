import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';
import { User, Phone, Mail, ShoppingBag, CheckCircle } from 'lucide-react';
import { authApi, ordersApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';

export const Profile: React.FC = () => {
  const queryClient = useQueryClient();
  const { showNotification } = useNotification();
  const isAuthenticated = !!localStorage.getItem('token');

  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // Fetch Profile query
  const { data: profile, isLoading: isProfileLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const data = await authApi.getProfile();
      // Sync form values on load
      setFullName(data.full_name || '');
      setPhone(data.phone || '');
      return data;
    },
    enabled: isAuthenticated,
  });

  // Fetch recent orders query
  const { data: ordersData, isLoading: isOrdersLoading } = useQuery({
    queryKey: ['myOrders'],
    queryFn: ordersApi.getMyOrders,
    enabled: isAuthenticated,
  });

  const orders = ordersData?.items || [];

  // Mutations
  const updateProfileMutation = useMutation({
    mutationFn: (data: any) => authApi.updateProfile(data),
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(['profile'], updatedProfile);
      setIsEditing(false);
      showNotification('Profile updated successfully!', 'success');
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to update profile details.');
    },
  });

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    if (!fullName.trim()) {
      setErrorMsg('Full Name is required.');
      return;
    }
    updateProfileMutation.mutate({ full_name: fullName, phone: phone || null });
  };

  // Redirect guest users
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">


      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Your Profile</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your settings and view recent orders history</p>
      </div>

      {isProfileLoading ? (
        <div className="text-center py-12 text-muted-foreground animate-pulse">Loading profile settings...</div>
      ) : (
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Profile form section */}
          <div className="rounded-2xl border border-border bg-card p-6 h-fit space-y-6">
            <div className="flex items-center space-x-3 border-b border-border pb-4">
              <User className="h-6 w-6 text-primary" />
              <h3 className="font-extrabold text-white text-lg">Personal Details</h3>
            </div>

            {errorMsg && (
              <div className="rounded bg-destructive/15 border border-destructive/20 p-3 text-xs text-red-400">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleUpdateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground uppercase mb-1">Email (Read Only)</label>
                <div className="flex items-center space-x-2 rounded-lg border border-border/50 bg-black/10 px-3 py-2 text-sm text-muted-foreground">
                  <Mail className="h-4 w-4" />
                  <span>{profile?.email}</span>
                </div>
              </div>

              <div>
                <label htmlFor="fullNameInput" className="block text-xs font-semibold text-muted-foreground uppercase mb-1">Full Name</label>
                <input
                  id="fullNameInput"
                  type="text"
                  disabled={!isEditing}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg border border-border bg-black/30 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                />
              </div>

              <div>
                <label htmlFor="phoneInput" className="block text-xs font-semibold text-muted-foreground uppercase mb-1">Phone</label>
                <div className="relative">
                  <input
                    id="phoneInput"
                    type="text"
                    disabled={!isEditing}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full rounded-lg border border-border bg-black/30 pl-10 pr-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                  />
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                </div>
              </div>

              {isEditing ? (
                <div className="flex space-x-2 pt-2">
                  <button
                    type="submit"
                    className="flex-grow rounded-lg bg-primary py-2 text-xs font-bold text-white transition-all hover:bg-primary/90"
                  >
                    Save Changes
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setFullName(profile?.full_name || '');
                      setPhone(profile?.phone || '');
                      setErrorMsg('');
                    }}
                    className="rounded-lg border border-border bg-card px-4 py-2 text-xs font-bold text-white hover:bg-muted"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="w-full rounded-lg bg-primary/20 border border-primary/30 py-2.5 text-xs font-bold text-primary hover:bg-primary/35"
                >
                  Edit Profile
                </button>
              )}
            </form>
          </div>

          {/* Recent Orders List */}
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-border bg-card p-6">
              <div className="flex items-center space-x-3 border-b border-border pb-4 mb-6">
                <ShoppingBag className="h-6 w-6 text-primary" />
                <h3 className="font-extrabold text-white text-lg">Recent Orders (Read-Only)</h3>
              </div>

              {isOrdersLoading ? (
                <div className="text-center py-6 text-muted-foreground animate-pulse">Loading orders...</div>
              ) : orders.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-xl">
                  You have not placed any orders yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {orders.map((order: any) => (
                    <div
                      key={order.id}
                      className="rounded-xl border border-border bg-black/10 p-5 space-y-3 flex flex-col justify-between md:flex-row md:items-center md:space-y-0"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-white text-sm">Order #{order.id}</span>
                          <span className="flex items-center space-x-1 rounded bg-emerald-500/10 text-emerald-400 px-2 py-0.5 text-3xs font-extrabold uppercase tracking-wider">
                            <CheckCircle className="h-3 w-3" />
                            <span>{order.status}</span>
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground block">
                          Total: <strong className="text-white">₹{Number(order.total).toFixed(2)}</strong>
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground text-left md:text-right">
                        Items: {order.items?.length || 0}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
