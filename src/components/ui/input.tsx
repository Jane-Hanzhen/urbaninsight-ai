import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "min-h-11 w-full rounded-md border border-border bg-surface px-md text-caption text-text-primary shadow-card outline-none transition-all duration-fast ease-smooth placeholder:text-text-secondary focus:border-primary focus:ring-2 focus:ring-map-glow",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };
