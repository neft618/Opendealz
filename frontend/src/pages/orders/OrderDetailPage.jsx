import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ordersApi } from '../../api/orders';
import { useAuth } from '../../hooks/useAuth';
import { StatusBadge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Spinner } from '../../components/ui/Spinner';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, activeRole } = useAuth();
  const [order, setOrder] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applyData, setApplyData] = useState({ cover_letter: '', proposed_price: '' });
  const [applying, setApplying] = useState(false);
  const [accepting, setAccepting] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data: o } = await ordersApi.get(id);
        setOrder(o);
        if (o.customer_id === user?.id) {
          const { data: apps } = await ordersApi.getApplications(id);
          setApplications(apps);
        }
      } catch (err) {
        toast.error(err.response?.data?.detail || 'Failed to load order');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, user]);

  const handleApply = async () => {
    try {
      setApplying(true);
      await ordersApi.applyToOrder(id, {
        cover_letter: applyData.cover_letter,
        proposed_price: parseFloat(applyData.proposed_price),
      });
      toast.success('Application submitted!');
      setShowApplyModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to apply');
    } finally {
      setApplying(false);
    }
  };

  const handleAcceptApplication = async (appId) => {
    try {
      setAccepting(appId);
      const { data: contract } = await ordersApi.acceptApplication(id, appId);
      toast.success('Application accepted! Contract created.');
      navigate(`/contracts/${contract.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to accept application');
    } finally {
      setAccepting(null);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>;
  if (!order) return null;

  const isCustomer = order.customer_id === user?.id;
  const isExecutor = activeRole === 'executor';
  const canApply = isExecutor && order.status === 'open' && !isCustomer;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{order.title}</h1>
            <p className="mt-1 text-sm text-gray-500">
              Posted {format(new Date(order.created_at), 'MMM d, yyyy')}
            </p>
          </div>
          <StatusBadge status={order.status} />
        </div>

        <p className="text-gray-700 mb-6">{order.description}</p>

        <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-xs text-gray-500">Budget</p>
            <p className="font-semibold text-gray-900">${Number(order.budget).toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Deadline</p>
            <p className="font-semibold text-gray-900">{format(new Date(order.deadline), 'MMM d, yyyy')}</p>
          </div>
        </div>

        {canApply && (
          <Button onClick={() => setShowApplyModal(true)}>Apply Now</Button>
        )}
      </div>

      {isCustomer && applications.length > 0 && (
        <div className="mt-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Applications ({applications.length})</h2>
          <div className="space-y-4">
            {applications.map((app) => (
              <div key={app.id} className="rounded-lg border border-gray-200 bg-white p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <Link
                      to={`/users/${app.executor_id}`}
                      className="font-medium text-indigo-600 hover:underline"
                    >
                      View Applicant Profile
                    </Link>
                    <p className="mt-2 text-sm text-gray-700">{app.cover_letter}</p>
                    <p className="mt-1 text-sm font-medium text-gray-900">
                      Proposed: ${Number(app.proposed_price).toFixed(2)}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <StatusBadge status={app.status} />
                    {app.status === 'pending' && order.status === 'open' && (
                      <Button
                        size="sm"
                        loading={accepting === app.id}
                        onClick={() => handleAcceptApplication(app.id)}
                      >
                        Accept
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <Modal isOpen={showApplyModal} onClose={() => setShowApplyModal(false)} title="Apply for this Order">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cover Letter</label>
            <textarea
              rows={4}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              value={applyData.cover_letter}
              onChange={(e) => setApplyData({ ...applyData, cover_letter: e.target.value })}
              placeholder="Describe your experience and approach..."
            />
          </div>
          <Input
            label="Proposed Price ($)"
            type="number"
            step="0.01"
            min="0"
            value={applyData.proposed_price}
            onChange={(e) => setApplyData({ ...applyData, proposed_price: e.target.value })}
          />
          <div className="flex gap-3">
            <Button loading={applying} onClick={handleApply}>Submit Application</Button>
            <Button variant="secondary" onClick={() => setShowApplyModal(false)}>Cancel</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
