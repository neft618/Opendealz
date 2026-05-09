import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Navbar } from './components/layout/Navbar';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { AdminRoute } from './components/layout/AdminRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { OrdersListPage } from './pages/orders/OrdersListPage';
import { CreateOrderPage } from './pages/orders/CreateOrderPage';
import { OrderDetailPage } from './pages/orders/OrderDetailPage';
import { ContractDetailPage } from './pages/contracts/ContractDetailPage';
import { ContractBuilderPage } from './pages/contracts/ContractBuilderPage';
import { DisputePage } from './pages/disputes/DisputePage';

function PlaceholderPage({ title }) {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
      <p className="mt-2 text-sm text-gray-600">This page is not implemented yet.</p>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Navbar />
      <Routes>
        <Route path="/" element={<Navigate to="/orders" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/orders"
          element={
            <ProtectedRoute>
              <OrdersListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders/create"
          element={
            <ProtectedRoute>
              <CreateOrderPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders/:id"
          element={
            <ProtectedRoute>
              <OrderDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/contracts/:id"
          element={
            <ProtectedRoute>
              <ContractDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/contracts/:id/build"
          element={
            <ProtectedRoute>
              <ContractBuilderPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/disputes/:id"
          element={
            <ProtectedRoute>
              <DisputePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <PlaceholderPage title="Admin Dashboard" />
            </AdminRoute>
          }
        />
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Notifications" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="Profile" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users/:id"
          element={
            <ProtectedRoute>
              <PlaceholderPage title="User Profile" />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/orders" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
