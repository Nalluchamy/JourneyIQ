import React, { useState, useEffect } from 'react';
import { addressesApi } from '../services/api';

interface Address {
  id: number;
  full_name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  is_default: boolean;
}

export const AddressManagement: React.FC = () => {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [isEditing, setIsEditing] = useState<number | null>(null);
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [addressLine1, setAddressLine1] = useState('');
  const [addressLine2, setAddressLine2] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [country, setCountry] = useState('United States');
  const [postalCode, setPostalCode] = useState('');
  const [isDefault, setIsDefault] = useState(false);

  const [formVisible, setFormVisible] = useState(false);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      const data = await addressesApi.getAddresses();
      setAddresses(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load addresses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAddresses();
  }, []);

  const resetForm = () => {
    setIsEditing(null);
    setFullName('');
    setPhone('');
    setAddressLine1('');
    setAddressLine2('');
    setCity('');
    setState('');
    setCountry('United States');
    setPostalCode('');
    setIsDefault(false);
    setFormVisible(false);
  };

  const handleEdit = (addr: Address) => {
    setIsEditing(addr.id);
    setFullName(addr.full_name);
    setPhone(addr.phone);
    setAddressLine1(addr.address_line1);
    setAddressLine2(addr.address_line2 || '');
    setCity(addr.city);
    setState(addr.state);
    setCountry(addr.country);
    setPostalCode(addr.postal_code);
    setIsDefault(addr.is_default);
    setFormVisible(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      full_name: fullName,
      phone,
      address_line1: addressLine1,
      address_line2: addressLine2 || null,
      city,
      state,
      country,
      postal_code: postalCode,
      is_default: isDefault,
    };

    try {
      if (isEditing !== null) {
        await addressesApi.updateAddress(isEditing, payload);
      } else {
        await addressesApi.createAddress(payload);
      }
      resetForm();
      fetchAddresses();
    } catch (err: any) {
      alert(err.message || 'Failed to save address.');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this address?')) return;
    try {
      await addressesApi.deleteAddress(id);
      fetchAddresses();
    } catch (err: any) {
      alert(err.message || 'Failed to delete address.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Shipping Addresses</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Manage your delivery locations for faster checkout.</p>
        </div>
        {!formVisible && (
          <button
            onClick={() => { resetForm(); setFormVisible(true); }}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors shadow-md shadow-blue-500/10 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
            </svg>
            Add New Address
          </button>
        )}
      </div>

      {formVisible && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 mb-8 shadow-sm transition-all">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
            {isEditing ? 'Edit Shipping Address' : 'Add New Shipping Address'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">Full Name</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">Phone Number</label>
                <input
                  type="text"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="+1 (555) 019-2834"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">Address Line 1</label>
              <input
                type="text"
                required
                value={addressLine1}
                onChange={(e) => setAddressLine1(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="1234 Main St"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">Address Line 2 (Optional)</label>
              <input
                type="text"
                value={addressLine2}
                onChange={(e) => setAddressLine2(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="Apt 4B, Building C"
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">City</label>
                <input
                  type="text"
                  required
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="Seattle"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">State / Region</label>
                <input
                  type="text"
                  required
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="WA"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">Postal Code</label>
                <input
                  type="text"
                  required
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="98101"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">Country</label>
                <input
                  type="text"
                  required
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="United States"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="default"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="w-4.5 h-4.5 text-blue-600 border-slate-300 dark:border-slate-700 rounded focus:ring-blue-500"
              />
              <label htmlFor="default" className="text-sm text-slate-750 dark:text-slate-300">Set as default shipping address</label>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-700">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2.5 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 rounded-xl font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors"
              >
                {isEditing ? 'Save Changes' : 'Add Address'}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Loading addresses...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400 p-4 rounded-xl border border-red-100 dark:border-red-900/30 text-center mb-6">
          {error}
        </div>
      ) : addresses.length === 0 ? (
        <div className="text-center py-16 bg-slate-50 dark:bg-slate-900 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 p-8">
          <svg className="w-12 h-12 mx-auto text-slate-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">No addresses saved</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">Please add an address to use during checkout.</p>
          <button
            onClick={() => setFormVisible(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors"
          >
            Add First Address
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {addresses.map((addr) => (
            <div
              key={addr.id}
              className={`p-6 rounded-2xl border transition-all ${
                addr.is_default
                  ? 'bg-blue-50/30 dark:bg-blue-950/10 border-blue-200 dark:border-blue-900/50 shadow-sm'
                  : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700'
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-bold text-slate-900 dark:text-white">{addr.full_name}</h4>
                  {addr.is_default && (
                    <span className="inline-block px-2 py-0.5 mt-1 bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-md">
                      Default Address
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(addr)}
                    className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 rounded-lg transition-colors"
                    title="Edit address"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => handleDelete(addr.id)}
                    className="p-1.5 hover:bg-red-50 dark:hover:bg-red-950/30 text-red-500 rounded-lg transition-colors"
                    title="Delete address"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              <div className="text-sm text-slate-650 dark:text-slate-350 space-y-1">
                <p>{addr.address_line1}</p>
                {addr.address_line2 && <p>{addr.address_line2}</p>}
                <p>{addr.city}, {addr.state} {addr.postal_code}</p>
                <p>{addr.country}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 font-medium">Phone: {addr.phone}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
