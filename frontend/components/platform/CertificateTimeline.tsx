import React from 'react';
import { format } from 'date-fns';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Rotate3D, 
  Download,
  UploadCloud,
  Shield,
  FileText
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';
import { Certificate } from '../../types/app';

export interface CertificateEvent {
  id: string;
  certificateId: string;
  eventType: 'created' | 'activated' | 'renewed' | 'revoked' | 'expired' | 'backed_up' | 'restored' | 'validated';
  timestamp: string;
  details?: string;
  performedBy?: string;
}

interface CertificateTimelineProps {
  certificate: Certificate;
  events: CertificateEvent[];
  className?: string;
}

/**
 * Certificate Timeline Component
 * 
 * Displays a chronological timeline of certificate-related events
 * from creation to the present status, including important milestones
 * such as activation, renewal, backup, and expiration warnings.
 */
const CertificateTimeline: React.FC<CertificateTimelineProps> = ({
  certificate,
  events,
  className = ''
}) => {
  // Sort events by timestamp (newest first)
  const sortedEvents = [...events].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  // Get appropriate icon for each event type
  const getEventIcon = (eventType: string) => {
    switch(eventType) {
      case 'created':
        return <FileText className="h-5 w-5" />;
      case 'activated':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'renewed':
        return <Rotate3D className="h-5 w-5 text-blue-500" />;
      case 'revoked':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'expired':
        return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'backed_up':
        return <Download className="h-5 w-5 text-indigo-500" />;
      case 'restored':
        return <UploadCloud className="h-5 w-5 text-purple-500" />;
      case 'validated':
        return <Shield className="h-5 w-5 text-cyan-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  // Format date in a user-friendly way
  const formatEventDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      return `Today at ${format(date, 'h:mm a')}`;
    } else if (diffInDays === 1) {
      return `Yesterday at ${format(date, 'h:mm a')}`;
    } else if (diffInDays < 7) {
      return `${diffInDays} days ago`;
    } else {
      return format(date, 'MMM d, yyyy');
    }
  };

  // Get badge for event type
  const getEventBadge = (eventType: string) => {
    switch(eventType) {
      case 'created':
        return <Badge className="bg-blue-100 text-blue-800">Created</Badge>;
      case 'activated':
        return <Badge className="bg-green-100 text-green-800">Activated</Badge>;
      case 'renewed':
        return <Badge className="bg-blue-100 text-blue-800">Renewed</Badge>;
      case 'revoked':
        return <Badge className="bg-red-100 text-red-800">Revoked</Badge>;
      case 'expired':
        return <Badge className="bg-orange-100 text-orange-800">Expired</Badge>;
      case 'backed_up':
        return <Badge className="bg-indigo-100 text-indigo-800">Backed Up</Badge>;
      case 'restored':
        return <Badge className="bg-purple-100 text-purple-800">Restored</Badge>;
      case 'validated':
        return <Badge className="bg-cyan-100 text-cyan-800">Validated</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  return (
    <Card className={cn('border-l-4 border-cyan-500', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center">
          <Clock className="h-5 w-5 mr-2 text-cyan-500" />
          Certificate Timeline
        </CardTitle>
      </CardHeader>
      <CardContent>
        {sortedEvents.length === 0 ? (
          <div className="text-center py-6 text-gray-500">
            No events recorded for this certificate
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
            
            {/* Timeline events */}
            <div className="space-y-6">
              {sortedEvents.map((event) => (
                <div key={event.id} className="relative pl-10">
                  {/* Timeline dot */}
                  <div className="absolute left-0 p-1 bg-white rounded-full border-2 border-cyan-500">
                    {getEventIcon(event.eventType)}
                  </div>
                  
                  {/* Event content */}
                  <div className="bg-white p-3 rounded-md border border-gray-200 shadow-sm">
                    <div className="flex justify-between items-start mb-1">
                      <div className="flex items-center">
                        {getEventBadge(event.eventType)}
                        {event.performedBy && (
                          <span className="ml-2 text-sm text-gray-600">by {event.performedBy}</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatEventDate(event.timestamp)}
                      </span>
                    </div>
                    {event.details && (
                      <p className="text-sm text-gray-700">{event.details}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CertificateTimeline;
