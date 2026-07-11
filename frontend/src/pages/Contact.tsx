import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send } from 'lucide-react';
import { useNotification } from '../context/NotificationContext';

export const Contact: React.FC = () => {
  const { showNotification } = useNotification();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) {
      showNotification('Please fill in all required fields.', 'error');
      return;
    }
    
    // Basic email validation regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      showNotification('Please enter a valid email address.', 'error');
      return;
    }

    setIsSubmitting(true);
    // Simulate API request
    setTimeout(() => {
      setIsSubmitting(false);
      showNotification('Message sent successfully! Our integration team will contact you shortly.', 'success');
      setFormData({
        name: '',
        email: '',
        subject: '',
        message: ''
      });
    }, 1500);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 text-slate-100 animate-fade-in">
      <div className="text-center max-w-3xl mx-auto mb-16">
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-violet-400 to-cyan-400 mb-6">
          Contact JourneyIQ Support
        </h1>
        <p className="text-lg text-slate-350 leading-relaxed">
          Connect with the JourneyIQ enterprise integration team for custom recommendations setup, 
          telemetry streaming configurations, or deep learning model training adjustments.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 max-w-6xl mx-auto">
        {/* Contact Info */}
        <div className="lg:col-span-1 space-y-8">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-white mb-1">Email Integration Support</h3>
              <p className="text-slate-400 text-sm">integration@journeyiq.io</p>
              <p className="text-slate-500 text-xs mt-1">Response time within 24 hours</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <Phone className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-white mb-1">Call Technical Hotlines</h3>
              <p className="text-slate-400 text-sm">+1 (800) 555-0199</p>
              <p className="text-slate-500 text-xs mt-1">Available Mon-Fri, 9am - 6pm EST</p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 shrink-0">
              <MapPin className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-white mb-1">HQ Headquarters</h3>
              <p className="text-slate-450 text-sm">100 Pine Street, Suite 1250</p>
              <p className="text-slate-450 text-sm">San Francisco, CA 94111</p>
            </div>
          </div>
        </div>

        {/* Contact Form */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-8 shadow-xl backdrop-blur-sm">
          <h2 className="text-2xl font-bold text-white mb-6">Send a Message</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-350 mb-2">Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Your full name"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all duration-200"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-350 mb-2">Email *</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@company.com"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all duration-200"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-350 mb-2">Subject</label>
              <input
                type="text"
                name="subject"
                value={formData.subject}
                onChange={handleChange}
                placeholder="Enterprise setup, API access, model queries"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all duration-200"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-350 mb-2">Message *</label>
              <textarea
                name="message"
                value={formData.message}
                onChange={handleChange}
                rows={5}
                placeholder="How can our technical team assist you?"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all duration-200 resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full inline-flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:from-indigo-900 disabled:to-cyan-900 text-white font-semibold shadow-lg hover:shadow-indigo-500/20 transition-all duration-200"
            >
              <Send className={`h-4 w-4 ${isSubmitting ? 'animate-pulse' : ''}`} />
              {isSubmitting ? 'Sending message...' : 'Send Message'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
