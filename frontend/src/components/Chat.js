// src/components/Chat.js
import React, { useState } from 'react';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { type: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      if (response.ok) {
        const botMessage = {
          type: 'bot',
          content: data.response,
          sources: data.sources || []
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        throw new Error(data.error || 'Erreur serveur');
      }
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        content: `Erreur: ${error.message}`,
        sources: []
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setLoading(false);
    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>🤖 Chatbot with Web Search</h1>
        <p>Ask your questions, I search the Internet for you!</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>👋 Hello! Try asking:</p>
            <ul>
              <li>"What are the latest news in AI?"</li>
              <li>"Weather in Paris today"</li>
              <li>"Current Bitcoin price"</li>
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message ${message.type}`}>
            <div className="message-content">
              <div className="message-text">
                {message.content}
              </div>
              
              {message.sources && message.sources.length > 0 && (
                <div className="message-sources">
                  <h4>📚 Sources :</h4>
                  {message.sources.map((source, i) => (
                    <div key={i} className="source">
                      <a href={source.url} target="_blank" rel="noopener noreferrer">
                        {source.title}
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message bot">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input">
        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question here..."
            disabled={loading}
            rows="1"
          />
          <button 
            onClick={sendMessage} 
            disabled={loading || !input.trim()}
            className="send-button"
          >
            {loading ? '⏳' : '📤'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;