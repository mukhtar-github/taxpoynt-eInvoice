import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Separator } from '../ui/separator';
import { 
  Phone, 
  Mail, 
  MessageCircle, 
  MapPin, 
  Calendar,
  Star,
  Users,
  Building,
  Clock,
  Heart,
  VideoIcon,
  User
} from 'lucide-react';

interface RelationshipManager {
  id: string;
  name: string;
  email: string;
  phone: string;
  whatsapp_number?: string;
  photo_url?: string;
  office_location?: string;
  local_language_preference: 'english' | 'hausa' | 'yoruba' | 'igbo';
  meeting_availability: string[];
  timezone: string;
  industry_specialization: string[];
  client_capacity: number;
  current_client_count: number;
  is_active: boolean;
}

interface ClientAssignment {
  id: string;
  relationship_manager: RelationshipManager;
  assigned_date: string;
  is_primary: boolean;
  cultural_preferences?: {
    greeting_style: 'formal' | 'traditional' | 'modern';
    communication_pace: 'relationship_first' | 'business_first';
    meeting_protocols: {
      relationship_building_time: number;
      hierarchy_acknowledgment: boolean;
      gift_exchange_customs: boolean;
    };
  };
  support_channels: {
    whatsapp_business_api: boolean;
    voice_calls: boolean;
    video_calls: boolean;
    in_person_meetings: boolean;
    traditional_email: boolean;
  };
  relationship_score: number;
  last_interaction_date?: string;
  interaction_frequency: 'daily' | 'weekly' | 'monthly';
}

interface BusinessInteraction {
  id: string;
  interaction_type: 'call' | 'meeting' | 'whatsapp' | 'email' | 'video';
  interaction_subject: string;
  interaction_date: string;
  duration_minutes?: number;
  relationship_building_time?: number;
  business_discussion_time?: number;
  interaction_outcome: 'positive' | 'neutral' | 'negative';
  follow_up_required: boolean;
  follow_up_date?: string;
}

interface RelationshipManagerSystemProps {
  organizationId: string;
  clientAssignment?: ClientAssignment;
  onRequestAssignment?: () => void;
  onScheduleMeeting?: (managerId: string) => void;
  onLogInteraction?: (interactionData: Partial<BusinessInteraction>) => void;
}

const LANGUAGE_NAMES = {
  english: 'English',
  hausa: 'Hausa',
  yoruba: 'Yoruba',
  igbo: 'Igbo'
};

const LANGUAGE_GREETINGS = {
  english: 'Good day',
  hausa: 'Sannu',
  yoruba: 'E kaaro',
  igbo: 'Ndewo'
};

const WhatsAppButton: React.FC<{ number: string }> = ({ number }) => (
  <Button
    variant="outline"
    size="sm"
    onClick={() => window.open(`https://wa.me/${number.replace(/[^\d]/g, '')}`, '_blank')}
    className="text-green-600 hover:text-green-700 hover:bg-green-50"
  >
    <MessageCircle className="w-4 h-4 mr-1" />
    WhatsApp
  </Button>
);

const CallButton: React.FC<{ number: string }> = ({ number }) => (
  <Button
    variant="outline"
    size="sm"
    onClick={() => window.open(`tel:${number}`, '_self')}
    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
  >
    <Phone className="w-4 h-4 mr-1" />
    Call
  </Button>
);

const EmailButton: React.FC<{ email: string }> = ({ email }) => (
  <Button
    variant="outline"
    size="sm"
    onClick={() => window.open(`mailto:${email}`, '_self')}
    className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
  >
    <Mail className="w-4 h-4 mr-1" />
    Email
  </Button>
);

const VideoCallButton: React.FC<{ onVideoCall: () => void }> = ({ onVideoCall }) => (
  <Button
    variant="outline"
    size="sm"
    onClick={onVideoCall}
    className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
  >
    <VideoIcon className="w-4 h-4 mr-1" />
    Video Call
  </Button>
);

