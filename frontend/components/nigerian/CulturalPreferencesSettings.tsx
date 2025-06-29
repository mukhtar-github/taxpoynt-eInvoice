import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { Separator } from '../ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Globe,
  MessageCircle,
  Users,
  Clock,
  Star,
  Phone,
  Mail,
  Video,
  MapPin,
  Heart,
  Handshake,
  Gift,
  Crown,
  Shield,
  AlertCircle,
  CheckCircle,
  Settings
} from 'lucide-react';

interface CulturalPreferences {
  // Language and Communication
  primary_language: 'english' | 'hausa' | 'yoruba' | 'igbo';
  secondary_languages: string[];
  greeting_style: 'formal' | 'traditional' | 'modern';
  communication_pace: 'relationship_first' | 'business_first';
  
  // Meeting Protocols
  relationship_building_time: number; // minutes
  hierarchy_acknowledgment: boolean;
  gift_exchange_customs: boolean;
  
  // Support Channel Preferences
  whatsapp_business_api: boolean;
  voice_calls: boolean;
  video_calls: boolean;
  in_person_meetings: boolean;
  traditional_email: boolean;
  
  // Cultural Respect Settings
  respect_titles: boolean;
  age_respectful_language: boolean;
  gender_appropriate_language: boolean;
  
  // Regional Preferences
  regional_customs: {
    northern_protocols: boolean;
    southern_protocols: boolean;
    middle_belt_protocols: boolean;
  };
  
  // Religious Considerations
  religious_accommodations: {
    islamic_considerations: boolean;
    christian_considerations: boolean;
    traditional_considerations: boolean;
  };
  
  // Business Relationship Style
  relationship_building_importance: 'low' | 'medium' | 'high';
  decision_making_style: 'individual' | 'consultative' | 'consensus';
  formality_level: 'casual' | 'business' | 'formal';
}

interface CulturalPreferencesSettingsProps {
  organizationId: string;
  currentPreferences?: CulturalPreferences;
  onSave?: (preferences: CulturalPreferences) => void;
  onCancel?: () => void;
}

const LANGUAGE_OPTIONS = [
  { value: 'english', label: 'English', flag: '🇬🇧', greeting: 'Good day' },
  { value: 'hausa', label: 'Hausa', flag: '🇳🇬', greeting: 'Sannu' },
  { value: 'yoruba', label: 'Yoruba', flag: '🇳🇬', greeting: 'E kaaro' },
  { value: 'igbo', label: 'Igbo', flag: '🇳🇬', greeting: 'Ndewo' }
];

const NIGERIAN_TITLES = [
  'Alhaji', 'Alhaja', 'Chief', 'Dr.', 'Prof.', 'Engr.', 'Barr.', 'Otunba', 
  'Oba', 'Emir', 'Sir', 'Dame', 'HRH', 'HRM', 'Malam', 'Mallam'
];

const DEFAULT_PREFERENCES: CulturalPreferences = {
  primary_language: 'english',
  secondary_languages: [],
  greeting_style: 'formal',
  communication_pace: 'relationship_first',
  relationship_building_time: 15,
  hierarchy_acknowledgment: true,
  gift_exchange_customs: false,
  whatsapp_business_api: true,
  voice_calls: true,
  video_calls: false,
  in_person_meetings: true,
  traditional_email: true,
  respect_titles: true,
  age_respectful_language: true,
  gender_appropriate_language: true,
  regional_customs: {
    northern_protocols: false,
    southern_protocols: false,
    middle_belt_protocols: false
  },
  religious_accommodations: {
    islamic_considerations: false,
    christian_considerations: false,
    traditional_considerations: false
  },
  relationship_building_importance: 'high',
  decision_making_style: 'consensus',
  formality_level: 'business'
};

