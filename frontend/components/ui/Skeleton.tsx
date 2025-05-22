import { cn } from "../../utils/cn";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

/**
 * Skeleton component for loading states
 * 
 * Used to display a placeholder while content is loading
 */
export function Skeleton({ className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-secondary/30",
        className
      )}
      {...props}
    />
  );
}
