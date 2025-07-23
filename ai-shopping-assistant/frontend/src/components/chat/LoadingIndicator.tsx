import { Spinner } from "../ui/spinner";

export function LoadingIndicator() {
  return (
    <div className="flex w-full items-center justify-start p-4">
      <div className="flex items-center space-x-2 rounded-lg bg-[hsl(var(--muted))] px-4 py-2">
        <Spinner size="sm" />
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Thinking...</p>
      </div>
    </div>
  );
}