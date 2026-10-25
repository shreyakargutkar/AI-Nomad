const USER_STORAGE_KEY = 'ainomad_auth_user';

/** Synced by AuthProvider for journal API and legacy callers. */
export function getStoredUser() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed?.id) return parsed;
  } catch {
    /* ignore */
  }
  return null;
}

export function setStoredUser(user) {
  if (typeof window === 'undefined' || !user?.id) return;
  localStorage.setItem(
    USER_STORAGE_KEY,
    JSON.stringify({
      id: user.id,
      name: user.name || 'Explorer',
      email: user.email || '',
    })
  );
}

export function clearStoredUser() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(USER_STORAGE_KEY);
}
