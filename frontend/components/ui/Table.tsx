import React, { HTMLProps, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Table container variants
const tableContainerVariants = cva(
  "w-full overflow-x-auto rounded-lg",
  {
    variants: {
      variant: {
        default: "border border-border shadow-sm",
        bordered: "border border-border",
        card: "border border-border bg-white shadow-sm rounded-lg",
        minimal: "",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface TableContainerProps
  extends HTMLProps<HTMLDivElement>,
    VariantProps<typeof tableContainerVariants> {}

const TableContainer = forwardRef<HTMLDivElement, TableContainerProps>(
  ({ className, variant, children, ...props }, ref) => {
    return (
      <div
        className={tableContainerVariants({ variant, className })}
        ref={ref}
        {...props}
      >
        {children}
      </div>
    );
  }
);
TableContainer.displayName = "TableContainer";

// Table component
export interface TableProps extends HTMLProps<HTMLTableElement> {
  minWidth?: string;
  stickyHeader?: boolean;
}

const Table = forwardRef<HTMLTableElement, TableProps>(
  ({ className, minWidth = "600px", stickyHeader = false, ...props }, ref) => {
    return (
      <table
        ref={ref}
        className={`w-full border-collapse ${className || ''}`}
        style={{ minWidth }}
        {...props}
      />
    );
  }
);
Table.displayName = "Table";

// Table Header
const TableHeader = forwardRef<
  HTMLTableSectionElement,
  HTMLProps<HTMLTableSectionElement> & { sticky?: boolean }
>(({ className, sticky = false, ...props }, ref) => (
  <thead
    ref={ref}
    className={`bg-background-alt ${
      sticky ? 'sticky top-0 z-10' : ''
    } ${className || ''}`}
    {...props}
  />
));
TableHeader.displayName = "TableHeader";

// Table Body
const TableBody = forwardRef<
  HTMLTableSectionElement,
  HTMLProps<HTMLTableSectionElement> & { maxHeight?: string }
>(({ className, maxHeight, ...props }, ref) => {
  const style: React.CSSProperties | undefined = maxHeight 
    ? { 
        maxHeight, 
        overflowY: 'auto' as const, 
        display: 'block' as const 
      } 
    : undefined;
  
  return (
    <tbody
      ref={ref}
      className={className || ''}
      style={style}
      {...props}
    />
  );
});
TableBody.displayName = "TableBody";

// Table Row
const TableRow = forwardRef<HTMLTableRowElement, HTMLProps<HTMLTableRowElement>>(
  ({ className, ...props }, ref) => (
    <tr
      ref={ref}
      className={`border-b border-border hover:bg-background-alt transition-colors ${className || ''}`}
      {...props}
    />
  )
);
TableRow.displayName = "TableRow";

// Table Head Cell
const TableHead = forwardRef<HTMLTableCellElement, HTMLProps<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <th
      ref={ref}
      className={`px-4 py-3 text-left text-sm font-semibold border-b border-border ${className || ''}`}
      {...props}
    />
  )
);
TableHead.displayName = "TableHead";

// Table Cell
const TableCell = forwardRef<HTMLTableCellElement, HTMLProps<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={`px-4 py-3 text-sm ${className || ''}`}
      {...props}
    />
  )
);
TableCell.displayName = "TableCell";

// Table Caption
const TableCaption = forwardRef<HTMLTableCaptionElement, HTMLProps<HTMLTableCaptionElement>>(
  ({ className, ...props }, ref) => (
    <caption
      ref={ref}
      className={`py-2 text-sm text-text-secondary ${className || ''}`}
      {...props}
    />
  )
);
TableCaption.displayName = "TableCaption";

// Empty state component for tables
interface TableEmptyProps extends HTMLProps<HTMLTableRowElement> {
  colSpan: number;
  message?: string;
}

const TableEmpty = forwardRef<HTMLTableRowElement, TableEmptyProps>(
  ({ className, colSpan, message = "No data available", ...props }, ref) => (
    <tr ref={ref} className={className} {...props}>
      <td 
        colSpan={colSpan}
        className="px-4 py-6 text-center text-text-secondary"
      >
        {message}
      </td>
    </tr>
  )
);
TableEmpty.displayName = "TableEmpty";

// Loading state component for tables
interface TableLoadingProps extends HTMLProps<HTMLTableRowElement> {
  colSpan: number;
  message?: string;
}

const TableLoading = forwardRef<HTMLTableRowElement, TableLoadingProps>(
  ({ className, colSpan, message = "Loading...", ...props }, ref) => (
    <tr ref={ref} className={className} {...props}>
      <td 
        colSpan={colSpan}
        className="px-4 py-6 text-center text-text-secondary"
      >
        {message}
      </td>
    </tr>
  )
);
TableLoading.displayName = "TableLoading";

export {
  TableContainer,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
  TableEmpty,
  TableLoading
}; 