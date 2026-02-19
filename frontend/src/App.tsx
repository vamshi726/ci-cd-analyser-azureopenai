import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import FailureList from './pages/FailureList';
import FailureDetail from './pages/FailureDetail';
import BeforeAfter from './pages/BeforeAfter';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          {/* Navigation */}
          <nav className="bg-blue-900 text-white shadow-lg">
            <div className="max-w-7xl mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">CI/CD RCA System</h1>
                <div className="flex gap-6">
                  <Link to="/" className="hover:text-blue-200">Dashboard</Link>
                  <Link to="/failures" className="hover:text-blue-200">Failures</Link>
                  <Link to="/compare" className="hover:text-blue-200">Before/After</Link>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/failures" element={<FailureList />} />
              <Route path="/failures/:id" element={<FailureDetail />} />
              <Route path="/compare" element={<BeforeAfter />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
