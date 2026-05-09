import { useState, useEffect } from 'react';
import { contractsApi } from '../api/contracts';
import toast from 'react-hot-toast';

export function useContract(contractId) {
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchContract = async () => {
    try {
      setLoading(true);
      const { data } = await contractsApi.get(contractId);
      setContract(data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load contract');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contractId) {
      fetchContract();
    }
  }, [contractId]);

  return { contract, loading, refetch: fetchContract };
}
