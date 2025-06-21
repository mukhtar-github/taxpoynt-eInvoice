import React from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, 
  ShieldCheck, 
  Award, 
  CheckCircle, 
  Lock,
  FileCheck,
  Star,
  Verified
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';

interface TrustBadgesProps {
  showFIRSBadges?: boolean;
  showSecurityBadges?: boolean;
  showCertifications?: boolean;
  variant?: 'horizontal' | 'grid' | 'inline';
  animated?: boolean;
}

const TrustBadges: React.FC<TrustBadgesProps> = ({
  showFIRSBadges = true,
  showSecurityBadges = true,
  showCertifications = true,
  variant = 'horizontal',
  animated = true
}) => {
  const firsBadges = [
    {
      id: 'firs-certified',
      name: 'FIRS Certified',
      description: 'Officially certified by Federal Inland Revenue Service',
      icon: <ShieldCheck className="h-8 w-8 text-green-600" />,
      color: 'green',
      verified: true
    },
    {
      id: 'app-certified',
      name: 'Access Point Provider',
      description: 'Certified APP for secure e-invoice transmission',
      icon: <Shield className="h-8 w-8 text-cyan-600" />,
      color: 'cyan',
      verified: true
    },
    {
      id: 'si-certified',
      name: 'System Integrator',
      description: 'Certified SI for ERP/CRM/POS integrations',
      icon: <FileCheck className="h-8 w-8 text-blue-600" />,
      color: 'blue',
      verified: true
    }
  ];

  const securityBadges = [
    {
      id: 'ssl-secured',
      name: 'SSL Secured',
      description: 'End-to-end encryption for all data transmission',
      icon: <Lock className="h-6 w-6 text-gray-600" />,
      color: 'gray'
    },
    {
      id: 'iso-compliant',
      name: 'ISO 27001 Compliant',
      description: 'International security management standards',
      icon: <Award className="h-6 w-6 text-purple-600" />,
      color: 'purple'
    },
    {
      id: 'gdpr-compliant',
      name: 'NDPR Compliant',
      description: 'Nigerian Data Protection Regulation compliant',
      icon: <CheckCircle className="h-6 w-6 text-green-600" />,
      color: 'green'
    }
  ];

  const certifications = [
    {
      id: 'pci-dss',
      name: 'PCI DSS',
      level: 'Level 1',
      icon: <Star className="h-5 w-5 text-yellow-500" />
    },
    {
      id: 'soc2',
      name: 'SOC 2 Type II',
      level: 'Certified',
      icon: <Verified className="h-5 w-5 text-blue-500" />
    }
  ];

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

  const BadgeCard = ({ badge, size = 'normal' }: { badge: any; size?: 'small' | 'normal' | 'large' }) => {
    const sizeClasses = {
      small: 'p-3',
      normal: 'p-4',
      large: 'p-6'
    };

    return (
      <motion.div
        variants={animated ? itemVariants : {}}
        whileHover={animated ? { scale: 1.02, y: -2 } : {}}
        transition={{ duration: 0.2 }}
      >
        <Card className={`${sizeClasses[size]} bg-white border shadow-sm hover:shadow-md transition-shadow`}>
          <CardContent className="p-0">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                {badge.icon}
                {badge.verified && (
                  <div className="absolute -top-1 -right-1">
                    <CheckCircle className="h-4 w-4 text-green-500 bg-white rounded-full" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <Typography.Text className="font-semibold text-gray-900 text-sm">
                    {badge.name}
                  </Typography.Text>
                  {badge.level && (
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-${badge.color}-100 text-${badge.color}-800`}>
                      {badge.level}
                    </span>
                  )}
                </div>
                {size !== 'small' && badge.description && (
                  <Typography.Text className="text-xs text-gray-500 mt-1">
                    {badge.description}
                  </Typography.Text>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const InlineBadge = ({ badge }: { badge: any }) => (
    <motion.div
      variants={animated ? itemVariants : {}}
      whileHover={animated ? { scale: 1.05 } : {}}
      className="inline-flex items-center space-x-2 px-3 py-2 bg-white rounded-full shadow-sm border"
    >
      <div className="flex-shrink-0">
        {badge.icon}
      </div>
      <Typography.Text className="font-medium text-gray-900 text-sm">
        {badge.name}
      </Typography.Text>
      {badge.verified && (
        <CheckCircle className="h-4 w-4 text-green-500" />
      )}
    </motion.div>
  );

  if (variant === 'inline') {
    return (
      <motion.div
        variants={animated ? containerVariants : {}}
        initial={animated ? "hidden" : ""}
        animate={animated ? "visible" : ""}
        className="flex flex-wrap gap-3 justify-center"
      >
        {showFIRSBadges && firsBadges.map((badge) => (
          <InlineBadge key={badge.id} badge={badge} />
        ))}
        {showSecurityBadges && securityBadges.slice(0, 2).map((badge) => (
          <InlineBadge key={badge.id} badge={badge} />
        ))}
      </motion.div>
    );
  }

  if (variant === 'grid') {
    return (
      <motion.div
        variants={animated ? containerVariants : {}}
        initial={animated ? "hidden" : ""}
        animate={animated ? "visible" : ""}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        {showFIRSBadges && firsBadges.map((badge) => (
          <BadgeCard key={badge.id} badge={badge} />
        ))}
        {showSecurityBadges && securityBadges.map((badge) => (
          <BadgeCard key={badge.id} badge={badge} />
        ))}
        {showCertifications && certifications.map((cert) => (
          <BadgeCard key={cert.id} badge={cert} size="small" />
        ))}
      </motion.div>
    );
  }

  // Default horizontal layout
  return (
    <div className="space-y-8">
      {/* FIRS Certifications */}
      {showFIRSBadges && (
        <div>
          <div className="text-center mb-6">
            <Typography.Heading level="h3" className="text-lg font-bold text-gray-900 mb-2">
              FIRS Certified Platform
            </Typography.Heading>
            <Typography.Text className="text-gray-600">
              Official certifications from Federal Inland Revenue Service
            </Typography.Text>
          </div>
          <motion.div
            variants={animated ? containerVariants : {}}
            initial={animated ? "hidden" : ""}
            animate={animated ? "visible" : ""}
            className="flex flex-col md:flex-row gap-4 justify-center"
          >
            {firsBadges.map((badge) => (
              <BadgeCard key={badge.id} badge={badge} size="large" />
            ))}
          </motion.div>
        </div>
      )}

      {/* Security & Compliance */}
      {showSecurityBadges && (
        <div>
          <div className="text-center mb-6">
            <Typography.Heading level="h3" className="text-lg font-bold text-gray-900 mb-2">
              Security & Compliance
            </Typography.Heading>
            <Typography.Text className="text-gray-600">
              Enterprise-grade security standards and certifications
            </Typography.Text>
          </div>
          <motion.div
            variants={animated ? containerVariants : {}}
            initial={animated ? "hidden" : ""}
            animate={animated ? "visible" : ""}
            className="flex flex-wrap gap-4 justify-center"
          >
            {securityBadges.map((badge) => (
              <BadgeCard key={badge.id} badge={badge} />
            ))}
          </motion.div>
        </div>
      )}

      {/* Additional Certifications */}
      {showCertifications && (
        <div>
          <div className="text-center mb-4">
            <Typography.Text className="text-gray-600 font-medium">
              Additional Industry Certifications
            </Typography.Text>
          </div>
          <motion.div
            variants={animated ? containerVariants : {}}
            initial={animated ? "hidden" : ""}
            animate={animated ? "visible" : ""}
            className="flex flex-wrap gap-3 justify-center"
          >
            {certifications.map((cert) => (
              <InlineBadge key={cert.id} badge={cert} />
            ))}
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default TrustBadges;