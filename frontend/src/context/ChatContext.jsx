// context/ChatContext.jsx
// Changes from previous version:
//   • Added deletingIds state (Set) for delete slide-out animation
//   • removeConversation: marks ID as deleting immediately, waits 350ms then removes
//   • Everything else is identical

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import { sendMessage, getHistory, listConversations, deleteConversation } from "../api/tasks";
import { useAuth } from "./AuthContext";

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const { user } = useAuth();

  const [messages, setMessages]                         = useState([]);
  const [conversationId, setConversationId]             = useState(null);
  const [conversations, setConversations]               = useState([]);
  const [conversationsLoading, setConversationsLoading] = useState(false);
  const [isLoading, setIsLoading]                       = useState(false);
  const [hasStartedChat, setHasStartedChat]             = useState(false);
  const [deletingIds, setDeletingIds]                   = useState(new Set());

  const refreshConversations = useCallback(async () => {
    if (!user) { setConversations([]); return; }
    try {
      const data = await listConversations();
      setConversations(data.conversations || []);
    } catch (_) {}
  }, [user]);

  useEffect(() => {
    if (user) {
      setConversationsLoading(true);
      listConversations()
        .then((data) => setConversations(data.conversations || []))
        .catch(() => {})
        .finally(() => setConversationsLoading(false));
    } else {
      setConversations([]);
    }
  }, [user]);

  const loadConversation = useCallback(async (convId) => {
    try {
      const data = await getHistory(convId, 50);
      const loaded = (data.messages || []).map((m, i) => ({
        id: `hist-${convId}-${i}`,
        type: m.role === "user" ? "user" : "ai",
        content: m.content,
        timestamp: new Date(m.timestamp).toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      }));
      setMessages(loaded);
      setConversationId(convId);
      setHasStartedChat(loaded.length > 0);
    } catch (err) {
      console.error("Failed to load conversation:", err);
    }
  }, []);

  const send = useCallback(
    async (text, files = []) => {
      if ((!text.trim() && files.length === 0) || isLoading) return;

      const userMsg = {
        id: `user-${Date.now()}`,
        type: "user",
        content: files.length
          ? `${text}\n\n📎 Files: ${files.map((f) => f.name).join(", ")}`
          : text,
        timestamp: new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setHasStartedChat(true);
      setIsLoading(true);

      try {
        const data = await sendMessage(text, conversationId, files);

        const returnedId = data.conversation_id;
        if (returnedId && returnedId !== conversationId) {
          setConversationId(returnedId);
          refreshConversations();
        }

        let responseText = data.response || "";
        if (typeof responseText === "string") {
          responseText = responseText
            .replace(/\\n/g, "\n")
            .replace(/\\"/g, '"');
          if (responseText.includes("Heres the image:")) {
            responseText = responseText.replace("Heres the image:", "🎨 Generated image:");
          }
        }

        const aiMsg = {
          id: `ai-${Date.now()}`,
          type: "ai",
          content: responseText,
          timestamp: new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          file: data.file || null,
        };

        setMessages((prev) => [...prev, aiMsg]);
        refreshConversations();
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            type: "error",
            content: `❌ ${err.message}`,
            timestamp: new Date().toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, isLoading, refreshConversations]
  );

  // Delete with animation: add to deletingIds → CSS animates out → remove from list
  const removeConversation = useCallback(
    async (convId) => {
      // Immediately mark as deleting — CSS transition fires instantly
      setDeletingIds((prev) => new Set([...prev, convId]));

      try {
        await deleteConversation(convId);
      } catch (err) {
        // Revert on failure
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(convId);
          return next;
        });
        console.error("Failed to delete conversation:", err);
        return;
      }

      // Wait for CSS animation (350ms) then remove from list
      setTimeout(() => {
        setConversations((prev) =>
          prev.filter((c) => c.conversation_id !== convId)
        );
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(convId);
          return next;
        });
        if (convId === conversationId) {
          setMessages([]);
          setConversationId(null);
          setHasStartedChat(false);
        }
      }, 350);
    },
    [conversationId]
  );

  const startNewConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setHasStartedChat(false);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        conversationId,
        conversations,
        conversationsLoading,
        deletingIds,
        isLoading,
        hasStartedChat,
        send,
        loadConversation,
        startNewConversation,
        removeConversation,
        refreshConversations,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => useContext(ChatContext);