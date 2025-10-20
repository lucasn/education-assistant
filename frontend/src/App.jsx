import { useState, useEffect, useRef, useCallback } from 'react'
import { handleKeyPress } from './utils'
import {
  PlusIcon,
  SendIcon,
  MessageIcon,
  MenuIcon,
  XIcon,
  AlertIcon
} from './components/icons';
import { MessageBubble } from './components/MessageBubble';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentThreadId, setCurrentThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [retrieveConversationsError, setRetrieveConversationsError] = useState(null);
  const apiUrl = import.meta.env.VITE_API_URL;
  const messagesEndRef = useRef(null);

  console.log(apiUrl)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchConversations = useCallback(async () => {
    try {
      setRetrieveConversationsError(null);
      const response = await fetch(`${apiUrl}/conversations`);

      console.log(response)

      if (!response.ok) {
        throw new Error(`Failed to load conversations: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.length != 0) {
        data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      }

      setConversations(data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setRetrieveConversationsError(error.message || 'Failed to load conversation history');
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const fetchConversation = async (threadId) => {
    const response = await fetch(`${apiUrl}/conversation/${threadId}`)

    if (!response.ok) {
      setMessages([{
        type: 'ai',
        content: 'Sorry, there was an error processing your request.',
      }]);
      throw new Error(`Failed to load conversation with threadId ${threadId}: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    const messages = data[0].messages.filter((m) => m.type === "human" || m.type == "ai" || m.type == "tool");

    setMessages(messages);
  }

  const createNewConversation = () => {
    const newThreadId = self.crypto.randomUUID();
    setCurrentThreadId(newThreadId);
    setMessages([]);
  };

  const selectConversation = (threadId) => {
    setCurrentThreadId(threadId);
    fetchConversation(threadId);
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { type: 'human', content: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    try {
      const threadId = currentThreadId || self.crypto.randomUUID();
      const response = await fetch(`${apiUrl}/ask_async`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          threadId: threadId,
          question: currentInput,
        }),
      });

      // const data = await response.json();

      if (!currentThreadId) {
        setCurrentThreadId(threadId);
      }

      let firstToken = true;
      let assistantMessage = {
        type: 'ai',
        content: '',
        additional_kwargs: { context: '' }
      };

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log('Stream complete');
          break;
        }

        // Decode the chunk
        const chunk = decoder.decode(value, { stream: true });

        // Parse SSE format (data: {...}\n\n)
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonData = line.slice(6); // Remove 'data: ' prefix
            try {
              const data = JSON.parse(jsonData);
              // console.log('Received:', data.content);
              if (data.content) {
                assistantMessage.content += data.content;
              }
              if (data.additional_kwargs) {
                assistantMessage.additional_kwargs.context = data.additional_kwargs.context;
                // console.log(data.additional_kwargs)
              }
              if (firstToken) {
                setMessages(prev => [...prev, assistantMessage]);
                firstToken = false;
              } else {
                setMessages(prev => [...prev.slice(0, prev.length - 1), assistantMessage]);
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }

      fetchConversation(threadId);
      // setMessages(prev => [...prev, assistantMessage]);
      fetchConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        type: 'ai',
        content: 'Sorry, there was an error processing your request.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <div className={`${sidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 bg-gray-950 border-r border-gray-800 flex flex-col overflow-hidden`}>
        <div className="p-4 border-b border-gray-800">
          <button
            onClick={createNewConversation}
            className="w-full flex items-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <PlusIcon />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {retrieveConversationsError ? (
            <div className="p-4">
              <div className="bg-red-900 bg-opacity-20 border border-red-800 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <AlertIcon />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-red-400 mb-1">Error Loading History</p>
                    <p className="text-xs text-red-300">{retrieveConversationsError}</p>
                    <button
                      onClick={fetchConversations}
                      className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No conversations yet
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.threadId}
                onClick={() => selectConversation(conv.threadId)}
                className={`w-full text-left px-4 py-3 rounded-lg mb-1 hover:bg-gray-800 transition-colors flex items-center gap-2 ${currentThreadId === conv.threadId ? 'bg-gray-800' : ''
                  }`}
              >
                <MessageIcon />
                <span className="truncate text-sm">{conv.title || conv.threadId}</span>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="bg-gray-950 border-b border-gray-800 p-4 flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            {sidebarOpen ? <XIcon /> : <MenuIcon />}
          </button>
          <h1 className="text-xl font-semibold">LLM Professor</h1>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="mx-auto mb-4 opacity-50" style={{ width: '48px', height: '48px' }}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                </div>
                <p className="text-lg">Start a conversation with your LLM Professor</p>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg, idx) => (
                msg.content && <MessageBubble idx={idx} message={msg} />
              ))}
              {loading && (
                <div className="flex gap-4 justify-start">
                  <div className="bg-gray-800 px-4 py-3 rounded-2xl">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="border-t border-gray-800 p-4 bg-gray-950">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-2 bg-gray-800 rounded-2xl p-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyUp={(e) => handleKeyPress(e, sendMessage)}
                placeholder="Ask your professor anything..."
                className="flex-1 bg-transparent px-3 py-2 focus:outline-none resize-none max-h-32"
                rows="1"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-xl transition-colors"
              >
                <SendIcon />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App
