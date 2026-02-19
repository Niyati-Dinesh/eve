import { useRef, useEffect, useState, useCallback } from "react";
import "./Dashboard.css";
import {
  Send,
  Paperclip,
  X,
  Plus,
  Loader2,
  Sidebar,
  LogOut,
  Trash2,
  Copy,
  Check,
  MessageSquareHeart,
  Star,
  ChevronDown,
} from "lucide-react";
import { Button } from "../ui/Button";
import { ScrollArea } from "../ui/Scroll-area";
import {
  HandIcon,
  ImageIcon,
  CodeIcon,
  FileIcon,
  DownloadIcon,
} from "@radix-ui/react-icons";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../ui/Sheet";

import { useAuth } from "../../context/AuthContext";
import { useChat } from "../../context/ChatContext";

const welcomeMessages = [
  "Ready to orchestrate intelligence?",
  "What task can I distribute for you today?",
  "Let's optimize your workflow together",
  "Your adaptive AI companion, at your service",
  "Seamless execution starts here",
  "Intelligence, distributed efficiently",
  "Master your tasks with precision",
  "Fault-tolerant intelligence awaits",
  "Let's build something remarkable",
  "Your orchestration engine is ready",
];

const quickActions = [
  {
    label: (
      <div className="flex">
        <HandIcon className="qicons mr-2 mt-0.5" /> Say Hi
      </div>
    ),
    prompt: "Hi!",
  },
  {
    label: (
      <div className="flex">
        <ImageIcon className="qicons mr-2 mt-0.5" /> Generate Image
      </div>
    ),
    prompt: "Generate an image of a sunset over mountains",
  },
  {
    label: (
      <div className="flex">
        <CodeIcon className="qicons mr-2 mt-0.5" /> Write Code
      </div>
    ),
    prompt: "Write a Python function to calculate fibonacci numbers",
  },
  {
    label: (
      <div className="flex">
        <FileIcon className="qicons mr-2 mt-0.5" /> Documentation
      </div>
    ),
    prompt: "Write documentation for a REST API login endpoint",
  },
];

function CopyButton({ text, className = "" }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (_) {}
  };
  return (
    <button
      className={`copy-btn ${className}`}
      onClick={handleCopy}
      title="Copy"
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
    </button>
  );
}

