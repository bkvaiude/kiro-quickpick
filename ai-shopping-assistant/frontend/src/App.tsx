import { BrowserRouter as Router } from "react-router-dom";
import { ChatProvider } from "./context/ChatContext";
import { AuthProvider } from "./auth/AuthContext";
import { ThemeProvider } from "./components/theme/ThemeProvider";
import { AppRoutes } from "./routes/AppRoutes";

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="shopping-assistant-theme">
      <AuthProvider>
        <ChatProvider>
          <Router>
            <AppRoutes />
          </Router>
        </ChatProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}


export default App;