import React from 'react';
import { Container, Row, Col, Grid } from '../components/ui/Grid';
import { Card, CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import { EnhancedMetricCard, MetricCardGrid } from '../components/dashboard/EnhancedMetricCard';
import { Button } from '../components/ui/Button';
import { Typography } from '../components/ui/Typography';
import { ColorPalette } from '../components/ui/ColorPalette';
import { Badge } from '../components/ui/Badge';
import { Download, Settings, ChevronRight, Bell, Mail, User, TrendingUp, Users, FileText, CheckCircle } from 'lucide-react';

/**
 * UI System Demo Page
 * 
 * This page demonstrates the implementation of the Modern UI/UX requirements:
 * 1. Responsive 12-column grid system
 * 2. Core typography with Inter/Source Sans Pro fonts
 * 3. Primary color palette (brand, success/error, neutrals)
 * 4. Initial dashboard layout with basic card components
 */
const UISystemPage: React.FC = () => {
  return (
    <Container>
      <div className="py-10">
        <Typography.Heading level="h1" className="mb-6">
          Modern UI/UX System
        </Typography.Heading>
        
        <Typography.Text className="mb-10 text-lg">
          This page demonstrates the implementation of our modern UI/UX system following the 
          requirements for responsive grid, typography, color palette, and component layout.
        </Typography.Text>
        
        {/* Section: Responsive Grid System */}
        <section className="mb-16">
          <Typography.Heading level="h2" className="mb-6">
            1. Responsive 12-Column Grid System
          </Typography.Heading>
          
          <Card className="mb-8">
            <CardHeader title="Grid System" subtitle="Responsive 12-column grid demonstration" />
            <CardContent>
              <Typography.Text className="mb-4">
                The grid system provides a flexible 12-column layout that adapts to different 
                screen sizes. Here's a demonstration of equal-width columns:
              </Typography.Text>
              
              {/* Equal width columns */}
              <div className="mb-8">
                <Typography.Text weight="medium" className="mb-2">Equal Width Columns</Typography.Text>
                <Row gap={4} className="mb-2">
                  <Col span={12} className="bg-primary-light p-2 text-center rounded">12 cols</Col>
                </Row>
                <Row gap={4} className="mb-2">
                  <Col span={6} className="bg-primary-light p-2 text-center rounded">6 cols</Col>
                  <Col span={6} className="bg-primary-light p-2 text-center rounded">6 cols</Col>
                </Row>
                <Row gap={4} className="mb-2">
                  <Col span={4} className="bg-primary-light p-2 text-center rounded">4 cols</Col>
                  <Col span={4} className="bg-primary-light p-2 text-center rounded">4 cols</Col>
                  <Col span={4} className="bg-primary-light p-2 text-center rounded">4 cols</Col>
                </Row>
                <Row gap={4} className="mb-2">
                  <Col span={3} className="bg-primary-light p-2 text-center rounded">3 cols</Col>
                  <Col span={3} className="bg-primary-light p-2 text-center rounded">3 cols</Col>
                  <Col span={3} className="bg-primary-light p-2 text-center rounded">3 cols</Col>
                  <Col span={3} className="bg-primary-light p-2 text-center rounded">3 cols</Col>
                </Row>
              </div>
              
              {/* Responsive columns */}
              <div>
                <Typography.Text weight="medium" className="mb-2">Responsive Columns</Typography.Text>
                <Typography.Text className="mb-4 text-text-secondary">
                  These columns change their width based on screen size. Resize the window to see the effect.
                </Typography.Text>
                
                <Row gap={4}>
                  <Col span={12} md={6} lg={3} className="bg-primary-light p-4 text-center rounded mb-4">
                    <Typography.Text>
                      12 cols on mobile<br/>
                      6 cols on tablet<br/>
                      3 cols on desktop
                    </Typography.Text>
                  </Col>
                  <Col span={12} md={6} lg={3} className="bg-primary-light p-4 text-center rounded mb-4">
                    <Typography.Text>
                      12 cols on mobile<br/>
                      6 cols on tablet<br/>
                      3 cols on desktop
                    </Typography.Text>
                  </Col>
                  <Col span={12} md={6} lg={3} className="bg-primary-light p-4 text-center rounded mb-4">
                    <Typography.Text>
                      12 cols on mobile<br/>
                      6 cols on tablet<br/>
                      3 cols on desktop
                    </Typography.Text>
                  </Col>
                  <Col span={12} md={6} lg={3} className="bg-primary-light p-4 text-center rounded mb-4">
                    <Typography.Text>
                      12 cols on mobile<br/>
                      6 cols on tablet<br/>
                      3 cols on desktop
                    </Typography.Text>
                  </Col>
                </Row>
              </div>
            </CardContent>
          </Card>
        </section>
        
        {/* Section: Typography */}
        <section className="mb-16">
          <Typography.Heading level="h2" className="mb-6">
            2. Core Typography
          </Typography.Heading>
          
          <Card className="mb-8">
            <CardHeader title="Typography System" subtitle="Inter and Source Sans Pro fonts" />
            <CardContent>
              <div className="mb-8">
                <Typography.Text weight="medium" className="mb-4">Headings (Inter Font)</Typography.Text>
                <div className="space-y-4">
                  <Typography.Heading level="h1">Heading 1 (Inter)</Typography.Heading>
                  <Typography.Heading level="h2">Heading 2 (Inter)</Typography.Heading>
                  <Typography.Heading level="h3">Heading 3 (Inter)</Typography.Heading>
                  <Typography.Heading level="h4">Heading 4 (Inter)</Typography.Heading>
                  <Typography.Heading level="h5">Heading 5 (Inter)</Typography.Heading>
                  <Typography.Heading level="h6">Heading 6 (Inter)</Typography.Heading>
                </div>
              </div>
              
              <div className="mb-8">
                <Typography.Text weight="medium" className="mb-4">Body Text (Source Sans Pro)</Typography.Text>
                <div className="space-y-4">
                  <Typography.Text size="xl">Extra Large Text (Source Sans Pro)</Typography.Text>
                  <Typography.Text size="lg">Large Text (Source Sans Pro)</Typography.Text>
                  <Typography.Text size="base">Base Text (Source Sans Pro)</Typography.Text>
                  <Typography.Text size="sm">Small Text (Source Sans Pro)</Typography.Text>
                  <Typography.Text size="xs">Extra Small Text (Source Sans Pro)</Typography.Text>
                </div>
              </div>
              
              <div className="mb-8">
                <Typography.Text weight="medium" className="mb-4">Text Variants</Typography.Text>
                <div className="space-y-2">
                  <Typography.Text variant="default">Default Text</Typography.Text>
                  <Typography.Text variant="secondary">Secondary Text</Typography.Text>
                  <Typography.Text variant="muted">Muted Text</Typography.Text>
                  <Typography.Text variant="success">Success Text</Typography.Text>
                  <Typography.Text variant="error">Error Text</Typography.Text>
                  <Typography.Text variant="warning">Warning Text</Typography.Text>
                  <Typography.Text variant="info">Info Text</Typography.Text>
                </div>
              </div>
              
              <div>
                <Typography.Text weight="medium" className="mb-4">Font Weights</Typography.Text>
                <div className="space-y-2">
                  <Typography.Text weight="light">Light Weight (300)</Typography.Text>
                  <Typography.Text weight="normal">Normal Weight (400)</Typography.Text>
                  <Typography.Text weight="medium">Medium Weight (500)</Typography.Text>
                  <Typography.Text weight="semibold">Semi-Bold Weight (600)</Typography.Text>
                  <Typography.Text weight="bold">Bold Weight (700)</Typography.Text>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
        
        {/* Section: Color Palette */}
        <section className="mb-16">
          <Typography.Heading level="h2" className="mb-6">
            3. Primary Color Palette
          </Typography.Heading>
          
          <ColorPalette />
        </section>
        
        {/* Section: Dashboard Layout with Card Components */}
        <section className="mb-16">
          <Typography.Heading level="h2" className="mb-6">
            4. Dashboard Layout with Card Components
          </Typography.Heading>
          
          <div className="mb-8">
            <Typography.Text className="mb-4">
              This example demonstrates a typical dashboard layout with various card components:
            </Typography.Text>
            
            {/* Enhanced Metric Cards with Animations */}
            <MetricCardGrid className="mb-8">
              <EnhancedMetricCard
                title="Total Invoices"
                value={2547}
                previousValue={2270}
                icon={<FileText className="w-6 h-6" />}
                countUp={true}
                animationDuration={2000}
              />
              <EnhancedMetricCard
                title="Pending Invoices"
                value={128}
                previousValue={132}
                icon={<Users className="w-6 h-6" />}
                countUp={true}
                animationDuration={1800}
              />
              <EnhancedMetricCard
                title="Success Rate"
                value={98.4}
                previousValue={97.7}
                suffix="%"
                precision={1}
                icon={<CheckCircle className="w-6 h-6" />}
                countUp={true}
                animationDuration={2200}
              />
              <EnhancedMetricCard
                title="Total Value"
                value={4500000}
                previousValue={3900000}
                prefix="₦"
                icon={<TrendingUp className="w-6 h-6" />}
                formatValue={(value) => `${(value / 1000000).toFixed(1)}M`}
                countUp={true}
                animationDuration={2500}
              />
            </MetricCardGrid>
            
            {/* Main Dashboard Content */}
            <Row gap={6}>
              {/* Left Column */}
              <Col span={12} lg={8}>
                <Card className="mb-6">
                  <CardHeader 
                    title="Recent Activity" 
                    subtitle="Latest system events and transactions"
                    action={
                      <Button variant="outline" size="sm" className="flex items-center gap-1">
                        <Settings size={14} />
                        <span>Settings</span>
                      </Button>
                    }
                  />
                  <CardContent>
                    <div className="space-y-4">
                      {/* Activity Items */}
                      {[
                        { id: 1, description: 'Invoice #INV-3847 processed successfully', timestamp: '10 minutes ago', status: 'success' },
                        { id: 2, description: 'Invoice #INV-3846 validation failed', timestamp: '25 minutes ago', status: 'error' },
                        { id: 3, description: 'Integration with Odoo updated', timestamp: '1 hour ago', status: 'info' },
                        { id: 4, description: 'Invoice #INV-3845 processed successfully', timestamp: '2 hours ago', status: 'success' },
                        { id: 5, description: 'System maintenance completed', timestamp: '5 hours ago', status: 'info' },
                      ].map(item => (
                        <div key={item.id} className="flex justify-between items-center p-3 bg-background-alt rounded-md">
                          <div>
                            <Typography.Text weight="medium">{item.description}</Typography.Text>
                            <Typography.Text variant="secondary" size="sm">{item.timestamp}</Typography.Text>
                          </div>
                          <Badge 
                            variant={
                              item.status === 'success' ? 'success' : 
                              item.status === 'error' ? 'destructive' : 
                              'secondary'
                            }
                          >
                            {item.status}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button variant="ghost" size="sm" className="ml-auto flex items-center gap-1">
                      <span>View All Activity</span>
                      <ChevronRight size={16} />
                    </Button>
                  </CardFooter>
                </Card>
                
                <Card>
                  <CardHeader title="System Health" subtitle="Current system status" />
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <Typography.Text>API Uptime</Typography.Text>
                        <Badge variant="success">99.9%</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <Typography.Text>Database</Typography.Text>
                        <Badge variant="success">Online</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <Typography.Text>Storage</Typography.Text>
                        <Badge variant="warning">78% Used</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <Typography.Text>FIRS Connection</Typography.Text>
                        <Badge variant="secondary">Degraded</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <Typography.Text>Scheduled Tasks</Typography.Text>
                        <Badge variant="success">Running</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Col>
              
              {/* Right Column */}
              <Col span={12} lg={4}>
                <Card className="mb-6">
                  <CardHeader title="Quick Actions" />
                  <CardContent>
                    <div className="space-y-3">
                      <Button className="w-full flex justify-between items-center">
                        <span>Generate IRN</span>
                        <ChevronRight size={16} />
                      </Button>
                      <Button variant="secondary" className="w-full flex justify-between items-center">
                        <span>Validate Invoice</span>
                        <ChevronRight size={16} />
                      </Button>
                      <Button variant="outline" className="w-full flex justify-between items-center">
                        <span>Export Report</span>
                        <Download size={16} />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader title="Notifications" subtitle="Recent alerts" />
                  <CardContent>
                    <div className="space-y-4">
                      {/* Notification Items */}
                      {[
                        { id: 1, title: 'System Update', message: 'A new system update is available', icon: <Bell size={16} /> },
                        { id: 2, title: 'New Message', message: 'You have a new message from admin', icon: <Mail size={16} /> },
                        { id: 3, title: 'Profile Updated', message: 'Your profile was updated successfully', icon: <User size={16} /> },
                      ].map(item => (
                        <div key={item.id} className="flex items-start gap-3 p-3 bg-background-alt rounded-md">
                          <div className="mt-1 text-primary">{item.icon}</div>
                          <div>
                            <Typography.Text weight="medium">{item.title}</Typography.Text>
                            <Typography.Text variant="secondary" size="sm">{item.message}</Typography.Text>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button variant="ghost" size="sm" className="ml-auto">
                      View All
                    </Button>
                  </CardFooter>
                </Card>
              </Col>
            </Row>
          </div>
        </section>
      </div>
    </Container>
  );
};

export default UISystemPage;
