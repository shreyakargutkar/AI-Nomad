import { getStoredUser } from '@/lib/auth';

const headers = () => {
  const user = getStoredUser();
  if (!user?.id) return null;
  return {
    'Content-Type': 'application/json',
    'X-User-Id': user.id,
  };
};

export async function listJournals() {
  const h = headers();
  if (!h) throw new Error('Sign in to access your travel journals.');
  const res = await fetch('/api/journal', { headers: h });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load journals');
  return data.journals || [];
}

export async function createJournal({ title, destination }) {
  const h = headers();
  if (!h) throw new Error('Sign in to create a journal.');
  const res = await fetch('/api/journal', {
    method: 'POST',
    headers: h,
    body: JSON.stringify({ title, destination }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to create journal');
  return data;
}

export async function getJournal(id) {
  const h = headers();
  if (!h) throw new Error('Sign in to view this journal.');
  const res = await fetch(`/api/journal/${id}`, { headers: h });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load journal');
  return data;
}

export async function addJournalEntry(journalId, payload) {
  const h = headers();
  if (!h) throw new Error('Sign in to add entries.');
  const res = await fetch(`/api/journal/${journalId}/entries`, {
    method: 'POST',
    headers: h,
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to add entry');
  return data;
}

export async function addCollaborator(journalId, userId) {
  const h = headers();
  if (!h) throw new Error('Sign in to invite collaborators.');
  const res = await fetch(`/api/journal/${journalId}/collaborators`, {
    method: 'POST',
    headers: h,
    body: JSON.stringify({ user_id: userId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to add collaborator');
  return data;
}