function FeedbackModal({ onClose, messageContent, conversationId }) {
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (rating === 0) {
      setError("Please select a rating.");
      return;
    }
    setSending(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/feedback/send", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rating,
          message,
          conversation_id: conversationId || null,
          ai_message_snippet: messageContent
            ? messageContent.slice(0, 200)
            : null,
        }),
      });
      if (!res.ok) throw new Error("Failed");
      setSent(true);
      setTimeout(onClose, 2000);
    } catch (_) {
      setError("Failed to send. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const labels = ["", "Poor", "Fair", "Good", "Great", "Excellent"];
  return (
    <div className="feedback-overlay" onClick={onClose}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        <button className="feedback-close" onClick={onClose}>
          <X size={15} />
        </button>
        {sent ? (
          <div className="feedback-sent">
            <div className="feedback-sent-icon">
              <Check size={22} style={{ color: "#ff14a5" }} />
            </div>
            <p>Feedback received</p>
            <span>Thanks for helping us improve E.V.E.</span>
          </div>
        ) : (
          <>
            <p className="feedback-label">Response quality</p>
            <h3 className="feedback-title">How did we do?</h3>
            <p className="feedback-subtitle">Your feedback helps us improve.</p>
            <div className="feedback-stars">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  className={`feedback-star ${s <= (hovered || rating) ? "active" : ""}`}
                  onMouseEnter={() => setHovered(s)}
                  onMouseLeave={() => setHovered(0)}
                  onClick={() => setRating(s)}
                  title={labels[s]}
                >
                  <Star
                    size={28}
                    strokeWidth={1.5}
                    fill={s <= (hovered || rating) ? "#ff14a5" : "none"}
                    stroke={
                      s <= (hovered || rating)
                        ? "#ff14a5"
                        : "rgba(255,255,255,0.2)"
                    }
                  />
                </button>
              ))}
            </div>
            <textarea
              className="feedback-textarea"
              placeholder="Anything else to share? (optional)"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
            />
            {error && <p className="feedback-error">{error}</p>}
            <button
              className="feedback-submit"
              onClick={handleSubmit}
              disabled={sending}
            >
              {sending ? (
                <Loader2 size={14} className="spin" />
              ) : (
                "Submit feedback"
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function MarkdownContent({ content }) {
  const parts = [];
  let lastIndex = 0;
  const codeBlockRegex = /```([\w]*)\n?([\s\S]*?)```/g;
  let match;
  while ((match = codeBlockRegex.exec(content)) !== null) {
    if (match.index > lastIndex)
      parts.push({
        type: "text",
        content: content.slice(lastIndex, match.index),
      });
    parts.push({ type: "code", lang: match[1], content: match[2] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < content.length)
    parts.push({ type: "text", content: content.slice(lastIndex) });

  const renderText = (text) => {
    const html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/^#### (.+)$/gm, "<b>$1</b>")
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      .replace(/\n/g, "<br/>");
    return (
      <div
        className="message-markdown"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  };

  if (parts.length === 0) return renderText(content);
  return (
    <div>
      {parts.map((part, i) =>
        part.type === "code" ? (
          <div key={i} className="code-block-wrapper">
            <div className="code-block-header">
              <span className="code-lang">{part.lang || "code"}</span>
              <CopyButton text={part.content} />
            </div>
            <pre>
              <code>{part.content}</code>
            </pre>
          </div>
        ) : (
          <div key={i}>{renderText(part.content)}</div>
        ),
      )}
    </div>
  );
}

function downloadFile(fileData) {
  try {
    const byteCharacters = atob(fileData.content);
    const bytes = new Uint8Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++)
      bytes[i] = byteCharacters.charCodeAt(i);
    const blob = new Blob([bytes], { type: fileData.mime_type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileData.filename;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (e) {
    console.error("Download failed", e);
  }
}

function MessageBubble({ message, conversationId }) {
  const isUser = message.type === "user";
  const isError = message.type === "error";
  const content = message.content ?? "";
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  const urlMatch =
    content.match(/(https?:\/\/[^\s]+\.(png|jpg|jpeg|gif|webp)[^\s]*)/i) ||
    (content.includes("pollinations.ai") &&
      content.match(/(https?:\/\/[^\s]+)/));
  const imageUrl = urlMatch ? urlMatch[1] : null;

  return (
    <>
      <div
        className={`message ${isUser ? "user-message" : isError ? "error-message" : "ai-message"}`}
      >
        <div className="message-content">
          {!isUser && (
            <div className="message-avatar ai-avatar">
              <img src="/eve.jpeg" alt="EVE" className="avatar-eve" />
            </div>
          )}
          <div className="message-bubble-wrapper">
            <div className="message-bubble">
              {imageUrl ? (
                <div>
                  <p className="image-label">Generated image:</p>
                  <img
                    src={imageUrl}
                    alt="Generated"
                    className="generated-image"
                    onError={(e) => {
                      e.target.style.display = "none";
                    }}
                  />
                </div>
              ) : isUser ? (
                <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{content}</p>
              ) : (
                <MarkdownContent content={content} />
              )}
              {message.file && (
                <button
                  className="download-btn"
                  onClick={() => downloadFile(message.file)}
                >
                  <DownloadIcon /> {message.file.filename}
                </button>
              )}
              <span className="message-time">{message.timestamp}</span>
            </div>
            <div
              className={`message-actions ${isUser ? "message-actions--user" : "message-actions--ai"}`}
            >
              <CopyButton text={content} />
              {!isUser && !isError && (
                <button
                  className="feedback-trigger-btn"
                  onClick={() => setFeedbackOpen(true)}
                  title="Give feedback"
                >
                  <MessageSquareHeart size={13} />
                </button>
              )}
            </div>
          </div>
          {isUser && (
            <div className="message-avatar user-avatar">
              <span className="avatar-text">You</span>
            </div>
          )}
        </div>
      </div>
      {feedbackOpen && (
        <FeedbackModal
          onClose={() => setFeedbackOpen(false)}
          messageContent={content}
          conversationId={conversationId}
        />
      )}
    </>
  );
}

// ─────────────── Dashboard ──────────────────────
export default function Dashboard() {
  const { user, signOut } = useAuth();
  const {
    messages,
    isLoading,
    hasStartedChat,
    conversations,
    conversationId,
    conversationsLoading,
    deletingIds,
    send,
    loadConversation,
    startNewConversation,
    removeConversation,
  } = useChat();

  const [inputValue, setInputValue] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [currentWelcome] = useState(
    () => welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)],
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [convLoading, setConvLoading] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  // Direct ref to the scrollable messages div (no Radix layer)
  const scrollRef = useRef(null);
  // Tracks whether the user just sent a message (so we always scroll down)
  const userJustSentRef = useRef(false);

  // Add/remove body class to hide footer while dashboard is mounted
  useEffect(() => {
    document.body.classList.add("dashboard-active");
    return () => document.body.classList.remove("dashboard-active");
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }, [inputValue]);

  // Scroll to bottom helper — operates directly on our div
  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, []);

  // Show/hide the scroll-to-bottom button based on scroll position
  useEffect(() => {
    if (!hasStartedChat) {
      setShowScrollBtn(false);
      return;
    }

    const el = scrollRef.current;
    if (!el) return;

    const check = () => {
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
      setShowScrollBtn(dist > 120);
    };

    
    check();
    el.addEventListener("scroll", check, { passive: true });
    return () => el.removeEventListener("scroll", check);
  }, [hasStartedChat]);

  
  useEffect(() => {
    if (!hasStartedChat) return;
    const el = scrollRef.current;
    if (!el) return;

    if (userJustSentRef.current) {
      // Always jump to bottom after user sends
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      userJustSentRef.current = false;
    } else {
      // For AI replies: only follow if already near bottom
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
      if (dist < 200) {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      }
    }
  }, [messages, isLoading, hasStartedChat]);

  const handleFileChange = (e) => {
    setUploadedFiles((prev) => [...prev, ...Array.from(e.target.files)]);
    e.target.value = "";
  };
  const removeFile = (idx) =>
    setUploadedFiles((prev) => prev.filter((_, i) => i !== idx));

  const handleSend = (e) => {
    e?.preventDefault();
    const text = inputValue.trim();
    if ((!text && uploadedFiles.length === 0) || isLoading) return;
    const files = [...uploadedFiles];
    setInputValue("");
    setUploadedFiles([]);
    userJustSentRef.current = true; // signal: always scroll after this send
    send(text, files);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const handleLoadConversation = useCallback(
    async (convId) => {
      setConvLoading(true);
      try {
        await loadConversation(convId);
      } finally {
        setConvLoading(false);
      }
      setSidebarOpen(false);
    },
    [loadConversation],
  );

  const handleDelete = useCallback(
    async (e, convId) => {
      e.stopPropagation();
      await removeConversation(convId);
    },
    [removeConversation],
  );

  return (
    <div className="dashboard-container">
      {/* ── Sidebar ── */}
      <div className="dashboard-header">
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="hamburger-btn">
              <Sidebar />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="chat-history-sidebar">
            <SheetHeader>
              <SheetTitle className="history-title">Chat History</SheetTitle>
            </SheetHeader>
            {user && (
              <div className="sidebar-user">
                <span className="sidebar-user-email">{user.email}</span>
                <button
                  className="sidebar-signout flex justify-between"
                  onClick={signOut}
                >
                  <LogOut className="w-4 h-3 mt-0.5 mr-1.5" /> Log out
                </button>
              </div>
            )}
            <button
              className="new-chat-btn"
              onClick={() => {
                startNewConversation();
                setSidebarOpen(false);
              }}
            >
              <Plus size={16} /> New conversation
            </button>
            <ScrollArea className="history-scroll">
              <div className="history-list">
                {conversationsLoading ? (
                  <div className="history-loading">
                    <span className="loading-dot" />
                    <span className="loading-dot" />
                    <span className="loading-dot" />
                  </div>
                ) : conversations.length === 0 ? (
                  <p className="history-empty">No conversations yet.</p>
                ) : (
                  conversations.map((conv) => (
                    <div
                      key={conv.conversation_id}
                      className={[
                        "history-item",
                        conv.conversation_id === conversationId
                          ? "history-item--active"
                          : "",
                        deletingIds.has(conv.conversation_id)
                          ? "history-item--deleting"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() =>
                        !deletingIds.has(conv.conversation_id) &&
                        handleLoadConversation(conv.conversation_id)
                      }
                    >
                      <div className="history-item-top">
                        <div className="history-item-title">
                          {conv.preview
                            ? conv.preview.slice(0, 48) +
                              (conv.preview.length > 48 ? "…" : "")
                            : "New conversation"}
                        </div>
                        <button
                          className="history-delete-btn"
                          onClick={(e) => handleDelete(e, conv.conversation_id)}
                          disabled={deletingIds.has(conv.conversation_id)}
                        >
                          {deletingIds.has(conv.conversation_id) ? (
                            <Loader2 size={13} className="spin" />
                          ) : (
                            <Trash2 size={13} />
                          )}
                        </button>
                      </div>
                      <div className="history-item-meta">
                        <span>
                          {new Date(conv.last_updated).toLocaleDateString(
                            "en-US",
                            { month: "short", day: "numeric" },
                          )}
                        </span>
                        <span className="history-item-count">
                          {conv.message_count} messages
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </SheetContent>
        </Sheet>
      </div>

      {/* ── Chat area ── */}
      <div className="chat-content">
        {convLoading ? (
          <div className="conv-loading-screen">
            <div className="conv-loading-dots">
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span className="loading-dot" />
            </div>
            <p className="conv-loading-text">Loading conversation…</p>
          </div>
        ) : !hasStartedChat ? (
          <div className="welcome-screen">
            <h1 className="welcome-text">
              Welcome to <span className="eve-gradient">E.V.E</span>
            </h1>
            <p className="welcome-subtitle">{currentWelcome}</p>
            <div className="video-container">
              <video
                className="agent-video"
                autoPlay
                loop
                muted
                playsInline
                src="/agent.mp4"
              />
            </div>
            <div className="quick-actions">
              {quickActions.map((qa, idx) => (
                <button
                  key={idx}
                  className="quick-action-chip"
                  onClick={() => {
                    setInputValue(qa.prompt);
                    textareaRef.current?.focus();
                  }}
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
         
          <div
            ref={scrollRef}
            className="messages-container"
          >
            <div className="messages-inner">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  conversationId={conversationId}
                />
              ))}
              {isLoading && (
                <div className="message ai-message">
                  <div className="message-content">
                    <div className="message-avatar ai-avatar">
                      <img src="/eve.jpeg" alt="EVE" className="avatar-eve" />
                    </div>
                    <div className="message-bubble loading-bubble">
                      <span className="loading-dot" />
                      <span className="loading-dot" />
                      <span className="loading-dot" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* ── Scroll-to-bottom button ── */}
      {hasStartedChat && showScrollBtn && (
        <button
          className="scroll-to-bottom-btn"
          onClick={scrollToBottom}
          title="Scroll to bottom"
        >
          <ChevronDown size={18} />
        </button>
      )}

      {/* ── File preview strip ── */}
      {uploadedFiles.length > 0 && (
        <div className="file-preview-strip">
          {uploadedFiles.map((file, idx) => (
            <div key={idx} className="file-chip">
              <span className="flex">
                <FileIcon className="mt-0.5 mr-1.5" /> {file.name} (
                {(file.size / 1024).toFixed(1)} KB)
              </span>
              <button
                className="file-chip-remove"
                onClick={() => removeFile(idx)}
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Input bar (fixed at bottom) ── */}
      <div className="input-area">
        <form onSubmit={handleSend} className="input-form">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
          <button
            type="button"
            className="attach-btn"
            onClick={() => fileInputRef.current?.click()}
          >
            <Paperclip size={18} />
          </button>
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder="Message E.V.E…"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="chat-input"
            data-testid="chat-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-button"
            disabled={
              isLoading || (!inputValue.trim() && uploadedFiles.length === 0)
            }
          >
            {isLoading ? (
              <Loader2 size={18} className="spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}