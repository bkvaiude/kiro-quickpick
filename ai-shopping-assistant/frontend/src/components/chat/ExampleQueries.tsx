import { Button } from "../ui/button";

interface ExampleQueriesProps {
  onSelectQuery: (query: string) => void;
}

const exampleQueries = [
  "What's the best 5G phone under ₹12,000 with 8GB RAM?",
  "Recommend a good laptop for programming under ₹50,000",
  "What are the best wireless earbuds under ₹2,000?",
  "Compare top washing machines under ₹20,000"
];

export function ExampleQueries({ onSelectQuery }: ExampleQueriesProps) {
  return (
    <div className="flex flex-col space-y-2">
      <p className="text-sm text-[hsl(var(--muted-foreground))]">Try asking:</p>
      <div className="flex flex-wrap gap-2">
        {exampleQueries.map((query, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => onSelectQuery(query)}
          >
            {query}
          </Button>
        ))}
      </div>
    </div>
  );
}