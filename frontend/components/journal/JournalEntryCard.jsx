'use client';

import { Pencil, Trash2 } from 'lucide-react';

function previewText(content, max = 140) {
  if (!content) return '';
  const t = content.trim();
  return t.length <= max ? t : `${t.slice(0, max)}…`;
}

export default function JournalEntryCard({
  entry,
  onEdit,
  onDelete,
  compact = false,
}) {
  const dateLabel = entry.created_at
    ? new Date(entry.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : '';

  return (
    <article className="bg-white border border-[#EAE3D2] rounded-xl p-5 shadow-sm relative group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <time className="text-[10px] font-mono text-[#C85A32] uppercase tracking-wider">{dateLabel}</time>
          {entry.title && (
            <h3 className="text-lg font-bold font-display text-[#1E2229] mt-1">{entry.title}</h3>
          )}
          <p className={`text-sm text-[#1E2229]/80 mt-2 whitespace-pre-wrap ${compact ? 'line-clamp-3' : ''}`}>
            {compact ? previewText(entry.content) : entry.content}
          </p>
        </div>
        <div className="flex gap-1 shrink-0 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={() => onEdit(entry)}
            className="p-2 rounded-lg text-[#1E3F2E] hover:bg-[#FBF9F6] border border-transparent hover:border-[#EAE3D2]"
            aria-label="Edit entry"
          >
            <Pencil size={14} />
          </button>
          <button
            type="button"
            onClick={() => onDelete(entry)}
            className="p-2 rounded-lg text-red-600 hover:bg-red-50 border border-transparent hover:border-red-100"
            aria-label="Delete entry"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      {entry.image_url && (
        <img
          src={entry.image_url}
          alt=""
          className="mt-4 rounded-lg max-h-64 w-full object-cover border border-[#EAE3D2]"
        />
      )}
    </article>
  );
}
