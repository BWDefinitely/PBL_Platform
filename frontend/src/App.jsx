import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import TeacherDashboard from './pages/teacher/Dashboard';
import PlanGenerator from './pages/teacher/PlanGenerator';
import TaskManagement from './pages/teacher/TaskManagement';
import ProcessData from './pages/teacher/ProcessData';
import Evaluation from './pages/teacher/Evaluation';
import DecisionSupport from './pages/teacher/DecisionSupport';
import StudentDashboard from './pages/student/StudentDashboard';
import StudentTasks from './pages/student/StudentTasks';
import StudentReport from './pages/student/StudentReport';
import TeamChat from './pages/student/TeamChat';
import FileUpload from './pages/student/FileUpload';
import StudentProgress from './pages/student/StudentProgress';
import StudentProfile from './pages/student/StudentProfile';
import { useAuth } from './context/AuthContext';

function AppContent() {
  const { isAuthenticated, role, email, logout, isPreview, switchPreviewRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isAuthenticated && !['/login', '/register'].includes(location.pathname)) {
      navigate('/login');
      return;
    }
    if (isAuthenticated && !isPreview && role === 'teacher' && location.pathname.startsWith('/student')) {
      navigate('/teacher/dashboard');
    } else if (isAuthenticated && !isPreview && role === 'student' && location.pathname.startsWith('/teacher')) {
      navigate('/student/dashboard');
    }
  }, [isAuthenticated, role, location.pathname, navigate, isPreview]);

  if (!isAuthenticated) {
    return (
      <main className="main-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </main>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar
        role={role}
        userName={email}
        isPreview={isPreview}
        onSwitchRole={(nextRole) => {
          switchPreviewRole(nextRole);
          navigate(nextRole === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
        }}
        onLogout={() => {
          logout();
          navigate(isPreview ? (role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard') : '/login');
        }}
      />
      <main className="main-content">
        <Routes>
          {/* Teacher Routes */}
          <Route path="/teacher/dashboard" element={<TeacherDashboard />} />
          <Route path="/teacher/plan-generator" element={<PlanGenerator />} />
          <Route path="/teacher/task-management" element={<TaskManagement />} />
          <Route path="/teacher/process-data" element={<ProcessData />} />
          <Route path="/teacher/evaluation" element={<Evaluation />} />
          <Route path="/teacher/decision-support" element={<DecisionSupport />} />

          {/* Student Routes */}
          <Route path="/student/dashboard" element={<StudentDashboard />} />
          <Route path="/student/tasks" element={<StudentTasks />} />
          <Route path="/student/progress" element={<StudentProgress />} />
          <Route path="/student/chat" element={<TeamChat />} />
          <Route path="/student/files" element={<FileUpload />} />
          <Route path="/student/report" element={<StudentReport />} />
          <Route path="/student/profile" element={<StudentProfile />} />

          {/* Default */}
          <Route path="*" element={<Navigate to={role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard'} replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
