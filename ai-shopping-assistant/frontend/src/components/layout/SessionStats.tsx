import React from "react";
import { Card } from "../ui/card";
import { useChatContext } from "../../context/ChatContext";

export function SessionStats() {
  const { state } = useChatContext();
  const { messages } = state;
  
  // Count user messages (queries)
  const queriesUsed = messages.filter(msg => msg.sender === 'user').length;
  
  // Mock API credits - in a real app, this would come from the API response
  const creditsLeft = 10 - queriesUsed > 0 ? 10 - queriesUsed : 0;
  
  // Calculate session duration
  const sessionStart = messages.length > 0 
    ? new Date(messages[0].timestamp).getTime() 
    : new Date().getTime();
  const sessionDuration = Math.floor((new Date().getTime() - sessionStart) / 60000); // in minutes
  
  return (
    <Card className="p-4 mb-4">
      <h3 className="text-sm font-medium mb-2">Session Stats</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-[hsl(var(--muted-foreground))]">Queries used:</span>
          <span className="font-medium">{queriesUsed}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[hsl(var(--muted-foreground))]">Credits left:</span>
          <span className="font-medium">{creditsLeft}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[hsl(var(--muted-foreground))]">Session time:</span>
          <span className="font-medium">{sessionDuration} min</span>
        </div>
      </div>
    </Card>
  );
}