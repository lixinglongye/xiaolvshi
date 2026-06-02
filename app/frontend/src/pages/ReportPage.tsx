import { Navigate, useParams } from 'react-router-dom';

export default function ReportPage() {
  const { id } = useParams();
  return <Navigate to={`/deep-report/${id ?? ''}`} replace />;
}
