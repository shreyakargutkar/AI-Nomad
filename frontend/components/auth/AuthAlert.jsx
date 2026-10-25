'use client';

export default function AuthAlert({ type = 'error', message }) {
  if (!message) return null;

  const styles =
    type === 'success'
      ? 'bg-[#1E3F2E]/10 border-[#1E3F2E]/25 text-[#1E3F2E]'
      : 'bg-red-50 border-red-200 text-red-700';

  return (
    <div
      role="alert"
      className={`rounded-lg border px-4 py-3 text-sm font-medium ${styles}`}
    >
      {message}
    </div>
  );
}
