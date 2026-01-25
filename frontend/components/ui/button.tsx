import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-medium transition",
  {
    variants: {
      variant: {
        primary: "bg-black text-white",
        ghost: "bg-white/70"
      }
    },
    defaultVariants: { variant: "primary" }
  }
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant }), className)} {...props} />;
}
