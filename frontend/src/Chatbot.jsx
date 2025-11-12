import { useState } from "react";

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const backendChatUrl = "http://loan-backend-route-loan-app.apps.asa-demo.7mhsq.gcp.redhatworkshops.io/chat";

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(backendChatUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();
      setMessages([...newMessages, { sender: "bot", text: data.response || "No response from model" }]);
    } catch (err) {
      setMessages([...newMessages, { sender: "bot", text: "⚠️ Error: could not reach backend." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.chatWrapper}>
      {!isOpen && (
        <button style={styles.fabButton} onClick={() => setIsOpen(true)}>
          💬
        </button>
      )}
      {isOpen && (
        <div style={styles.chatContainer}>
          <div style={styles.header}>
            <strong>Loan Assistant</strong>
            <button style={styles.closeBtn} onClick={() => setIsOpen(false)}>
              ✖
            </button>
          </div>
          <div style={styles.messagesBox}>
            {messages.map((msg, i) => (
              <div key={i} style={msg.sender === "user" ? styles.userMsg : styles.botMsg}>
                {msg.text}
              </div>
            ))}
          </div>
          <div style={styles.inputBox}>
            <input
              style={styles.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about loans..."
            />
            <button onClick={sendMessage} disabled={loading} style={styles.button}>
              {loading ? "..." : "➤"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  chatWrapper: {
    position: "fixed",
    bottom: "20px",
    right: "20px",
    zIndex: 1000,
  },
  fabButton: {
    background: "#007BFF",
    color: "white",
    border: "none",
    borderRadius: "50%",
    width: "60px",
    height: "60px",
    fontSize: "28px",
    cursor: "pointer",
    boxShadow: "0px 2px 8px rgba(0,0,0,0.3)",
  },
  chatContainer: {
    width: "300px",
    height: "400px",
    background: "#fff",
    border: "1px solid #ccc",
    borderRadius: "10px",
    boxShadow: "0px 4px 10px rgba(0,0,0,0.2)",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    background: "#007BFF",
    color: "white",
    padding: "10px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopLeftRadius: "10px",
    borderTopRightRadius: "10px",
  },
  closeBtn: {
    background: "transparent",
    border: "none",
    color: "white",
    fontSize: "16px",
    cursor: "pointer",
  },
  messagesBox: {
    flex: 1,
    overflowY: "auto",
    padding: "10px",
    background: "#f9f9f9",
  },
  inputBox: {
    display: "flex",
    borderTop: "1px solid #ddd",
    padding: "8px",
  },
  input: {
    flex: 1,
    padding: "6px",
    borderRadius: "5px",
    border: "1px solid #ccc",
  },
  button: {
    marginLeft: "5px",
    padding: "6px 10px",
    background: "#007BFF",
    color: "white",
    border: "none",
    borderRadius: "5px",
  },
  userMsg: {
    textAlign: "right",
    background: "#DCF8C6",
    padding: "6px",
    borderRadius: "8px",
    margin: "5px 0",
    alignSelf: "flex-end",
  },
  botMsg: {
    textAlign: "left",
    background: "#F1F0F0",
    padding: "6px",
    borderRadius: "8px",
    margin: "5px 0",
  },
};