const RelationshipManagerCard: React.FC<{
  manager: RelationshipManager;
  assignment?: ClientAssignment;
  onScheduleMeeting?: () => void;
  onLogInteraction?: () => void;
}> = ({ manager, assignment, onScheduleMeeting, onLogInteraction }) => {
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  const getRelationshipScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getAvailabilityStatus = () => {
    const now = new Date();
    const currentHour = now.getHours();
    
    // Assume business hours are 8 AM to 6 PM Lagos time
    if (currentHour >= 8 && currentHour < 18) {
      return { status: 'Available', color: 'bg-green-500' };
    } else if (currentHour >= 18 && currentHour < 20) {
      return { status: 'Limited', color: 'bg-yellow-500' };
    } else {
      return { status: 'Unavailable', color: 'bg-red-500' };
    }
  };

  const availability = getAvailabilityStatus();
  const greeting = LANGUAGE_GREETINGS[manager.local_language_preference];

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader className="pb-4">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Avatar className="w-16 h-16">
              <AvatarImage src={manager.photo_url} alt={manager.name} />
              <AvatarFallback className="bg-blue-100 text-blue-600 font-semibold">
                {getInitials(manager.name)}
              </AvatarFallback>
            </Avatar>
            <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full ${availability.color} border-2 border-white`} />
          </div>
          
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-lg">{manager.name}</CardTitle>
              <Badge variant="secondary" className="text-xs">
                {LANGUAGE_NAMES[manager.local_language_preference]}
              </Badge>
            </div>
            <CardDescription className="text-sm mt-1">
              Your Dedicated Relationship Manager
            </CardDescription>
            <div className="flex items-center space-x-2 mt-2">
              <span className="text-sm text-gray-600">{greeting}!</span>
              <span className={`text-xs px-2 py-1 rounded-full ${availability.color} text-white`}>
                {availability.status}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Contact Methods */}
        <div className="flex flex-wrap gap-2">
          <CallButton number={manager.phone} />
          <EmailButton email={manager.email} />
          {manager.whatsapp_number && (
            <WhatsAppButton number={manager.whatsapp_number} />
          )}
          {assignment?.support_channels?.video_calls && (
            <VideoCallButton onVideoCall={() => onLogInteraction?.()} />
          )}
        </div>

        <Separator />

        {/* Manager Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span>{manager.office_location || 'Lagos, Nigeria'}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-gray-500" />
            <span>{manager.current_client_count}/{manager.client_capacity} clients</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Building className="w-4 h-4 text-gray-500" />
            <span>{manager.industry_specialization?.join(', ') || 'General'}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span>{manager.timezone}</span>
          </div>
        </div>

        {assignment && (
          <>
            <Separator />
            
            {/* Relationship Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <Heart className="w-4 h-4 text-pink-500" />
                <span className="text-sm">Relationship Score:</span>
                <span className={`font-semibold ${getRelationshipScoreColor(assignment.relationship_score)}`}>
                  {assignment.relationship_score.toFixed(1)}/10
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm">
                  Last contact: {assignment.last_interaction_date 
                    ? new Date(assignment.last_interaction_date).toLocaleDateString()
                    : 'Never'
                  }
                </span>
              </div>
            </div>

            {/* Cultural Preferences */}
            {assignment.cultural_preferences && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <h4 className="font-medium text-sm mb-2">Cultural Preferences</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-600">Greeting Style:</span>
                    <Badge variant="outline" className="ml-2 text-xs">
                      {assignment.cultural_preferences.greeting_style}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-gray-600">Communication:</span>
                    <Badge variant="outline" className="ml-2 text-xs">
                      {assignment.cultural_preferences.communication_pace.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-gray-600">Relationship Building:</span>
                    <span className="ml-2 font-medium">
                      {assignment.cultural_preferences.meeting_protocols.relationship_building_time} min
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Hierarchy Respect:</span>
                    <span className="ml-2">
                      {assignment.cultural_preferences.meeting_protocols.hierarchy_acknowledgment ? '✓' : '✗'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 pt-2">
          <Button 
            variant="default" 
            size="sm"
            onClick={onScheduleMeeting}
            className="flex items-center space-x-1"
          >
            <Calendar className="w-4 h-4" />
            <span>Schedule Meeting</span>
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={onLogInteraction}
            className="flex items-center space-x-1"
          >
            <User className="w-4 h-4" />
            <span>Log Interaction</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export const RelationshipManagerSystem: React.FC<RelationshipManagerSystemProps> = ({
  organizationId,
  clientAssignment,
  onRequestAssignment,
  onScheduleMeeting,
  onLogInteraction
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [recentInteractions, setRecentInteractions] = useState<BusinessInteraction[]>([]);

  useEffect(() => {
    // Load recent interactions
    loadRecentInteractions();
  }, [organizationId]);

  const loadRecentInteractions = async () => {
    try {
      const response = await fetch(`/api/nigerian/interactions/${organizationId}`);
      if (response.ok) {
        const data = await response.json();
        setRecentInteractions(data.interactions || []);
      }
    } catch (error) {
      console.error('Failed to load interactions:', error);
    }
  };

  const handleScheduleMeeting = () => {
    if (clientAssignment?.relationship_manager) {
      onScheduleMeeting?.(clientAssignment.relationship_manager.id);
    }
  };

  const handleLogInteraction = () => {
    onLogInteraction?.({
      interaction_type: 'call',
      interaction_subject: '',
      interaction_date: new Date().toISOString(),
      interaction_outcome: 'positive'
    });
  };

  if (!clientAssignment) {
    return (
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Relationship Manager Assignment</CardTitle>
          <CardDescription>
            Get assigned a dedicated Nigerian relationship manager for personalized support
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <User className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">
              No relationship manager assigned yet. Our Nigerian business specialists 
              will help you navigate local business culture and build strong relationships.
            </p>
            <Button onClick={onRequestAssignment} disabled={isLoading}>
              {isLoading ? 'Assigning...' : 'Request Relationship Manager'}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <RelationshipManagerCard
        manager={clientAssignment.relationship_manager}
        assignment={clientAssignment}
        onScheduleMeeting={handleScheduleMeeting}
        onLogInteraction={handleLogInteraction}
      />

      {/* Recent Interactions */}
      {recentInteractions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Interactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentInteractions.slice(0, 5).map((interaction) => (
                <div key={interaction.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 rounded-full bg-blue-500" />
                    <div>
                      <p className="font-medium text-sm">{interaction.interaction_subject}</p>
                      <p className="text-xs text-gray-600">
                        {new Date(interaction.interaction_date).toLocaleDateString()} • 
                        {interaction.duration_minutes ? ` ${interaction.duration_minutes} min` : ''} • 
                        {interaction.interaction_type}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant={interaction.interaction_outcome === 'positive' ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {interaction.interaction_outcome}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RelationshipManagerSystem;