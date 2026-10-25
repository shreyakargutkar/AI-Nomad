"use client";

import { useState, useEffect, useRef } from "react";
import { Mic, Send, Pause, Play, Compass, X, Loader } from "lucide-react";

export default function VoiceChatbot() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState({
    voice: null,
    rate: 1,
    pitch: 1,
    volume: 1
  });
  
  const chatBodyRef = useRef(null);
  const speechSynthesisRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize speech synthesis
  useEffect(() => {
    speechSynthesisRef.current = window.speechSynthesis;
    
    // Load available voices
    const loadVoices = () => {
      const voices = speechSynthesisRef.current.getVoices();
      if (voices.length > 0) {
        // Default to first English voice, or first available
        const englishVoice = voices.find(voice => voice.lang.includes('en-')) || voices[0];
        setVoiceSettings(prev => ({ ...prev, voice: englishVoice }));
      }
    };

    loadVoices();
    
    // Chrome loads voices asynchronously
    if (speechSynthesisRef.current.onvoiceschanged !== undefined) {
      speechSynthesisRef.current.onvoiceschanged = loadVoices;
    }

    // Send welcome message when chat is opened for the first time
    if (isChatOpen && messages.length === 0) {
      const timer = setTimeout(() => {
        addMessage("Hello — I'm Alfred, your Ainomad travel assistant. Where shall we plan your next journey?", "bot");
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isChatOpen, messages.length]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages]);

  // Clean up speech recognition and synthesis when component unmounts
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (speechSynthesisRef.current) {
        speechSynthesisRef.current.cancel();
      }
    };
  }, []);

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  const addMessage = (text, sender) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { text, sender, timestamp }]);
    if (sender === "bot" && !isPaused) {
      speakText(text);
    }
  };

  const sendMessage = async () => {
    if (inputText.trim() === "") return;
    
    const userMessage = inputText.trim();
    addMessage(userMessage, "user");
    setInputText("");
    setLoading(true);
    
    try {
      const response = await fetch("/api/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMessage,
          conversation_history: messages.map(m => ({ role: m.sender === "user" ? "user" : "assistant", content: m.text }))
        })
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      
      const data = await response.json();
      addMessage(data.reply || "Sorry, I couldn't process that request.", "bot");
    } catch (error) {
      console.error("Error:", error);
      addMessage("Error connecting to server. Please try again later.", "bot");
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text) => {
    if (speechSynthesisRef.current && !isPaused) {
      speechSynthesisRef.current.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Apply voice settings
      if (voiceSettings.voice) {
        utterance.voice = voiceSettings.voice;
      }
      utterance.rate = voiceSettings.rate;
      utterance.pitch = voiceSettings.pitch;
      utterance.volume = voiceSettings.volume;
      
      speechSynthesisRef.current.speak(utterance);
    }
  };

  const togglePause = () => {
    const synthesis = speechSynthesisRef.current;
    if (synthesis) {
      if (isPaused) {
        synthesis.resume();
      } else {
        synthesis.pause();
      }
    }
    setIsPaused(!isPaused);
  };

  const startVoiceRecognition = () => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        // Stop existing recognition instance if it exists
        if (recognitionRef.current) {
          recognitionRef.current.stop();
        }
        
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US'; // Set language
        
        recognition.onstart = () => {
          setIsListening(true);
        };
        
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          setInputText(transcript);
        };
        
        recognition.onend = () => {
          setIsListening(false);
          // Automatically send message when speech recognition ends
          if (inputText.trim()) {
            sendMessage();
          }
        };
        
        recognition.onerror = (event) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
          addMessage(`Speech recognition error: ${event.error}`, "bot");
        };
        
        recognition.start();
      } else {
        addMessage("Speech recognition is not supported in your browser.", "bot");
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="chat-container">
      <div className={`chat-box ${isChatOpen ? 'active' : 'hidden'}`}>
        <div className="chat-header">
          <div className="flex items-center gap-2">
            <span className="animate-spin-slow text-lg">🧭</span>
            <span>Alfred</span>
          </div>
          <div className="header-buttons">
            <button 
              className="clear-button" 
              onClick={clearChat} 
              aria-label="Clear chat history"
              title="Clear chat history"
            >
              Reset
            </button>
            <button 
              className="close-button" 
              onClick={toggleChat}
              aria-label="Close chat"
            >
              <X size={16} />
            </button>
          </div>
        </div>
        
        <div className="chat-body" ref={chatBodyRef}>
          {messages.length === 0 ? (
            <div className="empty-chat font-sans text-xs">
              <span className="text-3xl mb-2 opacity-55">📓</span>
              <p>Ask about visas, packing advice, local attractions, or daily schedules.</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={index} className={`message ${message.sender}`}>
                <div className="message-content">
                  {message.text}
                </div>
                <div className="message-timestamp font-mono">{message.timestamp}</div>
              </div>
            ))
          )}
          {loading && (
            <div className="message bot loading font-mono text-[10px]">
              <Loader className="animate-spin text-[#C85A32]" size={14} />
              <span>LOGGING ENTRY...</span>
            </div>
          )}
        </div>
        
        <div className="chat-footer">
          <textarea
            className="chat-input font-sans"
            placeholder="Write a message..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={loading || isListening}
            rows={1}
            aria-label="Message input"
          />
          <div className="button-group">
            <button 
              className={`voice-button ${isListening ? 'listening' : ''}`}
              onClick={startVoiceRecognition}
              disabled={loading}
              aria-label="Start voice recognition"
              title="Speak to type"
            >
              <Mic size={16} />
            </button>
            <button 
              className="pause-button"
              onClick={togglePause}
              aria-label={isPaused ? "Resume speech" : "Pause speech"}
              title={isPaused ? "Resume speech" : "Pause speech"}
            >
              {isPaused ? <Play size={16} /> : <Pause size={16} />}
            </button>
            <button 
              className="send-button"
              onClick={sendMessage}
              disabled={loading || inputText.trim() === ''}
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
      
      <button 
        className={`chat-toggle ${isChatOpen ? 'hidden' : ''}`} 
        onClick={toggleChat}
        aria-label="Open chat"
      >
        <Compass size={28} className="animate-spin-slow text-white" />
      </button>
      
      <style jsx>{`
        .chat-container {
          position: fixed;
          bottom: 24px;
          right: 24px;
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          z-index: 1000;
        }
        
        .chat-box {
          width: 360px;
          height: 480px;
          background: #FFFFFF;
          color: #1E2229;
          border-radius: 16px;
          border: 2px solid #EAE3D2;
          overflow: hidden;
          box-shadow: 0 10px 40px rgba(30, 34, 41, 0.12);
          display: flex;
          flex-direction: column;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .chat-box.hidden {
          opacity: 0;
          transform: translateY(20px) scale(0.95);
          pointer-events: none;
          display: none;
        }
        
        .chat-header {
          background: #1E3F2E;
          color: #FBF9F6;
          padding: 14px 18px;
          font-family: var(--font-fraunces), serif;
          font-size: 16px;
          font-weight: 700;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 2px solid #EAE3D2;
        }
        
        .header-buttons {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        
        .clear-button {
          background: transparent;
          color: #FBF9F6;
          opacity: 0.75;
          border: none;
          font-size: 11px;
          font-family: var(--font-plus-jakarta), sans-serif;
          font-weight: 700;
          text-transform: uppercase;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        
        .clear-button:hover {
          opacity: 1;
        }
        
        .close-button {
          background: transparent;
          color: #FBF9F6;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0.75;
          transition: opacity 0.2s;
        }
        
        .close-button:hover {
          opacity: 1;
        }
        
        .chat-body {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 12px;
          background: #FBF9F6;
          background-image: radial-gradient(#EAE3D2 1px, transparent 1px);
          background-size: 12px 12px;
        }
        
        .empty-chat {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #1E2229;
          opacity: 0.6;
          text-align: center;
          padding: 24px;
        }
        
        .message {
          max-width: 80%;
          padding: 10px 14px;
          border-radius: 12px;
          word-wrap: break-word;
          position: relative;
          font-size: 13px;
          line-height: 1.5;
        }
        
        .message.user {
          align-self: flex-end;
          background-color: #C85A32;
          color: #FFFFFF;
          border-bottom-right-radius: 2px;
          box-shadow: 0 2px 8px rgba(200, 90, 50, 0.15);
        }
        
        .message.bot {
          align-self: flex-start;
          background-color: #FFFFFF;
          color: #1E2229;
          border: 1px solid #EAE3D2;
          border-bottom-left-radius: 2px;
          box-shadow: 0 2px 8px rgba(30, 34, 41, 0.02);
        }
        
        .message.loading {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          background: transparent;
          border: none;
          box-shadow: none;
          color: #1E2229;
          opacity: 0.65;
        }
        
        .message-timestamp {
          font-size: 8px;
          opacity: 0.5;
          text-align: right;
          margin-top: 4px;
        }
        
        .chat-footer {
          background: #FFFFFF;
          padding: 12px;
          display: flex;
          gap: 8px;
          align-items: flex-end;
          border-top: 2px solid #EAE3D2;
        }
        
        .chat-input {
          flex: 1;
          border: 1px solid #EAE3D2;
          border-radius: 8px;
          padding: 8px 12px;
          font-size: 13px;
          resize: none;
          max-height: 80px;
          min-height: 20px;
          outline: none;
          background: #FBF9F6;
          color: #1E2229;
          transition: border-color 0.2s;
        }
        
        .chat-input:focus {
          border-color: #C85A32;
          background: #FFFFFF;
        }
        
        .button-group {
          display: flex;
          gap: 6px;
        }
        
        .voice-button, .pause-button, .send-button {
          background: #FBF9F6;
          border: 1px solid #EAE3D2;
          border-radius: 8px;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: #1E3F2E;
          transition: all 0.2s;
        }
        
        .voice-button:hover, .pause-button:hover, .send-button:hover {
          background: #EAE3D2;
          color: #C85A32;
        }
        
        .voice-button.listening {
          background: #EF4444;
          color: white;
          border-color: #EF4444;
          animation: pulse 1.5s infinite;
        }
        
        .send-button {
          background: #1E3F2E;
          color: #FBF9F6;
          border-color: #1E3F2E;
        }
        
        .send-button:hover {
          background: #2D5A43;
          color: white;
        }
        
        .send-button:disabled {
          background: #FBF9F6;
          color: #1E2229;
          opacity: 0.35;
          border-color: #EAE3D2;
          cursor: not-allowed;
        }
        
        .chat-toggle {
          background: #C85A32;
          color: white;
          border: 2px solid #EAE3D2;
          width: 52px;
          height: 52px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          box-shadow: 0 6px 20px rgba(200, 90, 50, 0.25);
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .chat-toggle:hover {
          background: #A54422;
          transform: scale(1.06) rotate(15deg);
        }
        
        .chat-toggle.hidden {
          display: none;
        }
        
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.08); }
          100% { transform: scale(1); }
        }
        
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 10s linear infinite;
        }
        
        @media (max-width: 480px) {
          .chat-box {
            width: calc(100vw - 32px);
            height: 60vh;
            bottom: 76px;
            right: 16px;
            position: fixed;
          }
        }
      `}</style>
    </div>
  );
}