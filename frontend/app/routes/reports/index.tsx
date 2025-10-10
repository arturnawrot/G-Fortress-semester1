import { useState } from 'react';
import { Link } from 'react-router'; // Changed from 'react-router-dom'
import { api } from '../../services/api';

const reportsApi = api.injectEndpoints({
    endpoints: (builder) => ({
        getReports: builder.query<any, { page: number; pageSize: number }>({
            query: ({ page, pageSize }) => `/reports?page=${page}&page_size=${pageSize}`,
            providesTags: (result) => 
                result ? [...result.map(({ id }: any) => ({ type: 'Reports' as const, id })), { type: 'Reports', id: 'LIST' }] : [{ type: 'Reports', id: 'LIST' }],
        }),
    }),
});

const { useGetReportsQuery } = reportsApi;

export default function ReportsPage() {
    const [page, setPage] = useState(1);
    const pageSize = 10;
    const { data, error, isLoading, isFetching } = useGetReportsQuery({ page, pageSize });

    if (isLoading) return <div>Loading reports...</div>;
    if (error) return <div>Error loading reports.</div>;

    return (
        <div className="bg-white p-8 rounded-lg shadow">
            <h1 className="text-2xl font-bold mb-6">Completed Reports</h1>
            <div className="space-y-4">
                {data?.map((report: any) => (
                    <Link to={`/reports/${report.id}`} key={report.id} className="block p-4 border rounded-lg hover:bg-gray-50">
                        <p className="font-semibold">Report ID: {report.id}</p>
                        <p className="text-sm text-gray-600">Created At: {new Date(report.created_at).toLocaleString()}</p>
                        <p className="text-sm text-gray-600">{report.users.length} users analyzed.</p>
                    </Link>
                ))}
            </div>
             <div className="mt-6 flex justify-between items-center">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1 || isFetching} className="px-4 py-2 bg-gray-300 rounded disabled:opacity-50">
                    Previous
                </button>
                <span>Page {page}</span>
                <button onClick={() => setPage(p => p + 1)} disabled={!data || data.length < pageSize || isFetching} className="px-4 py-2 bg-gray-300 rounded disabled:opacity-50">
                    Next
                </button>
            </div>
        </div>
    );
}