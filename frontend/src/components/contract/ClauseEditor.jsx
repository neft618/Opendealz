import React from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable';
import { SortableClause } from './SortableClause';

export function ClauseEditor({ clauses, setClauses, onSave }) {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = clauses.findIndex((c) => c.id === active.id);
      const newIndex = clauses.findIndex((c) => c.id === over.id);
      const reordered = arrayMove(clauses, oldIndex, newIndex).map((c, i) => ({
        ...c,
        position: i,
      }));
      setClauses(reordered);
      if (onSave) onSave(reordered);
    }
  };

  const handleUpdate = (id, content) => {
    setClauses(clauses.map((c) => (c.id === id ? { ...c, content } : c)));
  };

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={clauses.map((c) => c.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-3">
          {[...clauses].sort((a, b) => a.position - b.position).map((clause) => (
            <SortableClause key={clause.id} clause={clause} onUpdate={handleUpdate} />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}
