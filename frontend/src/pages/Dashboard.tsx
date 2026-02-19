import { useQuery } from '@tanstack/react-query';
import { BarChart3, Clock, AlertCircle, TrendingDown } from 'lucide-react';
import { apiClient } from '../api/client';

export default function Dashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => apiClient.get('/metrics/summary').then(r => r.data)
  });

  const { data: failures } = useQuery({
    queryKey: ['failures'],
    queryFn: () => apiClient.get('/failures?limit=10').then(r => r.data)
  });

  const avgTimeMinutes = metrics ? (metrics.avg_processing_time_ms / 1000 / 60).toFixed(1) : 0;
  const timeSaved = metrics ? ((45 - parseFloat(avgTimeMinutes)) * metrics.total_failures / 60).toFixed(1) : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Real-time CI/CD failure analysis metrics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Failures</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{metrics?.total_failures || 0}</p>
            </div>
            <AlertCircle className="w-12 h-12 text-red-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg RCA Time</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{avgTimeMinutes}m</p>
            </div>
            <Clock className="w-12 h-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Time Saved</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{timeSaved}h</p>
            </div>
            <TrendingDown className="w-12 h-12 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Categories</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {Object.keys(metrics?.category_breakdown || {}).length}
              </p>
            </div>
            <BarChart3 className="w-12 h-12 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Failure Categories</h2>
        <div className="space-y-3">
          {metrics && Object.entries(metrics.category_breakdown).map(([category, count]: [string, any]) => (
            <div key={category} className="flex items-center justify-between">
              <span className="text-gray-700 font-medium">{category}</span>
              <div className="flex items-center gap-3">
                <div className="w-48 bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full"
                    style={{ width: `${(count / metrics.total_failures) * 100}%` }}
                  />
                </div>
                <span className="text-gray-900 font-bold w-12 text-right">{count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Failures */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Failures</h2>
        <div className="space-y-3">
          {failures?.slice(0, 5).map((failure: any) => (
            <div key={failure.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <p className="font-medium text-gray-900">{failure.job_name}</p>
                <p className="text-sm text-gray-600">{failure.error_type}</p>
              </div>
              <span className={`px-3 py-1 rounded text-sm font-medium ${
                failure.failure_category === 'Test' ? 'bg-yellow-100 text-yellow-800' :
                failure.failure_category === 'Infrastructure' ? 'bg-red-100 text-red-800' :
                failure.failure_category === 'Auth' ? 'bg-orange-100 text-orange-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {failure.failure_category}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
