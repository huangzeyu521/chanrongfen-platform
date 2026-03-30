import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore'
import LoginPage from './pages/LoginPage'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import EnterprisePage from './pages/EnterprisePage'
import ExpertPage from './pages/ExpertPage'
import RegionPage from './pages/RegionPage'
import DockingPage from './pages/DockingPage'
import MemberPage from './pages/MemberPage'

function RequireAuth({ children }) {
  const isAuthenticated = useAuthStore(s => s.isAuthenticated)
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="enterprises" element={<EnterprisePage />} />
        <Route path="experts" element={<ExpertPage />} />
        <Route path="regions" element={<RegionPage />} />
        <Route path="dockings" element={<DockingPage />} />
        <Route path="members" element={<MemberPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
