import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const isDark = theme === 'dark';

  return (
    <div className="flex-1 h-full bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">Profile Information</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">Personal details and account status.</p>
          </div>
          <div className="px-6 py-5 space-y-6">
            <div className="grid grid-cols-6 gap-6">
              <div className="col-span-6 sm:col-span-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Full Name</label>
                <input
                  type="text"
                  disabled
                  value={user?.full_name || ''}
                  className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md bg-gray-100 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 cursor-not-allowed px-3 py-2"
                />
              </div>
              <div className="col-span-6 sm:col-span-3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Email Address</label>
                <input
                  type="text"
                  disabled
                  value={user?.email || ''}
                  className="mt-1 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md bg-gray-100 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 cursor-not-allowed px-3 py-2"
                />
              </div>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Account created on {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
           <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">Appearance</h3>
          </div>
          <div className="px-6 py-5 flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900 dark:text-white">Dark Mode</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Toggle dark theme for the dashboard.</div>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative inline-flex flex-shrink-0 h-6 w-11 border-2 border-transparent rounded-full cursor-pointer transition-colors ease-in-out duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 ${
                isDark ? 'bg-brand-600' : 'bg-gray-200'
              }`}
            >
              <span className="sr-only">Use setting</span>
              <span
                aria-hidden="true"
                className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition ease-in-out duration-200 ${
                  isDark ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};