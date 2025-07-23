import { Card } from "../ui/card";

interface RecommendationsSummaryProps {
  summary: string;
}

export function RecommendationsSummary({ summary }: RecommendationsSummaryProps) {
  // Check if the summary contains bullet points (lines starting with •)
  const hasBulletPoints = summary.includes('•');
  
  // If it has bullet points, split by newline and render each point separately
  const summaryContent = hasBulletPoints ? (
    <ul className="list-none pl-0 space-y-2">
      {summary.split('\n').map((line, index) => {
        // Remove the bullet point character and trim
        const text = line.replace('•', '').trim();
        return text ? (
          <li key={index} className="flex items-start">
            <span className="text-[hsl(var(--primary))] mr-2 mt-0.5">•</span>
            <span>{text}</span>
          </li>
        ) : null;
      })}
    </ul>
  ) : (
    <p>{summary}</p>
  );

  return (
    <Card className="p-6 bg-[hsl(var(--primary))]/5 border-[hsl(var(--primary))]/20 shadow-sm">
      <div className="flex items-center mb-3">
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          className="w-5 h-5 mr-2 text-[hsl(var(--primary))]"
        >
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <h3 className="font-semibold text-lg">AI Recommendations</h3>
      </div>
      <div className="text-sm text-[hsl(var(--foreground))]">{summaryContent}</div>
    </Card>
  );
}