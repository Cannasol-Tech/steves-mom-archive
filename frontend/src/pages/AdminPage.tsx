import React from 'react';

const AdminPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="text-gray-600 mt-2">
          Manage system settings, user permissions, and monitor application performance.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Feature Toggles Card */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Toggles</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">NL→SQL Queries</span>
              <div className="relative inline-block w-10 mr-2 align-middle select-none">
                <input
                  type="checkbox"
                  name="nlsql-toggle"
                  id="nlsql-toggle"
                  className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  defaultChecked
                />
                <label
                  htmlFor="nlsql-toggle"
                  className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"
                ></label>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Email Integration</span>
              <div className="relative inline-block w-10 mr-2 align-middle select-none">
                <input
                  type="checkbox"
                  name="email-toggle"
                  id="email-toggle"
                  className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  defaultChecked
                />
                <label
                  htmlFor="email-toggle"
                  className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"
                ></label>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Document Generation</span>
              <div className="relative inline-block w-10 mr-2 align-middle select-none">
                <input
                  type="checkbox"
                  name="docs-toggle"
                  id="docs-toggle"
                  className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                  defaultChecked
                />
                <label
                  htmlFor="docs-toggle"
                  className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"
                ></label>
              </div>
            </div>
          </div>
        </div>

        {/* System Status Card */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">API Status</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Database</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">AI Model</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Pending
              </span>
            </div>
          </div>
        </div>

        {/* Quick Actions Card */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full btn-secondary text-left">
              View System Logs
            </button>
            <button className="w-full btn-secondary text-left">
              Export Analytics
            </button>
            <button className="w-full btn-secondary text-left">
              Manage Users
            </button>
          </div>
        </div>

        {/* Performance Metrics Card */}
        <div className="card md:col-span-2 lg:col-span-3">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">--</div>
              <div className="text-sm text-gray-600">Requests/Hour</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">--ms</div>
              <div className="text-sm text-gray-600">Avg Response Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">--%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">--</div>
              <div className="text-sm text-gray-600">Active Users</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-500">
            * Metrics will be populated when telemetry system is implemented (Phase 11)
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
