import { useState } from 'react';
import { useSearchParams, Link } from 'react-router';
import { api } from '../../services/api';
import DateTimePicker from 'react-datetime-picker';
import 'react-datetime-picker/dist/DateTimePicker.css';
import 'react-calendar/dist/Calendar.css';
import 'react-clock/dist/Clock.css';
import { toast } from 'react-toastify';

type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];


const scheduledScansApi = api.injectEndpoints({
    endpoints: (builder) => ({
        getScheduledScans: builder.query<any, { page: number; pageSize: number }>({
            query: ({ page, pageSize }) => `/scans/scheduled?page=${page}&page_size=${pageSize}`,
            providesTags: ['ScheduledScans'],
        }),
        scheduleScan: builder.mutation<any, any>({
            query: (body) => ({
                url: '/scans/scheduled',
                method: 'POST',
                body,
            }),
            invalidatesTags: ['ScheduledScans'],
        }),
    }),
});

const { useGetScheduledScansQuery, useScheduleScanMutation } = scheduledScansApi;

export default function ScheduledScansPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    const page = parseInt(searchParams.get('page') || '1', 10);
    const pageSize = 5;
    const { data, error, isLoading, isFetching } = useGetScheduledScansQuery({ page, pageSize });
    const [scheduleScan, { isLoading: isScheduling }] = useScheduleScanMutation();
    
    const [scheduledAt, setScheduledAt] = useState<Value>(new Date());
    const [options, setOptions] = useState(JSON.stringify([ "scan-type-a", "--verbose" ], null, 2));

    const handleScheduleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const date = scheduledAt instanceof Date ? scheduledAt : scheduledAt?.[0];
            if (!date) {
                toast.error("Please select a valid date.");
                return;
            }
            const parsedOptions = JSON.parse(options);
            await scheduleScan({
                scheduled_at: date.toISOString(),
                options: parsedOptions,
            }).unwrap();
            toast.success("Scan scheduled successfully!");
        } catch (err) {
            toast.error("Failed to schedule scan. Check options format.");
        }
    };

    const handlePrevPage = () => {
        setSearchParams({ page: Math.max(1, page - 1).toString() });
    };

    const handleNextPage = () => {
        setSearchParams({ page: (page + 1).toString() });
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-2 bg-white p-8 rounded-lg shadow">
                <h1 className="text-2xl font-bold mb-6">Scheduled Scans</h1>
                {isLoading && <p>Loading scans...</p>}
                {error && <p>Error loading scans.</p>}
                <div className="space-y-4">
                    {data?.map((scan: any) => (
                        <div key={scan.uuid} className="p-4 border rounded-lg flex justify-between items-center">
                            <div>
                                <p className={`font-semibold ${scan.completed_scan_id ? 'text-green-600' : 'text-yellow-600'}`}>
                                    {scan.completed_scan_id ? 'Completed' : 'Pending'}
                                </p>
                                <p className="text-sm text-gray-600">Scheduled for: {new Date(scan.scheduled_at).toLocaleString()}</p>
                                <details className="mt-2 text-sm">
                                    <summary className="cursor-pointer">View Options</summary>
                                    <pre className="bg-gray-100 p-2 rounded mt-1 text-xs">
                                        {JSON.stringify(scan.options, null, 2)}
                                    </pre>
                                </details>
                            </div>
                            {scan.completed_scan_id && (
                                <Link to={`/reports/${scan.completed_scan_id}`} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                                    View Report
                                </Link>
                            )}
                        </div>
                    ))}
                </div>
                 <div className="mt-6 flex justify-between items-center">
                    <button onClick={handlePrevPage} disabled={page === 1 || isFetching} className="px-4 py-2 bg-gray-300 rounded disabled:opacity-50">
                        Previous
                    </button>
                    <span>Page {page}</span>
                    <button onClick={handleNextPage} disabled={!data || data.length < pageSize || isFetching} className="px-4 py-2 bg-gray-300 rounded disabled:opacity-50">
                        Next
                    </button>
                </div>
            </div>
            <div className="bg-white p-8 rounded-lg shadow">
                 <h2 className="text-xl font-bold mb-6">Schedule a New Scan</h2>
                 <form onSubmit={handleScheduleSubmit} className="space-y-4">
                     <div>
                         <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time</label>
                         <DateTimePicker onChange={setScheduledAt} value={scheduledAt} className="w-full" />
                     </div>
                     <div>
                         <label className="block text-sm font-medium text-gray-700 mb-1">Options (JSON format)</label>
                         <textarea
                            rows={5}
                            value={options}
                            onChange={(e) => setOptions(e.target.value)}
                            className="w-full p-2 border rounded font-mono text-sm"
                         />
                     </div>
                     <button type="submit" disabled={isScheduling} className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                        {isScheduling ? 'Scheduling...' : 'Schedule Scan'}
                     </button>
                 </form>
            </div>
        </div>
    );
}