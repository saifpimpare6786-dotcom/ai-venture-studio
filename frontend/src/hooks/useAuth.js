import { useState, useEffect } from 'react';

export function useAuth() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('avs_user');
    return saved ? JSON.parse(saved) : { id: 'default_founder', email: 'founder@venturestudio.ai', name: 'Startup Founder' };
  });

  const signIn = (email, name = 'Founder') => {
    const u = { id: 'usr_' + Math.random().toString(36).substring(2, 9), email, name };
    setUser(u);
    localStorage.setItem('avs_user', JSON.stringify(u));
  };

  const signOut = () => {
    localStorage.removeItem('avs_user');
    setUser({ id: 'default_founder', email: 'founder@venturestudio.ai', name: 'Startup Founder' });
  };

  return { user, signIn, signOut };
}
