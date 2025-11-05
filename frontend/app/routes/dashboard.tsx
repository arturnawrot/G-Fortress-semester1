import { Link } from 'react-router';

export default function Dashboard() {
  return (
    <div className="bg-white p-8 rounded-lg shadow space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to G-Fortress</h1>
        <p className="text-lg text-gray-600">
          This is your central hub for managing security scans and reports. Use the navigation bar at the top to get started.
        </p>
      </div>

      <div className="border-t border-gray-200 pt-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6">How to Use Your Dashboard</h2>

        <div className="space-y-6">
          {/* Reports Section */}
          <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-bold text-xl text-indigo-700 mb-2">
              <Link
                to="/reports"
                className="hover:underline hover:text-indigo-800 transition-colors duration-150"
              >
                Reports
              </Link>
            </h3>
            <p className="text-gray-700">
              Navigate to the{' '}
              <Link
                to="/reports"
                className="font-semibold text-indigo-600 hover:underline"
              >
                Reports
              </Link>{' '}
              page to view a paginated list of all completed security scans. Each item in the list
              represents a finalized report. Click on any report to see a detailed breakdown of the
              findings, including any detected vulnerabilities for each user and machine analyzed.
            </p>
          </div>

          {/* Scheduled Scans Section */}
          <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-bold text-xl text-indigo-700 mb-2">
              <Link
                to="/scheduled-scans"
                className="hover:underline hover:text-indigo-800 transition-colors duration-150"
              >
                Scheduled Scans
              </Link>
            </h3>
            <p className="text-gray-700">
              The{' '}
              <Link
                to="/scheduled-scans"
                className="font-semibold text-indigo-600 hover:underline"
              >
                Scheduled Scans
              </Link>{' '}
              page allows you to plan future scans. Here, you can see a list of all pending and
              completed scheduled tasks. You can also schedule a new scan by specifying the date,
              time, and any custom options in JSON format. Once a scheduled scan is complete, a link
              to its corresponding report will appear.
            </p>
          </div>

          {/* AES Encryption Section */}
          <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
            <h3 className="font-bold text-xl text-indigo-700 mb-2">AES Encryption Toggle</h3>
            <p className="text-gray-700">
              Located in the top-right of the navigation bar, the{' '}
              <span className="font-semibold">AES Encryption</span> toggle controls the end-to-end
              encryption for all communication with the server. When enabled, all data sent and
              received by your browser is securely encrypted using a session-specific AES key,
              providing an extra layer of security.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}