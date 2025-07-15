import React, { useState } from 'react';
import Chat from './components/Chat';
import ImageUpload from './components/ImageUpload';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="App">
      <div className="tab-navigation">
        <button 
          className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat with web search
        </button>
        <button 
          className={`tab-button ${activeTab === 'image' ? 'active' : ''}`}
          onClick={() => setActiveTab('image')}
        >
          🖼️ Image analysis
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'chat' && <Chat />}
        {activeTab === 'image' && <ImageUpload />}
      </div>
    </div>
  );
}

export default App;