import React from 'react';
import { Container } from '../components/ui/Container';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter,
  CardGrid
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { MobileNav } from '../components/ui/MobileNav';
import { 
  TableContainer, 
  Table, 
  TableHeader, 
  TableBody, 
  TableRow, 
  TableHead, 
  TableCell 
} from '../components/ui/Table';
import { TransactionTable, Transaction } from '../components/ui/TransactionTable';
import { PlusCircle, ExternalLink } from 'lucide-react';

const UIExamplePage: React.FC = () => {
  // Mock data for the transaction table
  const mockTransactions: Transaction[] = [
    {
      id: '1',
      date: '2023-06-12',
      reference: 'TXN-12345',
      type: 'Invoice',
      status: 'success',
      amount: 25000,
    },
    {
      id: '2',
      date: '2023-06-11',
      reference: 'TXN-12344',
      type: 'Credit Note',
      status: 'pending',
      amount: 5000,
    },
    {
      id: '3',
      date: '2023-06-10',
      reference: 'TXN-12343',
      type: 'Invoice',
      status: 'failed',
      amount: 12500,
    }
  ];

  const mockUserInfo = {
    name: 'Jane Doe',
    email: 'jane.doe@example.com'
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Navigation */}
      <MobileNav 
        userInfo={mockUserInfo}
        onLogout={() => alert('Logged out')}
      />

      {/* Main Content */}
      <Container maxWidth="xl" padding="medium" className="pt-8 md:pt-12">
        <h1 className="text-3xl font-heading font-semibold mb-6">UI Components</h1>

        {/* Responsive Containers */}
        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4">Responsive Containers</h2>
          <p className="mb-6 text-text-secondary">
            Mobile-first containers with proper padding, using Tailwind CSS utilities.
          </p>
          
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Mobile-First Container</CardTitle>
                <CardDescription>
                  Different max-width options with consistent padding
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-primary-light p-2 rounded text-center">
                    Default Container (max-width: 1024px)
                  </div>
                  
                  <div className="bg-background-alt p-2 rounded">
                    <code className="text-sm">
                      &lt;Container maxWidth="lg" padding="medium"&gt;...&lt;/Container&gt;
                    </code>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
        
        {/* Card Grid */}
        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4">Card Components</h2>
          <p className="mb-6 text-text-secondary">
            Standardized cards with 16px padding and 24px gap between cards.
          </p>
          
          <CardGrid columns={{ base: 1, md: 2, lg: 3 }}>
            <Card>
              <CardHeader>
                <CardTitle>Standard Card</CardTitle>
                <CardDescription>With 16px padding</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-text-secondary">
                  This is a standard card with consistent padding and spacing.
                </p>
              </CardContent>
              <CardFooter>
                <Button size="sm" className="ml-auto">Action</Button>
              </CardFooter>
            </Card>
            
            <Card variant="compact">
              <CardHeader>
                <CardTitle>Compact Card</CardTitle>
                <CardDescription>With less padding</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-text-secondary">
                  This is a compact card with reduced padding.
                </p>
              </CardContent>
              <CardFooter>
                <Button size="sm" className="ml-auto" variant="outline">Action</Button>
              </CardFooter>
            </Card>
            
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Elevated Card</CardTitle>
                <CardDescription>With shadow emphasis</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-text-secondary">
                  This card has elevated styling with shadows.
                </p>
              </CardContent>
              <CardFooter>
                <Button size="sm" className="ml-auto" variant="ghost">Action</Button>
              </CardFooter>
            </Card>
          </CardGrid>
        </section>
        
        {/* Table Examples */}
        <section className="mb-12">
          <h2 className="text-2xl font-heading font-semibold mb-4">Responsive Tables</h2>
          <p className="mb-6 text-text-secondary">
            Tables with horizontal scroll for transaction logs and data.
          </p>
          
          <div className="space-y-8">
            {/* Basic Table Example */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Responsive Table</CardTitle>
                <CardDescription>With horizontal scroll on mobile</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <TableContainer>
                  <Table minWidth="500px">
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Array.from({ length: 3 }).map((_, i) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">USER-{i + 1000}</TableCell>
                          <TableCell>User {i + 1}</TableCell>
                          <TableCell>user{i + 1}@example.com</TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              i % 3 === 0 ? 'bg-success bg-opacity-10 text-success' :
                              i % 3 === 1 ? 'bg-warning bg-opacity-10 text-warning' :
                              'bg-error bg-opacity-10 text-error'
                            }`}>
                              {i % 3 === 0 ? 'Active' : i % 3 === 1 ? 'Pending' : 'Inactive'}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
                              <ExternalLink size={16} />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
            
            {/* Transaction Table Example */}
            <Card>
              <CardHeader>
                <CardTitle>Transaction Log Table</CardTitle>
                <CardDescription>Using the TransactionTable component</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <TransactionTable 
                  transactions={mockTransactions}
                  onViewTransaction={(id) => alert(`View transaction ${id}`)}
                />
              </CardContent>
              <CardFooter>
                <Button variant="outline" size="sm" className="ml-auto flex items-center gap-1">
                  <PlusCircle size={16} />
                  <span>New Transaction</span>
                </Button>
              </CardFooter>
            </Card>
          </div>
        </section>
      </Container>
    </div>
  );
};

export default UIExamplePage; 