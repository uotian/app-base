import type { StatusItemProps } from "@/types/ui";

export function StatusItem({ label, value }: StatusItemProps) {
  return (
    <div className="flex flex-col gap-2.5 py-5.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <dt className="flex items-center gap-2.5 text-sm whitespace-nowrap text-muted-foreground">
        <span aria-hidden="true" className="size-2 rounded-full bg-success" />
        {label}
      </dt>
      <dd className="text-[15px] font-medium">{value}</dd>
    </div>
  );
}
