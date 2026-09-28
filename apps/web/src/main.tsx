import React from 'react';
import ReactDOM from 'react-dom/client';
import './shared/styles/fonts.css';
import { App } from './app/App';
import './shared/styles/tokens.css';
import './shared/styles/global.css';
import './shared/styles/identity.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
