import { useState, useEffect } from "react";
import { ThemeToggle } from "../theme/ThemeToggle";
import { ApiCredits } from "./ApiCredits";
import { Sidebar } from "./Sidebar";
import { LoginButton } from "../auth/LoginButton";
import { GuestActionCounter } from "../auth/GuestActionCounter";
import { UserProfile } from "../auth/UserProfile";
import { useAuthContext } from "../../auth/AuthContext";

interface LayoutProps {
  children: React.ReactNode;
  onProductResultsClick?: (messageId: string) => void;
  isMobile?: boolean;
}

export function Layout({ children, onProductResultsClick, isMobile: propIsMobile }: LayoutProps) {
  const [isMobile, setIsMobile] = useState(propIsMobile || false);
  const { isAuthenticated } = useAuthContext();

  // Check if the screen is mobile size (only if not provided via props)
  useEffect(() => {
    if (propIsMobile !== undefined) {
      setIsMobile(propIsMobile);
      return;
    }
    
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // 768px is the md breakpoint in Tailwind
    };

    // Initial check
    checkIfMobile();

    // Add event listener for window resize
    window.addEventListener("resize", checkIfMobile);

    // Clean up
    return () => window.removeEventListener("resize", checkIfMobile);
  }, [propIsMobile]);

  return (
    <div className="h-screen bg-[hsl(var(--background))] flex flex-col overflow-hidden">
      {/* Header */}
      <header className="w-full border-b bg-[hsl(var(--background))] flex-shrink-0">
        <div className="container flex h-16 items-center justify-between px-4 sm:px-8">
          <div className="flex items-center">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="w-6 h-6 mr-2 text-[hsl(var(--primary))]"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4" />
              <path d="M12 8h.01" />
            </svg>
            <h1 className="text-xl font-bold">AI Shopping Assistant</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <GuestActionCounter />
            <ApiCredits />
            <ThemeToggle />
            {isAuthenticated ? <UserProfile /> : <LoginButton />}
          </div>
        </div>
      </header>
      
      {/* Main content with two-panel layout - fixed height to prevent page scrolling */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Chat interface */}
        <div className={`${isMobile ? 'hidden' : 'w-1/3 lg:w-2/5'} border-r bg-[hsl(var(--background))] flex flex-col`}>
          <div className="p-4 border-b flex-shrink-0">
            <h2 className="text-lg font-semibold">Chat History</h2>
          </div>
          <div className="flex-1 overflow-hidden">
            <Sidebar 
              isMobile={false} 
              onProductResultsClick={onProductResultsClick}
            />
          </div>
        </div>
        
        {/* Right panel - Product display */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
      </div>
      
      {/* Mobile sidebar */}
      {isMobile && <Sidebar isMobile={true} onProductResultsClick={onProductResultsClick} />}
      
      {/* Footer */}
      <footer className="border-t bg-[hsl(var(--background))] flex-shrink-0">
        <div className="container flex h-16 items-center px-4 sm:px-8 justify-between text-sm text-[hsl(var(--muted-foreground))]">
          <div>© {new Date().getFullYear()} AI Shopping Assistant</div>
          <div className="flex items-center space-x-4">
            <a href="#" className="hover:underline">Contact</a>
            <a href="#" className="hover:underline">Terms</a>
            <div>Affiliate links may generate commission</div>
          </div>
        </div>
      </footer>
    </div>
  );
}