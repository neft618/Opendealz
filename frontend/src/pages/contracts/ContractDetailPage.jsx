import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useContract } from '../../hooks/useContract';
import { contractsApi } from '../../api/contracts';
import { useAuth } from '../../hooks/useAuth';
import { EscrowStatus } from '../../components/contract/EscrowStatus';
import { MilestoneList } from '../../components/contract/MilestoneList';
import { StatusBadge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { FileUpload } from '../../components/ui/FileUpload';
import { Spinner } from '../../components/ui/Spinner';
import { Modal } from '../../components/ui/Modal';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const STATUS_STEPS = ['draft', 'signed', 'in_progress', 'completed'];

function StatusStepper({ status }) {
  const currentIndex = STATUS_STEPS.indexOf(status);
  return (
    <div className="flex items-center mb-6">
      {STATUS_STEPS.map((s, i) => (
        <React.Fragment key={s}>
          <div className={`flex flex-col items-center ${i <= currentIndex ? 'text-indigo-600' : 'text-gray-400'}`}>
            <div className={`h-8 w-8 rounded-full border-2 flex items-center justify-center text-sm font-medium ${
              i < currentIndex ? 'bg-indigo-600 border-indigo-600 text-white' :
              i === currentIndex ? 'border-indigo-600 text-indigo-600' :
              'border-gray-300 text-gray-400'
            }`}>
              {i < currentIndex ? '✓' : i + 1}
            </div>
            <span className="mt-1 text-xs capitalize">{s.replace('_', ' ')}</span>
          </div>
          {i < STATUS_STEPS.length - 1 && (
            <div className={`flex-1 h-0.5 mx-2 ${i < currentIndex ? 'bg-indigo-600' : 'bg-gray-200'}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

export function ContractDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { contract, loading, refetch } = useContract(id);
  const [uploadingDeliverable, setUploadingDeliverable] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewData, setReviewData] = useState({ rating: 5, comment: '' });
  const [submittingReview, setSubmittingReview] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [rejecting, setRejecting] = useState(false);

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>;
  if (!contract) return null;

  const isCustomer = contract.customer_id === user?.id;
  const isExecutor = contract.executor_id === user?.id;

  const handleDeliverableUpload = async (file) => {
    try {
      setUploadingDeliverable(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', file.name);
      await contractsApi.uploadDeliverable(id, formData);
      toast.success('Deliverable uploaded!');
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploadingDeliverable(false);
    }
  };

  const handleAccept = async () => {
    try {
      setAccepting(true);
      await contractsApi.accept(id);
      toast.success('Contract accepted! Funds released.');
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to accept');
    } finally {
      setAccepting(false);
    }
  };

  const handleReject = async () => {
    try {
      setRejecting(true);
      await contractsApi.reject(id);
      toast.success('Work rejected. Dispute opened.');
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reject');
    } finally {
      setRejecting(false);
    }
  };

  const handleSubmitReview = async () => {
    try {
      setSubmittingReview(true);
      await contractsApi.createReview(id, reviewData);
      toast.success('Review submitted!');
      setShowReviewModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit review');
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Contract Details</h1>
        <StatusBadge status={contract.status} />
      </div>

      <StatusStepper status={contract.status === 'disputed' || contract.status === 'cancelled' ? 'in_progress' : contract.status} />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Contract info */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="font-semibold text-gray-900 mb-4">Contract Information</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Total Amount</p>
                <p className="font-medium text-gray-900">${Number(contract.total_amount).toFixed(2)}</p>
              </div>
              <div>
                <p className="text-gray-500">Payment Type</p>
                <p className="font-medium capitalize">{contract.payment_type}</p>
              </div>
              <div>
                <p className="text-gray-500">Review Period</p>
                <p className="font-medium">{contract.review_period_days} days</p>
              </div>
              {contract.signed_at && (
                <div>
                  <p className="text-gray-500">Signed</p>
                  <p className="font-medium">{format(new Date(contract.signed_at), 'MMM d, yyyy')}</p>
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="mt-4 flex gap-3 flex-wrap">
              {contract.status === 'draft' && (
                <Button onClick={() => navigate(`/contracts/${id}/build`)}>
                  Build Contract
                </Button>
              )}
              {isCustomer && contract.status === 'in_progress' && (
                <>
                  <Button loading={accepting} onClick={handleAccept}>Accept Work</Button>
                  <Button variant="danger" loading={rejecting} onClick={handleReject}>Reject & Dispute</Button>
                </>
              )}
              {contract.status === 'completed' && (
                <Button variant="outline" onClick={() => setShowReviewModal(true)}>
                  Leave Review
                </Button>
              )}
            </div>
          </div>

          {/* Clauses */}
          {contract.clauses && contract.clauses.length > 0 && (
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <h2 className="font-semibold text-gray-900 mb-4">Contract Clauses</h2>
              <div className="space-y-3">
                {[...contract.clauses].sort((a, b) => a.position - b.position).map((clause) => (
                  <div key={clause.id} className="rounded-lg border border-gray-100 p-3">
                    <p className="text-xs font-medium text-gray-500 mb-1">
                      {clause.clause_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </p>
                    <p className="text-sm text-gray-800">{clause.content || <em className="text-gray-400">Empty</em>}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Milestones */}
          {contract.milestones && contract.milestones.length > 0 && (
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <h2 className="font-semibold text-gray-900 mb-4">Milestones</h2>
              <MilestoneList
                milestones={contract.milestones}
                canEdit={isCustomer}
                onUpdate={async (mid, data) => {
                  await contractsApi.updateMilestone(id, mid, data);
                  refetch();
                }}
              />
            </div>
          )}

          {/* Deliverables */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">Deliverables</h2>
              {isExecutor && contract.status === 'in_progress' && (
                <FileUpload
                  label={uploadingDeliverable ? 'Uploading...' : 'Upload Deliverable'}
                  onFile={handleDeliverableUpload}
                />
              )}
            </div>
            {contract.deliverables && contract.deliverables.length > 0 ? (
              <div className="space-y-2">
                {contract.deliverables.map((d) => (
                  <div key={d.id} className="flex items-center justify-between rounded-lg border border-gray-100 p-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{d.file_name}</p>
                      <p className="text-xs text-gray-500">{d.description} · {(d.file_size / 1024).toFixed(1)} KB</p>
                    </div>
                    <a
                      href={`/api/v1/contracts/${id}/deliverables/${d.id}/download`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-indigo-600 hover:underline"
                    >
                      Download
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No deliverables yet.</p>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <EscrowStatus contract={contract} />
        </div>
      </div>

      <Modal isOpen={showReviewModal} onClose={() => setShowReviewModal(false)} title="Leave a Review">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Rating (1-5)</label>
            <input
              type="number"
              min={1} max={5}
              className="w-20 rounded border border-gray-300 px-3 py-1.5 text-sm"
              value={reviewData.rating}
              onChange={(e) => setReviewData({ ...reviewData, rating: parseInt(e.target.value) })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Comment (optional)</label>
            <textarea
              rows={3}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm"
              value={reviewData.comment}
              onChange={(e) => setReviewData({ ...reviewData, comment: e.target.value })}
            />
          </div>
          <div className="flex gap-3">
            <Button loading={submittingReview} onClick={handleSubmitReview}>Submit Review</Button>
            <Button variant="secondary" onClick={() => setShowReviewModal(false)}>Cancel</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
