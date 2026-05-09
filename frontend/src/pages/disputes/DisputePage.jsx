import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { disputesApi } from '../../api/disputes';
import { useAuth } from '../../hooks/useAuth';
import { StatusBadge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Spinner } from '../../components/ui/Spinner';
import { Avatar } from '../../components/ui/Avatar';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export function DisputePage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [dispute, setDispute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [resolveData, setResolveData] = useState({ resolution: 'executor', resolution_comment: '' });
  const [resolving, setResolving] = useState(false);
  const messagesEndRef = useRef(null);

  const fetchDispute = async () => {
    try {
      const { data } = await disputesApi.get(id);
      setDispute(data);
    } catch (err) {
      toast.error('Failed to load dispute');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDispute();
    const interval = setInterval(fetchDispute, 15000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [dispute?.messages]);

  const handleSend = async () => {
    if (!message.trim()) return;
    try {
      setSending(true);
      await disputesApi.addMessage(id, message);
      setMessage('');
      fetchDispute();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleResolve = async () => {
    try {
      setResolving(true);
      await disputesApi.resolve(id, resolveData);
      toast.success('Dispute resolved!');
      fetchDispute();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to resolve');
    } finally {
      setResolving(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>;
  if (!dispute) return null;

  const isAdmin = user?.role === 'admin';

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dispute</h1>
        <StatusBadge status={dispute.status} />
      </div>

      {dispute.description && (
        <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4">
          <p className="text-sm text-red-800">{dispute.description}</p>
        </div>
      )}

      {/* Messages */}
      <div className="rounded-xl border border-gray-200 bg-white">
        <div className="max-h-96 overflow-y-auto p-4 space-y-4">
          {dispute.messages && dispute.messages.length > 0 ? (
            dispute.messages.map((msg) => {
              const isOwn = msg.author_id === user?.id;
              return (
                <div key={msg.id} className={`flex gap-3 ${isOwn ? 'flex-row-reverse' : ''}`}>
                  <Avatar name={isOwn ? user?.full_name : 'User'} size="sm" />
                  <div className={`max-w-sm rounded-xl p-3 text-sm ${isOwn ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-900'}`}>
                    <p>{msg.content}</p>
                    {msg.file_url && (
                      <a href={msg.file_url} target="_blank" rel="noopener noreferrer" className="underline text-xs mt-1 block">
                        View Attachment
                      </a>
                    )}
                    <p className={`mt-1 text-xs ${isOwn ? 'text-indigo-200' : 'text-gray-400'}`}>
                      {format(new Date(msg.created_at), 'HH:mm')}
                    </p>
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-center text-sm text-gray-400 py-8">No messages yet.</p>
          )}
          <div ref={messagesEndRef} />
        </div>

        {dispute.status !== 'resolved' && (
          <div className="border-t border-gray-200 p-4 flex gap-3">
            <input
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
              placeholder="Type a message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            />
            <Button size="sm" loading={sending} onClick={handleSend}>Send</Button>
          </div>
        )}
      </div>

      {/* Admin panel */}
      {isAdmin && dispute.status !== 'resolved' && (
        <div className="mt-6 rounded-xl bg-white p-6 shadow-sm border border-gray-200">
          <h2 className="font-semibold text-gray-900 mb-4">Admin Resolution</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Resolution</label>
              <select
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                value={resolveData.resolution}
                onChange={(e) => setResolveData({ ...resolveData, resolution: e.target.value })}
              >
                <option value="executor">Executor wins (release funds)</option>
                <option value="customer">Customer wins (refund)</option>
                <option value="shared">50/50 split</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Comment</label>
              <textarea
                rows={3}
                className="w-full rounded-lg border border-gray-300 p-3 text-sm"
                value={resolveData.resolution_comment}
                onChange={(e) => setResolveData({ ...resolveData, resolution_comment: e.target.value })}
                placeholder="Resolution comment..."
              />
            </div>
            <div className="flex gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => disputesApi.updateStatus(id, 'under_review').then(fetchDispute)}
              >
                Mark Under Review
              </Button>
              <Button loading={resolving} onClick={handleResolve}>
                Resolve Dispute
              </Button>
            </div>
          </div>
        </div>
      )}

      {dispute.status === 'resolved' && (
        <div className="mt-6 rounded-lg bg-green-50 border border-green-200 p-4">
          <p className="font-medium text-green-800">Dispute Resolved</p>
          <p className="text-sm text-green-700 mt-1">Resolution: {dispute.resolution}</p>
          {dispute.resolution_comment && (
            <p className="text-sm text-green-700 mt-1">{dispute.resolution_comment}</p>
          )}
        </div>
      )}
    </div>
  );
}
