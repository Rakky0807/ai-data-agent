import React, { useState } from 'react';
import FileUpload from './components/FileUpload';
import ChatWindow from './components/ChatWindow';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [initialMessage, setInitialMessage] = useState('');

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 AI Data Agent</h1>
        <p>Your Conversational Data Analyst</p>
      </header>
      <main>
        {!sessionId ? (
          <FileUpload setSessionId={setSessionId} setInitialMessage={setInitialMessage} />
        ) : (
          <ChatWindow sessionId={sessionId} initialMessage={initialMessage} />
        )}
      </main>
      <footer>
        <p>Built for the SDE Hiring Assignment</p>
      </footer>
    </div>
  );
}

export default App;