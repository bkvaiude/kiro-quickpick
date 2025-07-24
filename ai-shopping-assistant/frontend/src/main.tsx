import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { CustomAuth0Provider } from './auth/Auth0Provider'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CustomAuth0Provider>
      <App />
    </CustomAuth0Provider>
  </React.StrictMode>,
)
