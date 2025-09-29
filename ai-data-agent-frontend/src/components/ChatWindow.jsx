import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import apiClient from '../api/apiClient';

const ChatWindow = ({ sessionId, initialMessage }) => {
  const [messages, setMessages] = useState([{ sender: 'ai', text: initialMessage }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/query', {
        session_id: sessionId,
        query: input,
      });
      setMessages((prev) => [...prev, response.data]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { sender: 'ai', text: 'Sorry, I encountered an error. Please try again.' };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="chat-container">
       <h2>2. Ask Questions</h2>
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}
        {isLoading && <div className="typing-indicator"><span></span><span></span><span></span></div>}
        <div ref={chatEndRef} />
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about your data..."
          disabled={isLoading}
        />
        <button onClick={handleSend} disabled={isLoading}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;