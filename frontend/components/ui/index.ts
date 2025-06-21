// Export UI components for use throughout the application

// Import and re-export each component with its correct exports
// Accordion component
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './Accordion';

// Toast/Alert components
import { ToastComponent, ToastContainer, ToastProvider, useToast } from './Toast';
// Export Alert as an alias for ToastComponent for backward compatibility
const Alert = ToastComponent;

// Badge component
import { Badge, badgeVariants } from './Badge';

// Button component
import { Button, buttonVariants } from './Button';

// Card components
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter,
} from './Card';
import { CardGrid } from './Card';
import { MetricCard } from './Card'; // @deprecated - Use EnhancedMetricCard from dashboard/ instead

// Typography components
import TypographyObj, { Heading, Text, Typography, Label as TypographyLabel } from './Typography';

// Import other components
import { BarChart, LineChart, chartThemes, createDataset } from './Charts';
import Checkbox from './Checkbox';
import ColorPalette from './ColorPalette';
import Container from './Container';
import { Divider, dividerVariants } from './Divider';
import FormField from './FormField';
import { Grid } from './Grid';
import { IconButton } from './IconButton';
import { Input, inputVariants } from './Input';
import { Label, labelVariants } from './Label';
import MainNav from './MainNav';
import MobileNav from './MobileNav';
import Modal, { modalVariants, modalContentVariants } from './Modal';
import { Progress } from './Progress';
import ResponsiveTable from './ResponsiveTable';
import { 
  Select, 
  LegacySelect, 
  selectVariants,
  SelectRoot, 
  SelectTrigger, 
  SelectValue, 
  SelectContent, 
  SelectItem 
} from './Select';
import Spinner from './Spinner';
import StandardCard from './StandardCard';
import { Switch } from './Switch';
import { Table } from './Table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';
import Textarea from './Textarea';
import { Tooltip } from './Tooltip';
import { TransactionTable } from './TransactionTable';

// Re-export everything
export {
  // Accordion components
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,

  // Toast/Alert components
  ToastComponent,
  ToastContainer,
  ToastProvider,
  useToast,
  Alert,
  
  // Badge
  Badge,
  badgeVariants,
  
  // Button
  Button,
  buttonVariants,
  
  // Card components
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  CardGrid,
  MetricCard,
  
  // Typography
  Typography,
  Heading,
  Text,
  TypographyLabel,
  
  // All other components
  BarChart,
  LineChart,
  chartThemes,
  createDataset,
  Checkbox,
  ColorPalette,
  Container,
  Divider,
  dividerVariants,
  FormField,
  Grid,
  IconButton,
  Input,
  inputVariants,
  Label,
  labelVariants,
  MainNav,
  MobileNav,
  Modal,
  modalVariants,
  modalContentVariants,
  Progress,
  ResponsiveTable,
  Select,
  LegacySelect,
  selectVariants,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Spinner,
  StandardCard,
  Switch,
  Table,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Textarea,
  Tooltip,
  TransactionTable
};

// Typography is already exported from the imported module
