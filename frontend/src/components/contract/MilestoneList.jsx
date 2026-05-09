import React from 'react';
import { StatusBadge } from '../ui/Badge';
import { format } from 'date-fns';

export function MilestoneList({ milestones, onUpdate, canEdit }) {
  if (!milestones || milestones.length === 0) {
    return <p className="text-sm text-gray-500">No milestones defined.</p>;
  }

  return (
    <div className="space-y-3">
      {milestones.map((ms) => (
        <div key={ms.id} className="rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-gray-900">{ms.title}</h4>
              {ms.description && (
                <p className="mt-1 text-sm text-gray-500">{ms.description}</p>
              )}
              <p className="mt-1 text-sm text-gray-600">
                Deadline: {format(new Date(ms.deadline), 'MMM d, yyyy')} · $
                {Number(ms.amount).toFixed(2)}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={ms.status} />
              {canEdit && onUpdate && (
                <select
                  className="rounded border border-gray-300 text-sm p-1"
                  value={ms.status}
                  onChange={(e) => onUpdate(ms.id, { status: e.target.value })}
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                </select>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
