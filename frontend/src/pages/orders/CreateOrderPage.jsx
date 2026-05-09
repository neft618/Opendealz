import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { ordersApi } from '../../api/orders';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

const schema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  budget: z.coerce.number().positive('Budget must be positive'),
  deadline: z.string().min(1, 'Deadline is required'),
});

export function CreateOrderPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      const { data: order } = await ordersApi.create(data);
      toast.success('Order created!');
      navigate(`/orders/${order.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Post New Order</h1>
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <Input
            label="Title"
            {...register('title')}
            error={errors.title?.message}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              {...register('description')}
              rows={4}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Describe your project requirements..."
            />
            {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
          </div>
          <Input
            label="Budget ($)"
            type="number"
            step="0.01"
            min="0"
            {...register('budget')}
            error={errors.budget?.message}
          />
          <Input
            label="Deadline"
            type="date"
            {...register('deadline')}
            error={errors.deadline?.message}
          />
          <div className="flex gap-3 pt-2">
            <Button type="submit" loading={loading}>Create Order</Button>
            <Button variant="secondary" type="button" onClick={() => navigate('/orders')}>
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
