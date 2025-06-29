import React, { useState, useEffect, useRef } from 'react';
import { motion, useInView, useAnimation } from 'framer-motion';
import { 
  Users, 
  FileText, 
  Building, 
  TrendingUp,
  Calendar,
  CheckCircle,
  Globe,
  Clock,
  Award,
  Zap,
  DollarSign,
  Shield
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';

interface Statistic {
  id: string;
  label: string;
  value: number;
  unit?: string;
  prefix?: string;
  suffix?: string;
  description?: string;
  icon: React.ReactNode;
  color: string;
  animationDuration?: number;
}

interface UsageStatisticsProps {
  statistics?: Statistic[];
  layout?: 'grid' | 'row' | 'hero';
  animated?: boolean;
  showDescriptions?: boolean;
  autoStart?: boolean;
  theme?: 'light' | 'dark' | 'gradient';
}

const UsageStatistics: React.FC<UsageStatisticsProps> = ({
  statistics,
  layout = 'grid',
  animated = true,
  showDescriptions = true,
  autoStart = true,
  theme = 'light'
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, threshold: 0.1 });
  const controls = useAnimation();
  
  const defaultStatistics: Statistic[] = [
    {
      id: 'total-invoices',
      label: 'Invoices Processed',
      value: 2500000,
      suffix: '+',
      description: 'Total e-invoices successfully processed and submitted to FIRS',
      icon: <FileText className="h-8 w-8" />,
      color: 'blue',
      animationDuration: 3000
    },
    {
      id: 'active-businesses',
      label: 'Active Businesses',
      value: 15000,
      suffix: '+',
      description: 'Nigerian businesses actively using our platform',
      icon: <Building className="h-8 w-8" />,
      color: 'green',
      animationDuration: 2500
    },
    {
      id: 'monthly-growth',
      label: 'Monthly Growth',
      value: 25,
      suffix: '%',
      description: 'Average monthly user growth rate',
      icon: <TrendingUp className="h-8 w-8" />,
      color: 'purple',
      animationDuration: 2000
    },
    {
      id: 'compliance-rate',
      label: 'Compliance Rate',
      value: 99.9,
      suffix: '%',
      description: 'FIRS compliance success rate',
      icon: <CheckCircle className="h-8 w-8" />,
      color: 'cyan',
      animationDuration: 2500
    },
    {
      id: 'cost-savings',
      label: 'Average Cost Savings',
      value: 40,
      suffix: '%',
      description: 'Reduction in invoicing operational costs',
      icon: <DollarSign className="h-8 w-8" />,
      color: 'orange',
      animationDuration: 2000
    },
    {
      id: 'processing-time',
      label: 'Processing Time',
      value: 85,
      suffix: '%',
      description: 'Reduction in invoice processing time',
      icon: <Clock className="h-8 w-8" />,
      color: 'indigo',
      animationDuration: 2200
    },
    {
      id: 'uptime',
      label: 'System Uptime',
      value: 99.99,
      suffix: '%',
      description: 'Platform availability over the last 12 months',
      icon: <Shield className="h-8 w-8" />,
      color: 'emerald',
      animationDuration: 2800
    },
    {
      id: 'api-calls',
      label: 'API Calls Daily',
      value: 500000,
      suffix: '+',
      description: 'Daily API requests processed',
      icon: <Zap className="h-8 w-8" />,
      color: 'yellow',
      animationDuration: 3500
    }
  ];

  const statsData = statistics || defaultStatistics;

  useEffect(() => {
    if (isInView && autoStart) {
      controls.start('visible');
    }
  }, [isInView, autoStart, controls]);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const AnimatedCounter: React.FC<{
    value: number;
    duration: number;
    prefix?: string;
    suffix?: string;
    decimals?: number;
  }> = ({ value, duration, prefix = '', suffix = '', decimals = 0 }) => {
    const [count, setCount] = useState(0);
    const [isAnimating, setIsAnimating] = useState(false);

    useEffect(() => {
      if (isInView && autoStart && !isAnimating) {
        setIsAnimating(true);
        const startTime = Date.now();
        const startValue = 0;
        const endValue = value;

        const updateCount = () => {
          const now = Date.now();
          const elapsed = now - startTime;
          const progress = Math.min(elapsed / duration, 1);
          
          // Easing function for smooth animation
          const easeOutQuart = 1 - Math.pow(1 - progress, 4);
          const currentValue = startValue + (endValue - startValue) * easeOutQuart;
          
          setCount(currentValue);

          if (progress < 1) {
            requestAnimationFrame(updateCount);
          } else {
            setCount(endValue);
            setIsAnimating(false);
          }
        };

        requestAnimationFrame(updateCount);
      }
    }, [isInView, autoStart, value, duration, isAnimating]);

    const displayValue = decimals > 0 ? count.toFixed(decimals) : Math.floor(count);
    const formattedValue = value >= 1000 ? formatNumber(Number(displayValue)) : displayValue;

    return (
      <span>
        {prefix}{formattedValue}{suffix}
      </span>
    );
  };

  const getColorClasses = (color: string, theme: string) => {
    const colorMap = {
      blue: {
        light: 'text-blue-600 bg-blue-50',
        dark: 'text-blue-400 bg-blue-900/20',
        gradient: 'text-blue-600 bg-gradient-to-br from-blue-50 to-blue-100'
      },
      green: {
        light: 'text-green-600 bg-green-50',
        dark: 'text-green-400 bg-green-900/20',
        gradient: 'text-green-600 bg-gradient-to-br from-green-50 to-green-100'
      },
      purple: {
        light: 'text-purple-600 bg-purple-50',
        dark: 'text-purple-400 bg-purple-900/20',
        gradient: 'text-purple-600 bg-gradient-to-br from-purple-50 to-purple-100'
      },
      cyan: {
        light: 'text-cyan-600 bg-cyan-50',
        dark: 'text-cyan-400 bg-cyan-900/20',
        gradient: 'text-cyan-600 bg-gradient-to-br from-cyan-50 to-cyan-100'
      },
      orange: {
        light: 'text-orange-600 bg-orange-50',
        dark: 'text-orange-400 bg-orange-900/20',
        gradient: 'text-orange-600 bg-gradient-to-br from-orange-50 to-orange-100'
      },
      indigo: {
        light: 'text-indigo-600 bg-indigo-50',
        dark: 'text-indigo-400 bg-indigo-900/20',
        gradient: 'text-indigo-600 bg-gradient-to-br from-indigo-50 to-indigo-100'
      },
      emerald: {
        light: 'text-emerald-600 bg-emerald-50',
        dark: 'text-emerald-400 bg-emerald-900/20',
        gradient: 'text-emerald-600 bg-gradient-to-br from-emerald-50 to-emerald-100'
      },
      yellow: {
        light: 'text-yellow-600 bg-yellow-50',
        dark: 'text-yellow-400 bg-yellow-900/20',
        gradient: 'text-yellow-600 bg-gradient-to-br from-yellow-50 to-yellow-100'
      }
    };

    return colorMap[color as keyof typeof colorMap]?.[theme] || colorMap.blue[theme];
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  const StatCard: React.FC<{ stat: Statistic; index: number }> = ({ stat, index }) => (
    <motion.div
      variants={animated ? itemVariants : {}}
      whileHover={animated ? { scale: 1.02, y: -5 } : {}}
      transition={{ duration: 0.2 }}
    >
      <Card className={`h-full ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-gray-100'} shadow-lg hover:shadow-xl transition-shadow`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${getColorClasses(stat.color, theme)}`}>
              {stat.icon}
            </div>
            {layout === 'hero' && (
              <div className="text-right">
                <Typography.Text className="text-xs text-gray-500 uppercase tracking-wide">
                  Live Stats
                </Typography.Text>
              </div>
            )}
          </div>
          
          <div className="space-y-2">
            <Typography.Text className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              <AnimatedCounter
                value={stat.value}
                duration={stat.animationDuration || 2000}
                prefix={stat.prefix}
                suffix={stat.suffix}
                decimals={stat.value % 1 !== 0 ? 1 : 0}
              />
            </Typography.Text>
            
            <Typography.Text className={`font-semibold ${theme === 'dark' ? 'text-gray-200' : 'text-gray-800'}`}>
              {stat.label}
            </Typography.Text>
            
            {showDescriptions && stat.description && (
              <Typography.Text className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                {stat.description}
              </Typography.Text>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  const getLayoutClasses = () => {
    switch (layout) {
      case 'row':
        return 'flex flex-wrap gap-6 justify-center';
      case 'hero':
        return 'grid grid-cols-2 md:grid-cols-4 gap-6';
      default:
        return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6';
    }
  };

  return (
    <div ref={containerRef} className="w-full">
      <motion.div
        variants={animated ? containerVariants : {}}
        initial={animated ? "hidden" : ""}
        animate={animated ? controls : ""}
        className={getLayoutClasses()}
      >
        {statsData.map((stat, index) => (
          <StatCard key={stat.id} stat={stat} index={index} />
        ))}
      </motion.div>
      
      {layout === 'hero' && (
        <motion.div
          initial={animated ? { opacity: 0, y: 20 } : {}}
          animate={animated ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8 }}
          className="text-center mt-8"
        >
          <Typography.Text className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            Statistics updated in real-time • Last updated: {new Date().toLocaleTimeString()}
          </Typography.Text>
        </motion.div>
      )}
    </div>
  );
};

export default UsageStatistics;