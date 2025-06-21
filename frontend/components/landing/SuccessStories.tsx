import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, 
  Users, 
  Clock, 
  DollarSign,
  Award,
  ChevronRight,
  Building,
  MapPin,
  Calendar,
  ArrowUpRight,
  CheckCircle,
  BarChart3,
  PieChart,
  LineChart
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';

interface SuccessMetric {
  label: string;
  value: string;
  improvement: string;
  icon: React.ReactNode;
}

interface SuccessStory {
  id: string;
  company: string;
  industry: string;
  location: string;
  size: string;
  implementationDate: string;
  challenge: string;
  solution: string;
  results: string;
  quote: string;
  author: {
    name: string;
    title: string;
  };
  metrics: SuccessMetric[];
  featured?: boolean;
  category: 'growth' | 'efficiency' | 'compliance' | 'cost-savings';
}

interface SuccessStoriesProps {
  stories?: SuccessStory[];
  showFilters?: boolean;
  layout?: 'grid' | 'carousel' | 'featured';
  maxStories?: number;
  animated?: boolean;
}

const SuccessStories: React.FC<SuccessStoriesProps> = ({
  stories,
  showFilters = true,
  layout = 'grid',
  maxStories = 6,
  animated = true
}) => {
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [selectedStory, setSelectedStory] = useState<SuccessStory | null>(null);

  const defaultStories: SuccessStory[] = [
    {
      id: '1',
      company: 'Lagos Manufacturing Ltd',
      industry: 'Manufacturing',
      location: 'Lagos, Nigeria',
      size: '500+ employees',
      implementationDate: 'March 2024',
      challenge: 'Manual invoice processing was taking 5-7 days per batch, causing cash flow delays and FIRS compliance issues. The company was spending ₦2M monthly on administrative overhead.',
      solution: 'Implemented TaxPoynt\'s full e-invoicing suite with ERP integration, automated FIRS submission, and real-time compliance monitoring.',
      results: 'Reduced processing time by 85%, achieved 100% FIRS compliance rate, and saved ₦1.5M monthly in operational costs.',
      quote: 'TaxPoynt didn\'t just solve our compliance issues—it transformed our entire financial operations. We\'re processing 10x more invoices with half the staff time.',
      author: {
        name: 'Adebayo Johnson',
        title: 'Chief Financial Officer'
      },
      metrics: [
        {
          label: 'Processing Time',
          value: '2 hours',
          improvement: '85% faster',
          icon: <Clock className="h-5 w-5 text-blue-600" />
        },
        {
          label: 'Cost Savings',
          value: '₦1.5M/month',
          improvement: '75% reduction',
          icon: <DollarSign className="h-5 w-5 text-green-600" />
        },
        {
          label: 'Compliance Rate',
          value: '100%',
          improvement: 'From 60%',
          icon: <CheckCircle className="h-5 w-5 text-cyan-600" />
        }
      ],
      featured: true,
      category: 'efficiency'
    },
    {
      id: '2',
      company: 'Northern Trading Co',
      industry: 'Wholesale Trading',
      location: 'Kano, Nigeria',
      size: '50-200 employees',
      implementationDate: 'January 2024',
      challenge: 'Rapid business growth overwhelmed manual systems. Processing 2,000+ monthly invoices manually led to errors and compliance failures.',
      solution: 'Deployed TaxPoynt\'s scalable platform with automated invoice generation, bulk processing capabilities, and comprehensive audit trails.',
      results: 'Scaled from 2,000 to 15,000 monthly invoices without additional staff. Achieved zero compliance violations and 40% revenue growth.',
      quote: 'TaxPoynt scaled with our explosive growth. What would have required hiring 10 more people was handled seamlessly by the platform.',
      author: {
        name: 'Fatima Al-Hassan',
        title: 'Operations Director'
      },
      metrics: [
        {
          label: 'Invoice Volume',
          value: '15,000/month',
          improvement: '650% increase',
          icon: <TrendingUp className="h-5 w-5 text-purple-600" />
        },
        {
          label: 'Revenue Growth',
          value: '40%',
          improvement: 'YoY increase',
          icon: <BarChart3 className="h-5 w-5 text-orange-600" />
        },
        {
          label: 'Error Rate',
          value: '0.01%',
          improvement: '99% reduction',
          icon: <Award className="h-5 w-5 text-yellow-600" />
        }
      ],
      featured: true,
      category: 'growth'
    },
    {
      id: '3',
      company: 'Port Harcourt Logistics',
      industry: 'Logistics & Transportation',
      location: 'Port Harcourt, Nigeria',
      size: '200-500 employees',
      implementationDate: 'November 2023',
      challenge: 'Complex multi-location operations with inconsistent invoice formats. FIRS audits were becoming increasingly difficult to manage.',
      solution: 'Centralized all locations on TaxPoynt\'s platform with standardized templates, automated compliance checks, and consolidated reporting.',
      results: 'Unified invoice management across 8 locations. Passed FIRS audit with zero issues and reduced compliance costs by 60%.',
      quote: 'Having consistent, compliant invoicing across all our locations has been a game-changer. FIRS audits are no longer a source of stress.',
      author: {
        name: 'Chinedu Okwu',
        title: 'Head of Finance'
      },
      metrics: [
        {
          label: 'Locations Unified',
          value: '8',
          improvement: 'All standardized',
          icon: <Building className="h-5 w-5 text-indigo-600" />
        },
        {
          label: 'Audit Compliance',
          value: '100%',
          improvement: 'Zero issues',
          icon: <CheckCircle className="h-5 w-5 text-green-600" />
        },
        {
          label: 'Compliance Costs',
          value: '60% less',
          improvement: 'Annual savings',
          icon: <DollarSign className="h-5 w-5 text-blue-600" />
        }
      ],
      category: 'compliance'
    },
    {
      id: '4',
      company: 'Abuja Tech Solutions',
      industry: 'Technology Services',
      location: 'Abuja, Nigeria',
      size: '20-50 employees',
      implementationDate: 'February 2024',
      challenge: 'Small team was spending 30% of time on invoice administration. Needed solution that didn\'t require additional staff.',
      solution: 'Implemented TaxPoynt\'s automated workflows with AI-powered data extraction and seamless integration with existing accounting software.',
      results: 'Reduced invoice administration time by 90%. Team now focuses on core business activities, leading to 25% increase in billable hours.',
      quote: 'TaxPoynt gave us our time back. We\'re a small team, and every hour counts. Now we can focus on what we do best—serving our clients.',
      author: {
        name: 'Sarah Adebisi',
        title: 'Managing Director'
      },
      metrics: [
        {
          label: 'Admin Time',
          value: '90% less',
          improvement: 'From 30% to 3%',
          icon: <Clock className="h-5 w-5 text-purple-600" />
        },
        {
          label: 'Billable Hours',
          value: '25% more',
          improvement: 'Revenue increase',
          icon: <TrendingUp className="h-5 w-5 text-green-600" />
        },
        {
          label: 'Setup Time',
          value: '4 hours',
          improvement: 'Same day launch',
          icon: <CheckCircle className="h-5 w-5 text-blue-600" />
        }
      ],
      category: 'efficiency'
    },
    {
      id: '5',
      company: 'Delta Agricultural Co-op',
      industry: 'Agriculture',
      location: 'Warri, Nigeria',
      size: '100-200 employees',
      implementationDate: 'December 2023',
      challenge: 'Seasonal business with complex invoicing needs. Manual processes couldn\'t handle peak season volumes efficiently.',
      solution: 'Deployed TaxPoynt\'s flexible platform with seasonal scaling, batch processing, and customizable invoice templates for different crop types.',
      results: 'Handled 300% volume increase during peak season without hiring additional staff. Improved cash flow by 45% through faster processing.',
      quote: 'Agriculture is seasonal, but compliance isn\'t. TaxPoynt helps us handle our peak seasons professionally while staying compliant year-round.',
      author: {
        name: 'Emmanuel Okafor',
        title: 'General Manager'
      },
      metrics: [
        {
          label: 'Peak Volume',
          value: '300% more',
          improvement: 'Same staff',
          icon: <BarChart3 className="h-5 w-5 text-orange-600" />
        },
        {
          label: 'Cash Flow',
          value: '45% better',
          improvement: 'Faster processing',
          icon: <TrendingUp className="h-5 w-5 text-green-600" />
        },
        {
          label: 'Seasonal Prep',
          value: '1 day',
          improvement: 'From 2 weeks',
          icon: <Calendar className="h-5 w-5 text-blue-600" />
        }
      ],
      category: 'growth'
    },
    {
      id: '6',
      company: 'Kaduna Steel Works',
      industry: 'Manufacturing',
      location: 'Kaduna, Nigeria',
      size: '1000+ employees',
      implementationDate: 'October 2023',
      challenge: 'Enterprise-level complexity with multiple product lines, currencies, and tax jurisdictions. Legacy systems couldn\'t handle FIRS requirements.',
      solution: 'Full enterprise deployment with custom integrations, multi-currency support, and advanced reporting dashboards for different business units.',
      results: 'Streamlined operations across 3 manufacturing facilities. Reduced compliance overhead by 70% and improved reporting accuracy to 99.9%.',
      quote: 'TaxPoynt handled our enterprise complexity without compromising on compliance. The reporting capabilities have transformed our financial visibility.',
      author: {
        name: 'Dr. Ibrahim Yakubu',
        title: 'Chief Financial Officer'
      },
      metrics: [
        {
          label: 'Facilities',
          value: '3',
          improvement: 'Unified system',
          icon: <Building className="h-5 w-5 text-indigo-600" />
        },
        {
          label: 'Compliance Overhead',
          value: '70% less',
          improvement: 'Cost reduction',
          icon: <DollarSign className="h-5 w-5 text-green-600" />
        },
        {
          label: 'Reporting Accuracy',
          value: '99.9%',
          improvement: 'From 85%',
          icon: <PieChart className="h-5 w-5 text-purple-600" />
        }
      ],
      category: 'compliance'
    }
  ];

  const storiesData = stories || defaultStories;
  const filters = [
    { id: 'all', label: 'All Stories', count: storiesData.length },
    { id: 'growth', label: 'Growth', count: storiesData.filter(s => s.category === 'growth').length },
    { id: 'efficiency', label: 'Efficiency', count: storiesData.filter(s => s.category === 'efficiency').length },
    { id: 'compliance', label: 'Compliance', count: storiesData.filter(s => s.category === 'compliance').length },
    { id: 'cost-savings', label: 'Cost Savings', count: storiesData.filter(s => s.category === 'cost-savings').length }
  ];

  const filteredStories = activeFilter === 'all' 
    ? storiesData.slice(0, maxStories)
    : storiesData.filter(story => story.category === activeFilter).slice(0, maxStories);

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

  const StoryCard: React.FC<{ story: SuccessStory; index: number }> = ({ story, index }) => (
    <motion.div
      variants={animated ? itemVariants : {}}
      whileHover={animated ? { y: -5, scale: 1.02 } : {}}
      transition={{ duration: 0.2 }}
      className={story.featured ? 'md:col-span-2' : ''}
    >
      <Card className={`h-full bg-white shadow-lg hover:shadow-xl transition-all cursor-pointer ${
        story.featured ? 'border-l-4 border-l-blue-600' : ''
      }`}>
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Typography.Heading level="h3" className="text-xl font-bold text-gray-900">
                  {story.company}
                </Typography.Heading>
                {story.featured && (
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    Featured
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="flex items-center space-x-1">
                  <Building className="h-4 w-4" />
                  <span>{story.industry}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <MapPin className="h-4 w-4" />
                  <span>{story.location}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Users className="h-4 w-4" />
                  <span>{story.size}</span>
                </span>
              </div>
            </div>
            <ArrowUpRight className="h-5 w-5 text-gray-400" />
          </div>

          <div className="space-y-4">
            <div>
              <Typography.Text className="font-semibold text-gray-900 mb-2">Challenge</Typography.Text>
              <Typography.Text className="text-gray-700 text-sm">
                {story.challenge}
              </Typography.Text>
            </div>

            <div>
              <Typography.Text className="font-semibold text-gray-900 mb-2">Results</Typography.Text>
              <Typography.Text className="text-gray-700 text-sm">
                {story.results}
              </Typography.Text>
            </div>

            <div className="grid grid-cols-3 gap-4 bg-gray-50 rounded-lg p-4">
              {story.metrics.map((metric, metricIndex) => (
                <div key={metricIndex} className="text-center">
                  <div className="flex justify-center mb-2">
                    {metric.icon}
                  </div>
                  <Typography.Text className="text-lg font-bold text-gray-900">
                    {metric.value}
                  </Typography.Text>
                  <Typography.Text className="text-xs text-gray-600">
                    {metric.label}
                  </Typography.Text>
                  <Typography.Text className="text-xs text-green-600 font-medium">
                    {metric.improvement}
                  </Typography.Text>
                </div>
              ))}
            </div>

            <div className="border-t pt-4">
              <Typography.Text className="italic text-gray-700 mb-3">
                "{story.quote}"
              </Typography.Text>
              <div className="flex items-center justify-between">
                <div>
                  <Typography.Text className="font-semibold text-gray-900">
                    {story.author.name}
                  </Typography.Text>
                  <Typography.Text className="text-sm text-gray-600">
                    {story.author.title}
                  </Typography.Text>
                </div>
                <Button 
                  variant="link" 
                  size="sm"
                  onClick={() => setSelectedStory(story)}
                  className="text-blue-600 p-0 h-auto"
                >
                  Read Full Story <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );

  return (
    <div className="space-y-8">
      {/* Filters */}
      {showFilters && (
        <div className="flex flex-wrap gap-2 justify-center">
          {filters.map((filter) => (
            <Button
              key={filter.id}
              variant={activeFilter === filter.id ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveFilter(filter.id)}
              className="relative"
            >
              {filter.label}
              <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold rounded-full bg-white/20">
                {filter.count}
              </span>
            </Button>
          ))}
        </div>
      )}

      {/* Stories Grid */}
      <motion.div
        variants={animated ? containerVariants : {}}
        initial={animated ? "hidden" : ""}
        animate={animated ? "visible" : ""}
        className="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        {filteredStories.map((story, index) => (
          <StoryCard key={story.id} story={story} index={index} />
        ))}
      </motion.div>

      {/* Modal for detailed story view */}
      <AnimatePresence>
        {selectedStory && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedStory(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-4">
                <Typography.Heading level="h2" className="text-2xl font-bold">
                  {selectedStory.company} Success Story
                </Typography.Heading>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedStory(null)}
                >
                  Close
                </Button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <Typography.Text className="font-semibold mb-2">Challenge</Typography.Text>
                  <Typography.Text className="text-gray-700">{selectedStory.challenge}</Typography.Text>
                </div>
                
                <div>
                  <Typography.Text className="font-semibold mb-2">Solution</Typography.Text>
                  <Typography.Text className="text-gray-700">{selectedStory.solution}</Typography.Text>
                </div>
                
                <div>
                  <Typography.Text className="font-semibold mb-2">Results</Typography.Text>
                  <Typography.Text className="text-gray-700">{selectedStory.results}</Typography.Text>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SuccessStories;