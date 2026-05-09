import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { contractsApi } from '../../api/contracts';
import { useAuth } from '../../hooks/useAuth';
import { ClauseEditor } from '../../components/contract/ClauseEditor';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Spinner } from '../../components/ui/Spinner';
import toast from 'react-hot-toast';

const STEPS = ['Subject', 'Timeline', 'Payment', 'Termination', 'Clauses', 'Review & Sign'];

export function ContractBuilderPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [contract, setContract] = useState(null);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);
  const [checked1, setChecked1] = useState(false);
  const [checked2, setChecked2] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data } = await contractsApi.get(id);
        setContract(data);
        setClauses(data.clauses || []);
      } catch {
        toast.error('Failed to load contract');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [id]);

  const getClauseByType = (type) => clauses.find((c) => c.clause_type === type) || { content: '' };
  const updateClauseContent = (type, content) => {
    setClauses(clauses.map((c) => c.clause_type === type ? { ...c, content } : c));
  };

  const saveClauses = async () => {
    try {
      setSaving(true);
      await contractsApi.updateClauses(id, clauses.map((c) => ({ id: c.id, content: c.content, position: c.position })));
      toast.success('Saved');
    } catch {
      toast.error('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleSign = async () => {
    try {
      setSigning(true);
      await saveClauses();
      const { data } = await contractsApi.sign(id);
      setContract(data);
      setClauses(data.clauses || []);
      toast.success(data.status === 'in_progress' ? 'Contract signed by both parties!' : 'Signed! Waiting for other party.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to sign');
    } finally {
      setSigning(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>;

  const isCustomer = contract?.customer_id === user?.id;
  const hasSigned = isCustomer ? !!contract?.customer_signed_at : !!contract?.executor_signed_at;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Contract Builder</h1>
        <p className="text-sm text-gray-500 mt-1">Contract #{id?.slice(0, 8)}</p>
      </div>

      {/* Step indicator */}
      <div className="mb-8 flex items-center">
        {STEPS.map((s, i) => (
          <React.Fragment key={s}>
            <button
              onClick={() => setStep(i)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                i === step ? 'bg-indigo-600 text-white' : i < step ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-500'
              }`}
            >
              {i + 1}. {s}
            </button>
            {i < STEPS.length - 1 && <div className="mx-1 flex-1 h-px bg-gray-200" />}
          </React.Fragment>
        ))}
      </div>

      {/* Step content */}
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        {step === 0 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Step 1: Project Subject</h2>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subject Description</label>
            <textarea
              rows={6}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm"
              value={getClauseByType('subject_description').content}
              onChange={(e) => updateClauseContent('subject_description', e.target.value)}
              placeholder="Describe the project subject and scope..."
            />
          </div>
        )}

        {step === 1 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Step 2: Timeline</h2>
            <textarea
              rows={4}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm"
              value={getClauseByType('timeline').content}
              onChange={(e) => updateClauseContent('timeline', e.target.value)}
              placeholder="Describe start date and milestone timeline..."
            />
          </div>
        )}

        {step === 2 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Step 3: Payment Terms</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Payment Type</label>
              <div className="flex gap-4">
                {['fixed', 'hourly', 'milestone'].map((pt) => (
                  <label key={pt} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="payment_type"
                      value={pt}
                      checked={contract?.payment_type === pt}
                      onChange={async () => {
                        const { data } = await contractsApi.update(id, { payment_type: pt });
                        setContract(data);
                      }}
                    />
                    <span className="capitalize text-sm">{pt}</span>
                  </label>
                ))}
              </div>
            </div>
            <textarea
              rows={4}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm"
              value={getClauseByType('payment_terms').content}
              onChange={(e) => updateClauseContent('payment_terms', e.target.value)}
              placeholder="Describe payment terms and schedule..."
            />
          </div>
        )}

        {step === 3 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Step 4: Termination Conditions</h2>
            <div className="mb-3 space-y-2">
              {['30-day notice required', 'Immediate termination for breach', 'Force majeure clause'].map((preset) => (
                <label key={preset} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      const current = getClauseByType('termination_conditions').content;
                      if (e.target.checked) {
                        updateClauseContent('termination_conditions', current ? `${current}\n${preset}` : preset);
                      }
                    }}
                  />
                  <span className="text-sm">{preset}</span>
                </label>
              ))}
            </div>
            <textarea
              rows={4}
              className="w-full rounded-lg border border-gray-300 p-3 text-sm"
              value={getClauseByType('termination_conditions').content}
              onChange={(e) => updateClauseContent('termination_conditions', e.target.value)}
              placeholder="Describe termination conditions..."
            />
          </div>
        )}

        {step === 4 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Step 5: Additional Clauses</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Review Period (days)</label>
                <input
                  type="number"
                  min={1}
                  className="w-24 rounded border border-gray-300 px-3 py-1 text-sm"
                  value={contract?.review_period_days || 3}
                  onChange={async (e) => {
                    const { data } = await contractsApi.update(id, { review_period_days: parseInt(e.target.value) });
                    setContract(data);
                  }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Refund Policy</label>
                <textarea
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 p-3 text-sm"
                  value={getClauseByType('refund_policy').content || 'Refunds are subject to mutual agreement within the review period.'}
                  onChange={(e) => updateClauseContent('refund_policy', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Platform Commission</label>
                <input
                  type="text"
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm bg-gray-50"
                  value="3% platform fee applies"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">IP Rights</label>
                <select
                  className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                  value={getClauseByType('ip_rights').content || 'Customer'}
                  onChange={(e) => updateClauseContent('ip_rights', e.target.value)}
                >
                  <option>Customer</option>
                  <option>Executor</option>
                  <option>Shared</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Confidentiality</label>
                <textarea
                  rows={2}
                  className="w-full rounded-lg border border-gray-300 p-3 text-sm"
                  value={getClauseByType('confidentiality').content}
                  onChange={(e) => updateClauseContent('confidentiality', e.target.value)}
                  placeholder="Both parties agree to maintain confidentiality..."
                />
              </div>
            </div>
          </div>
        )}

        {step === 5 && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Step 6: Review & Sign</h2>
            <ClauseEditor
              clauses={clauses}
              setClauses={setClauses}
              onSave={async (reordered) => {
                await contractsApi.updateClauses(id, reordered.map((c) => ({ id: c.id, content: c.content, position: c.position })));
              }}
            />
            <div className="mt-6 space-y-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={checked1} onChange={(e) => setChecked1(e.target.checked)} />
                <span className="text-sm">I have read and understood all contract terms</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={checked2} onChange={(e) => setChecked2(e.target.checked)} />
                <span className="text-sm">I agree to be bound by this contract</span>
              </label>

              {hasSigned ? (
                <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
                  ✓ You have signed this contract.
                  {contract?.status === 'in_progress'
                    ? ' Both parties have signed. Work can begin!'
                    : ' Waiting for the other party to sign.'}
                </div>
              ) : (
                <Button
                  className="mt-2"
                  loading={signing}
                  disabled={!checked1 || !checked2}
                  onClick={handleSign}
                >
                  Sign Contract
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 flex justify-between">
        <Button variant="secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>
          Previous
        </Button>
        <div className="flex gap-3">
          {step < STEPS.length - 1 && (
            <>
              <Button variant="outline" loading={saving} onClick={saveClauses}>Save</Button>
              <Button onClick={() => setStep(step + 1)}>Next</Button>
            </>
          )}
          {step === STEPS.length - 1 && (
            <Button variant="secondary" onClick={() => navigate(`/contracts/${id}`)}>
              View Contract
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
