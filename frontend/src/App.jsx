import { useState, useEffect} from "react";

import Navbar from "./components/Navbar";
import FieldEntryPage from "./pages/FieldEntryPage";
import QueryPage from "./pages/QueryPage";
import SeedInventoryPage from "./pages/SeedInventoryPage";
import LoginPage from "./pages/LoginPage";
import {login, logout, getCurrentUser, getAccessToken, saveAccessToken, removeAccessToken } from "./services/authService";

const VIEWS = {
  FIELD_ENTRY: "field-entry",
  QUERY: "query",
  SEED_INVENTORY: "seed-inventory",
};

export default function App() {
  const [activeView, setActiveView] = useState(VIEWS.FIELD_ENTRY);
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  
  useEffect(() => {
    let cancelled = false;

    async function checkAuthentication(){
      const token = getAccessToken();

      try{
        if (token){
          const currentUser = await getCurrentUser(token);

          if(!cancelled){
            setUser(currentUser);
          }
        }
      }catch{
        if(!cancelled){
          removeAccessToken();
          setUser(null);
        }
      }finally{
        if(!cancelled){
          setCheckingAuth(false);
        }
      }
    }

    checkAuthentication()

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(()=>{
    function handleSessionExpired(){
      removeAccessToken();
      setUser(null);
      setActiveView(VIEWS.FIELD_ENTRY);
    }
    window.addEventListener("harvestdb:session-expired", handleSessionExpired);

    return () => {
      window.removeEventListener("harvestdb:session-expired", handleSessionExpired);
    };
  }, []);

  async function handleLogin(email, password){
    const data = await login(email, password);
    const currentUser = await getCurrentUser(data.access_token);
    saveAccessToken(data.access_token);
    setUser(currentUser);
  }

  function handleLogout(){
    logout();
    setUser(null);
    setActiveView(VIEWS.FIELD_ENTRY);
  }

  if(checkingAuth){
    return(
      <div className="auth-loading">
        Checking Authentication...
      </div>
    );
  }
  if(!user){
    return<LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <Navbar activeView={activeView} onNavigate={setActiveView} views={VIEWS}  user={user} onLogout={handleLogout}/>
      <main className="page-content">
        {activeView === VIEWS.FIELD_ENTRY && <FieldEntryPage />}
        {activeView === VIEWS.QUERY && <QueryPage />}
        {activeView === VIEWS.SEED_INVENTORY && <SeedInventoryPage />}
      </main>
    </div>
  );
}
