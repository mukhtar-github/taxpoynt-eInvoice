import React from 'react';
import { useLocalization } from '../../context/LocalizationContext';
import { Button } from '../ui/Button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { Globe, ChevronDown } from 'lucide-react';

interface LanguageSwitcherProps {
  variant?: 'dropdown' | 'compact' | 'full';
  showFlag?: boolean;
  showGreeting?: boolean;
  className?: string;
}

const LANGUAGE_FLAGS = {
  'en-NG': '🇬🇧',
  'ha-NG': '🇳🇬',
  'yo-NG': '🇳🇬',
  'ig-NG': '🇳🇬'
};

const LANGUAGE_GREETINGS = {
  'en-NG': 'Hello',
  'ha-NG': 'Sannu',
  'yo-NG': 'Bawo',
  'ig-NG': 'Ndewo'
};

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({ 
  variant = 'dropdown', 
  showFlag = true, 
  showGreeting = false,
  className = '' 
}) => {
  const { currentLanguage, changeLanguage, supportedLanguages, languageConfig } = useLocalization();

  if (variant === 'compact') {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Globe className="w-4 h-4 text-gray-600" />
        <Select value={currentLanguage} onValueChange={changeLanguage}>
          <SelectTrigger className="w-auto min-w-0 border-none shadow-none p-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {supportedLanguages.map(lang => (
              <SelectItem key={lang.code} value={lang.code}>
                <div className="flex items-center space-x-2">
                  {showFlag && <span>{LANGUAGE_FLAGS[lang.code as keyof typeof LANGUAGE_FLAGS]}</span>}
                  <span className="text-sm">{lang.code.split('-')[0].toUpperCase()}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    );
  }

  if (variant === 'full') {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center space-x-2 mb-3">
          <Globe className="w-5 h-5 text-blue-600" />
          <h3 className="font-medium">Language / Harshe / Ede / Asụsụ</h3>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          {supportedLanguages.map(lang => {
            const isActive = currentLanguage === lang.code;
            const flag = LANGUAGE_FLAGS[lang.code as keyof typeof LANGUAGE_FLAGS];
            const greeting = LANGUAGE_GREETINGS[lang.code as keyof typeof LANGUAGE_GREETINGS];
            
            return (
              <Button
                key={lang.code}
                variant={isActive ? "default" : "outline"}
                onClick={() => changeLanguage(lang.code)}
                className={`h-auto p-4 justify-start ${isActive ? 'ring-2 ring-blue-500' : ''}`}
              >
                <div className="flex items-center space-x-3 w-full">
                  {showFlag && <span className="text-2xl">{flag}</span>}
                  <div className="text-left">
                    <div className="font-medium">{lang.name}</div>
                    {showGreeting && (
                      <div className="text-sm opacity-70">{greeting}</div>
                    )}
                  </div>
                  {isActive && (
                    <Badge variant="default" className="ml-auto">
                      Active
                    </Badge>
                  )}
                </div>
              </Button>
            );
          })}
        </div>
        
        {showGreeting && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-sm text-blue-800">
              <strong>Current greeting:</strong> {languageConfig.greetings.formal}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Default dropdown variant
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <Globe className="w-4 h-4 text-gray-600" />
      <Select value={currentLanguage} onValueChange={changeLanguage}>
        <SelectTrigger className="w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {supportedLanguages.map(lang => {
            const flag = LANGUAGE_FLAGS[lang.code as keyof typeof LANGUAGE_FLAGS];
            const greeting = LANGUAGE_GREETINGS[lang.code as keyof typeof LANGUAGE_GREETINGS];
            
            return (
              <SelectItem key={lang.code} value={lang.code}>
                <div className="flex items-center space-x-3 w-full">
                  {showFlag && <span>{flag}</span>}
                  <div className="flex-1">
                    <div className="font-medium">{lang.name}</div>
                    {showGreeting && (
                      <div className="text-sm text-gray-500">({greeting})</div>
                    )}
                  </div>
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
};

// Mobile-optimized language switcher
export const MobileLanguageSwitcher: React.FC = () => {
  const { currentLanguage, changeLanguage, supportedLanguages } = useLocalization();
  
  return (
    <div className="flex items-center justify-between p-4 bg-white border-b">
      <div className="flex items-center space-x-2">
        <Globe className="w-5 h-5 text-gray-600" />
        <span className="font-medium">Language</span>
      </div>
      
      <div className="flex space-x-1">
        {supportedLanguages.map(lang => {
          const isActive = currentLanguage === lang.code;
          const flag = LANGUAGE_FLAGS[lang.code as keyof typeof LANGUAGE_FLAGS];
          
          return (
            <Button
              key={lang.code}
              variant={isActive ? "default" : "ghost"}
              size="sm"
              onClick={() => changeLanguage(lang.code)}
              className="px-2 py-1"
            >
              <span className="mr-1">{flag}</span>
              <span className="text-xs">{lang.code.split('-')[0].toUpperCase()}</span>
            </Button>
          );
        })}
      </div>
    </div>
  );
};

// Language switcher for navigation bars
export const NavLanguageSwitcher: React.FC = () => {
  const { currentLanguage, changeLanguage, supportedLanguages } = useLocalization();
  const currentLang = supportedLanguages.find(lang => lang.code === currentLanguage);
  const flag = LANGUAGE_FLAGS[currentLanguage as keyof typeof LANGUAGE_FLAGS];
  
  return (
    <div className="relative">
      <Select value={currentLanguage} onValueChange={changeLanguage}>
        <SelectTrigger className="w-auto border-none shadow-none bg-transparent hover:bg-gray-100 px-2 py-1">
          <div className="flex items-center space-x-1">
            <span>{flag}</span>
            <span className="text-sm">{currentLang?.code.split('-')[0].toUpperCase()}</span>
            <ChevronDown className="w-3 h-3" />
          </div>
        </SelectTrigger>
        <SelectContent align="end">
          {supportedLanguages.map(lang => {
            const langFlag = LANGUAGE_FLAGS[lang.code as keyof typeof LANGUAGE_FLAGS];
            const greeting = LANGUAGE_GREETINGS[lang.code as keyof typeof LANGUAGE_GREETINGS];
            
            return (
              <SelectItem key={lang.code} value={lang.code}>
                <div className="flex items-center space-x-2">
                  <span>{langFlag}</span>
                  <span>{lang.name}</span>
                  <span className="text-xs text-gray-500">({greeting})</span>
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
};

export default LanguageSwitcher;