import React, { useRef } from 'react';
import { Button } from './Button';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.zip', '.png', '.jpg', '.jpeg'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function FileUpload({ onFile, label = 'Upload File', accept }) {
  const inputRef = useRef(null);

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      alert(`File type not allowed. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      alert('File exceeds 10MB limit');
      return;
    }
    onFile(file);
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={handleChange}
        accept={accept || ALLOWED_EXTENSIONS.join(',')}
      />
      <Button variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
        {label}
      </Button>
    </div>
  );
}
