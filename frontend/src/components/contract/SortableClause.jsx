import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical } from 'lucide-react';

const HIGHLIGHT_TYPES = ['termination_conditions', 'ip_rights', 'refund_policy'];

export function SortableClause({ clause, onUpdate }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: clause.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const shouldHighlight = HIGHLIGHT_TYPES.includes(clause.clause_type);

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`rounded-lg border p-4 ${shouldHighlight ? 'border-amber-300 bg-amber-50' : 'border-gray-200 bg-white'}`}
    >
      <div className="flex items-start gap-3">
        <button
          {...attributes}
          {...listeners}
          className="mt-1 cursor-grab text-gray-400 hover:text-gray-600"
        >
          <GripVertical size={18} />
        </button>
        <div className="flex-1">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">
              {clause.clause_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
            {shouldHighlight && <span className="text-amber-500">⚠️</span>}
            {clause.is_mandatory && (
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">Required</span>
            )}
          </div>
          <textarea
            className="w-full rounded-md border border-gray-300 p-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            rows={3}
            value={clause.content}
            onChange={(e) => onUpdate(clause.id, e.target.value)}
            placeholder={`Enter ${clause.clause_type.replace(/_/g, ' ')} content...`}
          />
        </div>
      </div>
    </div>
  );
}
