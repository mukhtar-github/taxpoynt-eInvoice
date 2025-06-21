import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Lock, 
  Eye, 
  Server, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  Globe,
  Database,
  Key,
  FileCheck,
  Activity
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';

interface SecurityIndicatorsProps {
  showRealTimeStatus?: boolean;
  showSecurityMetrics?: boolean;
  showUptime?: boolean;
  animated?: boolean;
  layout?: 'compact' | 'detailed' | 'banner';
}

const SecurityIndicators: React.FC<SecurityIndicatorsProps> = ({
  showRealTimeStatus = true,
  showSecurityMetrics = true,
  showUptime = true,
  animated = true,
  layout = 'detailed'
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [systemStatus, setSystemStatus] = useState('operational');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const securityFeatures = [
    {
      id: 'encryption',
      name: 'End-to-End Encryption',
      description: 'AES-256 encryption for all data transmission and storage',
      icon: <Lock className="h-6 w-6 text-green-600" />,
      status: 'active',
      level: 'Enterprise Grade'
    },
    {
      id: 'authentication',
      name: 'Multi-Factor Authentication',
      description: 'Advanced MFA with biometric and hardware key support',
      icon: <Key className="h-6 w-6 text-blue-600" />,
      status: 'active',
      level: 'Required'
    },
    {
      id: 'monitoring',
      name: '24/7 Security Monitoring',
      description: 'Real-time threat detection and incident response',
      icon: <Eye className="h-6 w-6 text-purple-600" />,
      status: 'active',
      level: 'Continuous'
    },
    {
      id: 'backup',
      name: 'Automated Backups',
      description: 'Multi-region backup with 99.99% data durability',
      icon: <Database className="h-6 w-6 text-orange-600" />,
      status: 'active',
      level: 'Daily'
    }
  ];

  const trustMetrics = [
    {
      label: 'System Uptime',
      value: '99.99%',
      period: 'Last 12 months',
      icon: <Activity className="h-5 w-5 text-green-500" />,
      color: 'green'
    },
    {
      label: 'Security Incidents',
      value: '0',
      period: 'This year',
      icon: <Shield className="h-5 w-5 text-blue-500" />,
      color: 'blue'
    },
    {
      label: 'Data Centers',
      value: '3',
      period: 'Global locations',
      icon: <Server className="h-5 w-5 text-purple-500" />,
      color: 'purple'
    },
    {
      label: 'Compliance Audits',
      value: '100%',
      period: 'Pass rate',
      icon: <FileCheck className="h-5 w-5 text-cyan-500" />,
      color: 'cyan'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'text-green-600 bg-green-100';
      case 'maintenance':
        return 'text-yellow-600 bg-yellow-100';
      case 'degraded':
        return 'text-orange-600 bg-orange-100';
      case 'outage':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'maintenance':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-orange-600" />;
      case 'outage':
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default:
        return <CheckCircle className="h-5 w-5 text-gray-600" />;
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  if (layout === 'banner') {
    return (
      <motion.div
        initial={animated ? { opacity: 0, y: -20 } : {}}
        animate={animated ? { opacity: 1, y: 0 } : {}}
        className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon(systemStatus)}
              <Typography.Text className="font-semibold text-gray-900">
                All Systems Operational
              </Typography.Text>
            </div>
            <div className="hidden md:flex items-center space-x-4 text-sm text-gray-600">
              <span className="flex items-center space-x-1">
                <Lock className="h-4 w-4" />
                <span>SSL Secured</span>
              </span>
              <span className="flex items-center space-x-1">
                <Shield className="h-4 w-4" />
                <span>FIRS Certified</span>
              </span>
              <span className="flex items-center space-x-1">
                <Globe className="h-4 w-4" />
                <span>99.99% Uptime</span>
              </span>
            </div>
          </div>
          <Typography.Text className="text-xs text-gray-500">
            Last updated: {currentTime.toLocaleTimeString()}
          </Typography.Text>
        </div>
      </motion.div>
    );
  }

  if (layout === 'compact') {
    return (
      <motion.div
        variants={animated ? containerVariants : {}}
        initial={animated ? "hidden" : ""}
        animate={animated ? "visible" : ""}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {trustMetrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            variants={animated ? itemVariants : {}}
            whileHover={animated ? { scale: 1.02 } : {}}
          >
            <Card className="p-4 text-center bg-white shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-0">
                <div className="flex justify-center mb-2">
                  {metric.icon}
                </div>
                <Typography.Text className="text-2xl font-bold text-gray-900">
                  {metric.value}
                </Typography.Text>
                <Typography.Text className="text-sm text-gray-600">
                  {metric.label}
                </Typography.Text>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    );
  }

  // Default detailed layout
  return (
    <div className="space-y-8">
      {/* Real-time Status */}
      {showRealTimeStatus && (
        <div>
          <div className="text-center mb-6">
            <Typography.Heading level="h3" className="text-lg font-bold text-gray-900 mb-2">
              Real-Time Security Status
            </Typography.Heading>
            <Typography.Text className="text-gray-600">
              Live monitoring of all security systems and infrastructure
            </Typography.Text>
          </div>

          <motion.div
            initial={animated ? { opacity: 0, scale: 0.95 } : {}}
            animate={animated ? { opacity: 1, scale: 1 } : {}}
            className="bg-white rounded-lg border shadow-sm"
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(systemStatus)}
                  <div>
                    <Typography.Text className="font-semibold text-gray-900">
                      System Status: Operational
                    </Typography.Text>
                    <Typography.Text className="text-sm text-gray-500">
                      All services running normally
                    </Typography.Text>
                  </div>
                </div>
                <div className="text-right">
                  <Typography.Text className="text-sm text-gray-500">
                    Last checked
                  </Typography.Text>
                  <Typography.Text className="font-mono text-sm text-gray-900">
                    {currentTime.toLocaleTimeString()}
                  </Typography.Text>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {securityFeatures.map((feature) => (
                  <motion.div
                    key={feature.id}
                    whileHover={animated ? { x: 5 } : {}}
                    className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      {feature.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <Typography.Text className="font-medium text-gray-900">
                          {feature.name}
                        </Typography.Text>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(feature.status)}`}>
                          {feature.level}
                        </span>
                      </div>
                      <Typography.Text className="text-sm text-gray-600 mt-1">
                        {feature.description}
                      </Typography.Text>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Security Metrics */}
      {showSecurityMetrics && (
        <div>
          <div className="text-center mb-6">
            <Typography.Heading level="h3" className="text-lg font-bold text-gray-900 mb-2">
              Trust & Reliability Metrics
            </Typography.Heading>
            <Typography.Text className="text-gray-600">
              Transparent performance and security statistics
            </Typography.Text>
          </div>

          <motion.div
            variants={animated ? containerVariants : {}}
            initial={animated ? "hidden" : ""}
            animate={animated ? "visible" : ""}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            {trustMetrics.map((metric, index) => (
              <motion.div
                key={metric.label}
                variants={animated ? itemVariants : {}}
                whileHover={animated ? { y: -5, scale: 1.02 } : {}}
                transition={{ duration: 0.2 }}
              >
                <Card className="p-6 text-center bg-white shadow-sm hover:shadow-md transition-all">
                  <CardContent className="p-0">
                    <div className="flex justify-center mb-3">
                      {metric.icon}
                    </div>
                    <Typography.Text className="text-3xl font-bold text-gray-900 mb-2">
                      {metric.value}
                    </Typography.Text>
                    <Typography.Text className="font-medium text-gray-900 mb-1">
                      {metric.label}
                    </Typography.Text>
                    <Typography.Text className="text-sm text-gray-500">
                      {metric.period}
                    </Typography.Text>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      )}

      {/* Uptime Display */}
      {showUptime && (
        <div>
          <div className="text-center mb-6">
            <Typography.Heading level="h3" className="text-lg font-bold text-gray-900 mb-2">
              Service Availability
            </Typography.Heading>
            <Typography.Text className="text-gray-600">
              Historical uptime and performance data
            </Typography.Text>
          </div>

          <motion.div
            initial={animated ? { opacity: 0, y: 20 } : {}}
            animate={animated ? { opacity: 1, y: 0 } : {}}
            className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 border border-green-200"
          >
            <div className="text-center">
              <div className="inline-flex items-center space-x-2 mb-4">
                <Activity className="h-8 w-8 text-green-600" />
                <Typography.Text className="text-4xl font-bold text-green-600">
                  99.99%
                </Typography.Text>
              </div>
              <Typography.Text className="text-lg font-semibold text-gray-900 mb-2">
                Uptime Over Last 12 Months
              </Typography.Text>
              <Typography.Text className="text-gray-600">
                Consistently reliable service with minimal downtime
              </Typography.Text>
              
              <div className="mt-6 grid grid-cols-3 gap-4 text-center">
                <div>
                  <Typography.Text className="text-2xl font-bold text-gray-900">
                    &lt; 1min
                  </Typography.Text>
                  <Typography.Text className="text-sm text-gray-600">
                    Average Response Time
                  </Typography.Text>
                </div>
                <div>
                  <Typography.Text className="text-2xl font-bold text-gray-900">
                    99.5%
                  </Typography.Text>
                  <Typography.Text className="text-sm text-gray-600">
                    API Success Rate
                  </Typography.Text>
                </div>
                <div>
                  <Typography.Text className="text-2xl font-bold text-gray-900">
                    24/7
                  </Typography.Text>
                  <Typography.Text className="text-sm text-gray-600">
                    Monitoring Coverage
                  </Typography.Text>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default SecurityIndicators;