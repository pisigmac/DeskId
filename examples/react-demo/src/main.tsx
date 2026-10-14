import React from 'react'
import ReactDOM from 'react-dom/client'
import { DeskIdProvider } from '@deskid/react'
import App from './App'

const authBaseUrl = import.meta.env.VITE_DESKID_URL || 'http://127.0.0.1:8090'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <DeskIdProvider baseUrl={authBaseUrl} storage="localStorage" autoRefresh={true}>
      <App />
    </DeskIdProvider>
  </React.StrictMode>
)
