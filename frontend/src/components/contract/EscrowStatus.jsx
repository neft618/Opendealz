import React, { useState } from 'react';
import { Copy, CheckCircle } from 'lucide-react';
import { StatusBadge } from '../ui/Badge';

function truncateHash(hash) {
  if (!hash) return '';
  return `${hash.slice(0, 8)}...${hash.slice(-8)}`;
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={handleCopy} className="ml-1 text-gray-400 hover:text-gray-600">
      {copied ? <CheckCircle size={14} className="text-green-500" /> : <Copy size={14} />}
    </button>
  );
}

export function EscrowStatus({ contract }) {
  const txs = contract?.escrow_transactions || [];
  const lockedAmount = txs
    .filter((t) => t.type === 'lock')
    .reduce((s, t) => s + Number(t.amount), 0);
  const fee = Number(contract?.platform_fee || 0);
  const payout = Number(contract?.total_amount || 0) - fee;

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h3 className="mb-3 font-semibold text-gray-900">Escrow Status</h3>
      <div className="mb-4 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-xs text-gray-500">Locked</p>
          <p className="text-lg font-bold text-gray-900">${lockedAmount.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Platform Fee</p>
          <p className="text-lg font-bold text-gray-900">${fee.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Executor Payout</p>
          <p className="text-lg font-bold text-green-600">${payout.toFixed(2)}</p>
        </div>
      </div>

      {txs.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-medium text-gray-700">Transactions</h4>
          <div className="space-y-2">
            {txs.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between rounded bg-white p-2 text-sm border border-gray-100">
                <div className="flex items-center gap-2">
                  <StatusBadge status={tx.status} />
                  <span className="capitalize text-gray-700">{tx.type}</span>
                  <span className="font-medium">${Number(tx.amount).toFixed(2)}</span>
                </div>
                <div className="flex items-center text-xs text-gray-400 font-mono">
                  {truncateHash(tx.tx_hash)}
                  <CopyButton text={tx.tx_hash} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {contract?.contract_hash && (
        <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
          <CheckCircle size={14} className="text-green-500" />
          <span>Contract hash: </span>
          <span className="font-mono">{truncateHash(contract.contract_hash)}</span>
          <CopyButton text={contract.contract_hash} />
        </div>
      )}
    </div>
  );
}