const LanguageSelector: React.FC<{
  value: string;
  onChange: (value: string) => void;
  label: string;
  description?: string;
}> = ({ value, onChange, label, description }) => {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {description && <p className="text-sm text-gray-600">{description}</p>}
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {LANGUAGE_OPTIONS.map(option => (
            <SelectItem key={option.value} value={option.value}>
              <div className="flex items-center space-x-2">
                <span>{option.flag}</span>
                <span>{option.label}</span>
                <span className="text-gray-500 text-sm">({option.greeting})</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};

const SupportChannelSettings: React.FC<{
  preferences: CulturalPreferences;
  onChange: (key: keyof CulturalPreferences, value: boolean) => void;
}> = ({ preferences, onChange }) => {
  const channels = [
    {
      key: 'whatsapp_business_api' as keyof CulturalPreferences,
      icon: <MessageCircle className="w-5 h-5 text-green-600" />,
      title: 'WhatsApp Business',
      description: 'Primary communication channel in Nigeria',
      popularity: 95
    },
    {
      key: 'voice_calls' as keyof CulturalPreferences,
      icon: <Phone className="w-5 h-5 text-blue-600" />,
      title: 'Voice Calls',
      description: 'Direct phone conversations for important matters',
      popularity: 90
    },
    {
      key: 'in_person_meetings' as keyof CulturalPreferences,
      icon: <Users className="w-5 h-5 text-purple-600" />,
      title: 'In-Person Meetings',
      description: 'Face-to-face meetings for relationship building',
      popularity: 85
    },
    {
      key: 'traditional_email' as keyof CulturalPreferences,
      icon: <Mail className="w-5 h-5 text-gray-600" />,
      title: 'Email',
      description: 'Formal communication and documentation',
      popularity: 70
    },
    {
      key: 'video_calls' as keyof CulturalPreferences,
      icon: <Video className="w-5 h-5 text-indigo-600" />,
      title: 'Video Calls',
      description: 'Remote face-to-face communication',
      popularity: 40
    }
  ];

  return (
    <div className="space-y-4">
      {channels.map(channel => (
        <div key={channel.key} className="flex items-center justify-between p-4 border rounded-lg">
          <div className="flex items-center space-x-3">
            {channel.icon}
            <div>
              <h4 className="font-medium">{channel.title}</h4>
              <p className="text-sm text-gray-600">{channel.description}</p>
              <div className="flex items-center space-x-2 mt-1">
                <div className="w-20 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${channel.popularity}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">{channel.popularity}% popular</span>
              </div>
            </div>
          </div>
          <Switch
            checked={preferences[channel.key] as boolean}
            onCheckedChange={(checked) => onChange(channel.key, checked)}
          />
        </div>
      ))}
    </div>
  );
};

const MeetingProtocolSettings: React.FC<{
  preferences: CulturalPreferences;
  onChange: (updates: Partial<CulturalPreferences>) => void;
}> = ({ preferences, onChange }) => {
  return (
    <div className="space-y-6">
      {/* Relationship Building Time */}
      <div className="space-y-2">
        <Label>Relationship Building Time (minutes)</Label>
        <p className="text-sm text-gray-600">
          Time allocated for relationship building at the start of meetings
        </p>
        <div className="flex items-center space-x-4">
          <Input
            type="number"
            min="0"
            max="60"
            value={preferences.relationship_building_time}
            onChange={(e) => onChange({ relationship_building_time: parseInt(e.target.value) || 0 })}
            className="w-24"
          />
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${(preferences.relationship_building_time / 60) * 100}%` }}
            />
          </div>
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>No time</span>
          <span>1 hour</span>
        </div>
      </div>

      {/* Hierarchy Acknowledgment */}
      <div className="flex items-center justify-between p-4 border rounded-lg">
        <div className="flex items-center space-x-3">
          <Crown className="w-5 h-5 text-yellow-600" />
          <div>
            <h4 className="font-medium">Hierarchy Acknowledgment</h4>
            <p className="text-sm text-gray-600">
              Recognize and respect traditional Nigerian corporate hierarchy
            </p>
          </div>
        </div>
        <Switch
          checked={preferences.hierarchy_acknowledgment}
          onCheckedChange={(checked) => onChange({ hierarchy_acknowledgment: checked })}
        />
      </div>

      {/* Gift Exchange Customs */}
      <div className="flex items-center justify-between p-4 border rounded-lg">
        <div className="flex items-center space-x-3">
          <Gift className="w-5 h-5 text-pink-600" />
          <div>
            <h4 className="font-medium">Gift Exchange Customs</h4>
            <p className="text-sm text-gray-600">
              Include traditional gift exchange in business relationships
            </p>
          </div>
        </div>
        <Switch
          checked={preferences.gift_exchange_customs}
          onCheckedChange={(checked) => onChange({ gift_exchange_customs: checked })}
        />
      </div>

      {/* Greeting Style */}
      <div className="space-y-2">
        <Label>Greeting Style</Label>
        <Select 
          value={preferences.greeting_style} 
          onValueChange={(value) => onChange({ greeting_style: value as any })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="formal">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4" />
                <span>Formal - "Good morning, Sir/Madam"</span>
              </div>
            </SelectItem>
            <SelectItem value="traditional">
              <div className="flex items-center space-x-2">
                <Crown className="w-4 h-4" />
                <span>Traditional - Local language greetings</span>
              </div>
            </SelectItem>
            <SelectItem value="modern">
              <div className="flex items-center space-x-2">
                <Star className="w-4 h-4" />
                <span>Modern - "Hi" or "Hello"</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Communication Pace */}
      <div className="space-y-2">
        <Label>Communication Pace</Label>
        <Select 
          value={preferences.communication_pace} 
          onValueChange={(value) => onChange({ communication_pace: value as any })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="relationship_first">
              <div className="flex items-center space-x-2">
                <Heart className="w-4 h-4" />
                <span>Relationship First - Build rapport before business</span>
              </div>
            </SelectItem>
            <SelectItem value="business_first">
              <div className="flex items-center space-x-2">
                <Settings className="w-4 h-4" />
                <span>Business First - Direct to business matters</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
};

const RegionalAndReligiousSettings: React.FC<{
  preferences: CulturalPreferences;
  onChange: (updates: Partial<CulturalPreferences>) => void;
}> = ({ preferences, onChange }) => {
  const updateRegionalCustoms = (key: keyof CulturalPreferences['regional_customs'], value: boolean) => {
    onChange({
      regional_customs: {
        ...preferences.regional_customs,
        [key]: value
      }
    });
  };

  const updateReligiousAccommodations = (key: keyof CulturalPreferences['religious_accommodations'], value: boolean) => {
    onChange({
      religious_accommodations: {
        ...preferences.religious_accommodations,
        [key]: value
      }
    });
  };

  return (
    <div className="space-y-6">
      {/* Regional Customs */}
      <div>
        <h3 className="font-medium mb-4 flex items-center space-x-2">
          <MapPin className="w-5 h-5" />
          <span>Regional Protocol Preferences</span>
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <h4 className="font-medium">Northern Nigeria Protocols</h4>
              <p className="text-sm text-gray-600">Traditional respect for elders, Islamic customs</p>
            </div>
            <Switch
              checked={preferences.regional_customs.northern_protocols}
              onCheckedChange={(checked) => updateRegionalCustoms('northern_protocols', checked)}
            />
          </div>
          
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <h4 className="font-medium">Southern Nigeria Protocols</h4>
              <p className="text-sm text-gray-600">Extended greetings, community consultation</p>
            </div>
            <Switch
              checked={preferences.regional_customs.southern_protocols}
              onCheckedChange={(checked) => updateRegionalCustoms('southern_protocols', checked)}
            />
          </div>
          
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <h4 className="font-medium">Middle Belt Protocols</h4>
              <p className="text-sm text-gray-600">Multi-cultural sensitivity, inclusive practices</p>
            </div>
            <Switch
              checked={preferences.regional_customs.middle_belt_protocols}
              onCheckedChange={(checked) => updateRegionalCustoms('middle_belt_protocols', checked)}
            />
          </div>
        </div>
      </div>

      {/* Religious Accommodations */}
      <div>
        <h3 className="font-medium mb-4 flex items-center space-x-2">
          <Shield className="w-5 h-5" />
          <span>Religious Accommodations</span>
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <h4 className="font-medium">Islamic Considerations</h4>
              <p className="text-sm text-gray-600">Prayer times, Halal requirements, Islamic calendar</p>
            </div>
            <Switch
              checked={preferences.religious_accommodations.islamic_considerations}
              onCheckedChange={(checked) => updateReligiousAccommodations('islamic_considerations', checked)}
            />
          </div>
          
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <h4 className="font-medium">Christian Considerations</h4>
              <p className="text-sm text-gray-600">Sunday schedules, Christian holidays</p>
            </div>
            <Switch
              checked={preferences.religious_accommodations.christian_considerations}
              onCheckedChange={(checked) => updateReligiousAccommodations('christian_considerations', checked)}
            />
          </div>
          
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <h4 className="font-medium">Traditional Considerations</h4>
              <p className="text-sm text-gray-600">Traditional festivals, ancestral customs</p>
            </div>
            <Switch
              checked={preferences.religious_accommodations.traditional_considerations}
              onCheckedChange={(checked) => updateReligiousAccommodations('traditional_considerations', checked)}
            />
          </div>
        </div>
      </div>

      {/* Business Relationship Style */}
      <div className="space-y-4">
        <h3 className="font-medium flex items-center space-x-2">
          <Handshake className="w-5 h-5" />
          <span>Business Relationship Style</span>
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Relationship Building Importance</Label>
            <Select 
              value={preferences.relationship_building_importance} 
              onValueChange={(value) => onChange({ relationship_building_importance: value as any })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low - Focus on efficiency</SelectItem>
                <SelectItem value="medium">Medium - Balanced approach</SelectItem>
                <SelectItem value="high">High - Relationship paramount</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label>Decision Making Style</Label>
            <Select 
              value={preferences.decision_making_style} 
              onValueChange={(value) => onChange({ decision_making_style: value as any })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="individual">Individual - Quick decisions</SelectItem>
                <SelectItem value="consultative">Consultative - Seek input</SelectItem>
                <SelectItem value="consensus">Consensus - Group agreement</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label>Formality Level</Label>
            <Select 
              value={preferences.formality_level} 
              onValueChange={(value) => onChange({ formality_level: value as any })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="casual">Casual - Relaxed atmosphere</SelectItem>
                <SelectItem value="business">Business - Professional tone</SelectItem>
                <SelectItem value="formal">Formal - Strict protocols</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  );
};

const PreferencesPreview: React.FC<{
  preferences: CulturalPreferences;
}> = ({ preferences }) => {
  const primaryLang = LANGUAGE_OPTIONS.find(lang => lang.value === preferences.primary_language);
  
  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span>Cultural Preferences Summary</span>
        </CardTitle>
        <CardDescription>
          How these settings will affect your business interactions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-2">Communication Style</h4>
            <div className="space-y-1 text-sm">
              <p>• Primary Language: {primaryLang?.label} ({primaryLang?.greeting})</p>
              <p>• Greeting: {preferences.greeting_style} style</p>
              <p>• Pace: {preferences.communication_pace.replace('_', ' ')}</p>
              <p>• Relationship Building: {preferences.relationship_building_time} minutes</p>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium mb-2">Business Approach</h4>
            <div className="space-y-1 text-sm">
              <p>• Hierarchy Respect: {preferences.hierarchy_acknowledgment ? 'Yes' : 'No'}</p>
              <p>• Decision Style: {preferences.decision_making_style}</p>
              <p>• Formality: {preferences.formality_level}</p>
              <p>• Gift Exchange: {preferences.gift_exchange_customs ? 'Yes' : 'No'}</p>
            </div>
          </div>
        </div>
        
        <Separator />
        
        <div>
          <h4 className="font-medium mb-2">Preferred Support Channels</h4>
          <div className="flex flex-wrap gap-2">
            {preferences.whatsapp_business_api && <Badge variant="secondary">WhatsApp</Badge>}
            {preferences.voice_calls && <Badge variant="secondary">Voice Calls</Badge>}
            {preferences.video_calls && <Badge variant="secondary">Video Calls</Badge>}
            {preferences.in_person_meetings && <Badge variant="secondary">In-Person</Badge>}
            {preferences.traditional_email && <Badge variant="secondary">Email</Badge>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export const CulturalPreferencesSettings: React.FC<CulturalPreferencesSettingsProps> = ({
  organizationId,
  currentPreferences,
  onSave,
  onCancel
}) => {
  const [preferences, setPreferences] = useState<CulturalPreferences>(
    currentPreferences || DEFAULT_PREFERENCES
  );
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('communication');

  const updatePreferences = (updates: Partial<CulturalPreferences>) => {
    setPreferences(prev => ({ ...prev, ...updates }));
  };

  const updatePreference = (key: keyof CulturalPreferences, value: any) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await onSave?.(preferences);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold">Nigerian Cultural Preferences</h1>
        <p className="text-gray-600">
          Configure how you prefer to interact within Nigerian business culture
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="communication">Communication</TabsTrigger>
          <TabsTrigger value="meetings">Meetings</TabsTrigger>
          <TabsTrigger value="support">Support</TabsTrigger>
          <TabsTrigger value="regional">Regional</TabsTrigger>
        </TabsList>

        <TabsContent value="communication" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Globe className="w-5 h-5" />
                <span>Language & Communication</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <LanguageSelector
                value={preferences.primary_language}
                onChange={(value) => updatePreference('primary_language', value)}
                label="Primary Language"
                description="Your preferred language for business communication"
              />
              
              <div className="space-y-2">
                <Label>Secondary Languages</Label>
                <p className="text-sm text-gray-600">Other languages you're comfortable with</p>
                <div className="flex flex-wrap gap-2">
                  {LANGUAGE_OPTIONS.filter(lang => lang.value !== preferences.primary_language).map(lang => (
                    <Badge
                      key={lang.value}
                      variant={preferences.secondary_languages.includes(lang.value) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        const isSelected = preferences.secondary_languages.includes(lang.value);
                        const newSecondary = isSelected
                          ? preferences.secondary_languages.filter(l => l !== lang.value)
                          : [...preferences.secondary_languages, lang.value];
                        updatePreference('secondary_languages', newSecondary);
                      }}
                    >
                      {lang.flag} {lang.label}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Respect Settings */}
              <div className="space-y-4">
                <h3 className="font-medium">Cultural Respect Settings</h3>
                
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <h4 className="font-medium">Respect Traditional Titles</h4>
                    <p className="text-sm text-gray-600">
                      Use titles like {NIGERIAN_TITLES.slice(0, 5).join(', ')}, etc.
                    </p>
                  </div>
                  <Switch
                    checked={preferences.respect_titles}
                    onCheckedChange={(checked) => updatePreference('respect_titles', checked)}
                  />
                </div>
                
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <h4 className="font-medium">Age-Respectful Language</h4>
                    <p className="text-sm text-gray-600">Use appropriate language based on age and seniority</p>
                  </div>
                  <Switch
                    checked={preferences.age_respectful_language}
                    onCheckedChange={(checked) => updatePreference('age_respectful_language', checked)}
                  />
                </div>
                
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <h4 className="font-medium">Gender-Appropriate Language</h4>
                    <p className="text-sm text-gray-600">Use culturally appropriate language for different genders</p>
                  </div>
                  <Switch
                    checked={preferences.gender_appropriate_language}
                    onCheckedChange={(checked) => updatePreference('gender_appropriate_language', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="meetings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="w-5 h-5" />
                <span>Meeting Protocols</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <MeetingProtocolSettings
                preferences={preferences}
                onChange={updatePreferences}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="support" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MessageCircle className="w-5 h-5" />
                <span>Support Channel Preferences</span>
              </CardTitle>
              <CardDescription>
                Choose your preferred methods of communication and support
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SupportChannelSettings
                preferences={preferences}
                onChange={updatePreference}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regional" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MapPin className="w-5 h-5" />
                <span>Regional & Religious Preferences</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RegionalAndReligiousSettings
                preferences={preferences}
                onChange={updatePreferences}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Preview */}
      <PreferencesPreview preferences={preferences} />

      {/* Actions */}
      <div className="flex justify-between pt-6">
        <Button variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save Cultural Preferences'}
        </Button>
      </div>
    </div>
  );
};

export default CulturalPreferencesSettings;