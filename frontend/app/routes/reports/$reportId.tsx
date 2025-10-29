import { useParams } from 'react-router';
import { api } from '../../services/api';

const reportDetailApi = api.injectEndpoints({
    endpoints: (builder) => ({
        getReportById: builder.query<any, string>({
            query: (id) => `/reports?id=${id}`, // Assuming API can filter by ID
             transformResponse: (response: any[]) => response[0], // Assuming it returns a list with one item
             providesTags: (result, error, id) => [{ type: 'Reports', id }],
        }),
    }),
});

const { useGetReportByIdQuery } = reportDetailApi;
const baseUrl = import.meta.env.VITE_API_BASE_URL;

export default function ReportDetailPage() {
    const { reportId } = useParams<{ reportId: string }>();
    const { data: report, error, isLoading } = useGetReportByIdQuery(reportId!);

    if (isLoading) return <div>Loading report details...</div>;
    if (error || !report) return <div>Error loading report details.</div>;
    
    const pdfUrl = `${baseUrl}/report/pdf/${report.id}`;

    return (
        <div className="bg-white p-8 rounded-lg shadow">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold">Report Details</h1>
                    <p className="text-gray-500 text-sm">{report.id}</p>
                </div>
                 <a href={pdfUrl} target="_blank" rel="noreferrer" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Download PDF
                </a>
            </div>

            <div className="space-y-6">
                {report.users.map((userData: any) => {
                    const detectedVulnerabilities = userData.vulnerabilities.filter((vuln: any) => vuln.is_vulnerable);
                    return (
                        <div key={userData.user.uuid} className="p-4 border rounded-lg">
                            <h3 className="font-bold text-lg">{userData.user.name} on {userData.user.machine.friendly_name}</h3>
                            <p className="text-sm text-gray-600">Password Last Updated: {new Date(userData.user.password_updated_at).toLocaleDateString()}</p>
                            
                            <div className="mt-4">
                                <h4 className="font-semibold">Detected Vulnerabilities:</h4>
                                {detectedVulnerabilities.length > 0 ? (
                                    <ul className="list-disc list-inside mt-2 space-y-2">
                                        {detectedVulnerabilities.map((vuln: any) => (
                                            <li key={vuln.name} className="text-red-600">
                                                <span className="font-medium">{vuln.name} (Severity: {vuln.severity_score})</span>: {vuln.detected_description}
                                            </li>
                                        ))}
                                    </ul>
                                ) : (
                                    <p className="mt-2 text-gray-500">No vulnerabilities were detected for this user.</p>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}