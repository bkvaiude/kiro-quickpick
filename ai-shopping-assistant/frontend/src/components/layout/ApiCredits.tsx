import { useChatContext } from "../../context/ChatContext";

export function ApiCredits() {
  const { state } = useChatContext();
  const { messages } = state;
  
  // Count user messages (queries)
  const queriesUsed = messages.filter(msg => msg.sender === 'user').length;
  
  // Mock API credits - in a real app, this would come from the API response
  const creditsLeft = 10 - queriesUsed > 0 ? 10 - queriesUsed : 0;
  const percentage = (creditsLeft / 10) * 100;
  
  // Determine color based on credits left
  const getColor = () => {
    if (creditsLeft <= 2) return 'bg-red-500';
    if (creditsLeft <= 5) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  
  return (
    <div className="flex items-center space-x-2">
      <div className="flex flex-col">
        <div className="flex items-center text-sm">
          <span className="text-[hsl(var(--muted-foreground))] mr-1">API Credits:</span>
          <span className={`font-medium ${creditsLeft < 3 ? 'text-red-500' : ''}`}>
            {creditsLeft}/10
          </span>
        </div>
        <div className="w-full bg-[hsl(var(--muted))] rounded-full h-1.5 mt-1">
          <div 
            className={`h-1.5 rounded-full ${getColor()}`} 
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
}