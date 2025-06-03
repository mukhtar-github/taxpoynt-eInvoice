import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, AlertTriangle, CheckCircle, RotateCcw, Zap, Database, Settings, RefreshCw } from 'lucide-react';
import { Button } from '../../ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/Tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/Table';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';
import { Skeleton } from '../../ui/Skeleton';

// Types for signature events
type SignatureEvent = {
  id: string;
  event_type: string;
  timestamp: string;
  timestamp_display?: string;
  user_id?: string;
  invoice_id?: string;
  signature_id?: string;
  duration_ms?: number;
  duration_display?: string;
  success?: boolean;
  error_message?: string;
  details?: Record<string, any>;
};

type SignatureStats = {
  verification: {
    total_count: number;
    success_rate: number;
    avg_duration_ms: number;
  };
  generation: {
    total_count: number;
    success_rate: number;
    avg_duration_ms: number;
  };
  cache: {
    hits: number;
    misses: number;
    hit_rate: number;
  };
  time_range: string;
};

const EventTypeIcon = ({ type }: { type: string }) => {
  switch (type) {
    case 'verification':
      return <CheckCircle className="h-4 w-4 text-cyan-500" />;
    case 'generation':
      return <Zap className="h-4 w-4 text-amber-500" />;
    case 'cache_hit':
      return <Database className="h-4 w-4 text-green-500" />;
    case 'cache_miss':
      return <Database className="h-4 w-4 text-gray-500" />;
    case 'cache_clear':
      return <RotateCcw className="h-4 w-4 text-blue-500" />;
    case 'error':
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    case 'settings_change':
    case 'settings_retrieval':
    case 'settings_rollback':
      return <Settings className="h-4 w-4 text-purple-500" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
};

const EventStatusBadge = ({ event }: { event: SignatureEvent }) => {
  if (event.event_type === 'error') {
    return <Badge variant="destructive">Error</Badge>;
  }
  if (event.success === false) {
    return <Badge variant="destructive">Failed</Badge>;
  }
  if (event.success === true) {
    return <Badge variant="success">Success</Badge>;
  }
  if (event.event_type === 'cache_hit') {
    return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Cache Hit</Badge>;
  }
  if (event.event_type === 'cache_miss') {
    return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">Cache Miss</Badge>;
  }
  if (event.event_type === 'settings_change') {
    return <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">Settings Updated</Badge>;
  }
  
  return null;
};

export const SignatureEventsMonitor: React.FC = () => {
  const [events, setEvents] = useState<SignatureEvent[]>([]);
  const [stats, setStats] = useState<SignatureStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [eventType, setEventType] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('24h');

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const params: Record<string, any> = { limit: 50 };
      if (eventType) {
        params.event_type = eventType;
      }
      
      const response = await axios.get('/api/platform/signatures/events/recent', { params });
      setEvents(response.data.events || []);
      setError('');
    } catch (err) {
      console.error('Error fetching signature events:', err);
      setError('Failed to load signature events. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const params: Record<string, any> = { time_range: timeRange };
      if (eventType) {
        params.event_type = eventType;
      }
      
      const response = await axios.get('/api/platform/signatures/events/stats', { params });
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching signature stats:', err);
    }
  };

  useEffect(() => {
    fetchEvents();
    fetchStats();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      fetchEvents();
      fetchStats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [eventType, timeRange]);

  const handleClearEvents = async () => {
    try {
      await axios.post('/api/platform/signatures/events/clear');
      fetchEvents();
      fetchStats();
    } catch (err) {
      console.error('Error clearing events:', err);
      setError('Failed to clear events. Please try again.');
    }
  };

  const formatEventDetails = (event: SignatureEvent) => {
    if (!event.details) return 'No details available';
    
    try {
      return Object.entries(event.details)
        .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
        .join(', ');
    } catch (e) {
      return 'Error parsing details';
    }
  };

  return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-cyan-500" />
              Signature Events Monitor
              <Badge variant="outline" className="ml-2 bg-cyan-50 text-cyan-700 border-cyan-200">Platform</Badge>
            </CardTitle>
            <CardDescription>
              Track and monitor signature events across the system
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => {
                fetchEvents();
                fetchStats();
              }}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Button 
              variant="destructive" 
              size="sm"
              onClick={handleClearEvents}
            >
              Clear Events
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <Tabs defaultValue="events" className="w-full">
        <div className="px-6">
          <TabsList className="grid grid-cols-2">
            <TabsTrigger value="events">Recent Events</TabsTrigger>
            <TabsTrigger value="stats">Performance Metrics</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="events" className="p-0">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 mb-4">
              <div>
                <label className="text-sm font-medium">Filter by event type:</label>
                <select 
                  className="ml-2 p-1 border rounded text-sm"
                  value={eventType || ''}
                  onChange={(e) => setEventType(e.target.value || null)}
                >
                  <option value="">All events</option>
                  <option value="verification">Verification</option>
                  <option value="generation">Generation</option>
                  <option value="cache_hit">Cache Hit</option>
                  <option value="cache_miss">Cache Miss</option>
                  <option value="error">Errors</option>
                  <option value="settings_change">Settings Changes</option>
                </select>
              </div>
            </div>

            {error && (
              <Alert variant="error" className="mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            {loading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : events.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No signature events found.
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[120px]">Type</TableHead>
                      <TableHead className="w-[180px]">Timestamp</TableHead>
                      <TableHead>Details</TableHead>
                      <TableHead className="w-[100px]">Duration</TableHead>
                      <TableHead className="w-[120px]">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {events.map((event) => (
                      <TableRow key={event.id}>
                        <TableCell className="font-medium flex items-center gap-1">
                          <EventTypeIcon type={event.event_type} />
                          <span className="capitalize text-xs">
                            {event.event_type.replace('_', ' ')}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs">
                          {event.timestamp_display || new Date(event.timestamp).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-xs truncate max-w-[400px]">
                          {event.invoice_id && <span className="font-medium">Invoice: {event.invoice_id}</span>}
                          {event.invoice_id && event.error_message ? ' - ' : ''}
                          {event.error_message ? (
                            <span className="text-red-600">{event.error_message}</span>
                          ) : (
                            formatEventDetails(event)
                          )}
                        </TableCell>
                        <TableCell className="text-xs">
                          {event.duration_display || (event.duration_ms ? `${event.duration_ms.toFixed(2)} ms` : '-')}
                        </TableCell>
                        <TableCell>
                          <EventStatusBadge event={event} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </TabsContent>

        <TabsContent value="stats">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 mb-4">
              <div>
                <label className="text-sm font-medium">Time range:</label>
                <select 
                  className="ml-2 p-1 border rounded text-sm"
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                >
                  <option value="1h">Last hour</option>
                  <option value="24h">Last 24 hours</option>
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                </select>
              </div>
            </div>

            {!stats ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Verification Stats */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-cyan-500" />
                      Verification
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Total count</span>
                        <span className="font-medium">{stats.verification.total_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Success rate</span>
                        <span className="font-medium">{(stats.verification.success_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Avg. duration</span>
                        <span className="font-medium">{stats.verification.avg_duration_ms.toFixed(2)} ms</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                {/* Generation Stats */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Zap className="h-4 w-4 text-amber-500" />
                      Generation
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Total count</span>
                        <span className="font-medium">{stats.generation.total_count}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Success rate</span>
                        <span className="font-medium">{(stats.generation.success_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Avg. duration</span>
                        <span className="font-medium">{stats.generation.avg_duration_ms.toFixed(2)} ms</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                {/* Cache Stats */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Database className="h-4 w-4 text-green-500" />
                      Cache Performance
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Hit rate</span>
                        <span className="font-medium">{(stats.cache.hit_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Hits</span>
                        <span className="font-medium">{stats.cache.hits}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-muted-foreground">Misses</span>
                        <span className="font-medium">{stats.cache.misses}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </CardContent>
        </TabsContent>
      </Tabs>
      
      <CardFooter className="text-xs text-muted-foreground border-t py-3">
        Data refreshes automatically every 30 seconds. Last update: {new Date().toLocaleTimeString()}
      </CardFooter>
    </Card>
  );
};

export default SignatureEventsMonitor;
