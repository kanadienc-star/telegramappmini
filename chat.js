document.addEventListener("DOMContentLoaded", function() {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatMessages = document.getElementById("chat-messages");
  const typingIndicator = document.getElementById("typing-indicator");
  const sendButton = document.getElementById("send-button");

  // Scroll to bottom of chat
  function scrollToBottom() {
    const chatContainer = document.querySelector(".chat-container");
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  // Show typing indicator
  function showTypingIndicator() {
    typingIndicator.classList.remove("d-none");
    scrollToBottom();
  }

  // Hide typing indicator
  function hideTypingIndicator() {
    typingIndicator.classList.add("d-none");
  }

  // Add message to chat
  function addMessage(message, sender, isError = false) {
    const messageContainer = document.createElement("div");
    messageContainer.classList.add("message-container");
    
    if (sender === "user") {
      messageContainer.classList.add("user-message");
    } else {
      messageContainer.classList.add("ai-message");
    }
    
    if (isError) {
      messageContainer.classList.add("error-message");
    }

    const messageHTML = `
      <div class="message-bubble">
        <div class="message-text">${message}</div>
      </div>
      <div class="user-avatar ${sender}">
        <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
      </div>
    `;
    
    messageContainer.innerHTML = messageHTML;
    chatMessages.appendChild(messageContainer);
    scrollToBottom();
  }

  // Send message to server
  async function sendMessage(message) {
    showTypingIndicator();
    
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
      });
      
      hideTypingIndicator();
      
      const data = await response.json();
      
      if (response.ok) {
        addMessage(data.reply, "ai");
      } else {
        addMessage(data.error || "Произошла ошибка при обработке запроса.", "ai", true);
      }
    } catch (error) {
      hideTypingIndicator();
      addMessage("Не удалось соединиться с сервером. Проверьте подключение к интернету.", "ai", true);
      console.error("Error:", error);
    }
  }

  // Handle form submit
  chatForm.addEventListener("submit", function(event) {
    event.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    
    addMessage(message, "user");
    userInput.value = "";
    sendMessage(message);
  });

  // Focus input on page load
  userInput.focus();

  // Toggle send button state based on input
  userInput.addEventListener("input", function() {
    sendButton.disabled = !userInput.value.trim();
  });
  
  // Initialize button state
  sendButton.disabled = !userInput.value.trim();

  // Enable pressing Enter to send a message
  userInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (userInput.value.trim()) {
        chatForm.dispatchEvent(new Event("submit"));
      }
    }
  });

  // Auto-resize input field (optional)
  userInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
  });

  // Scroll to bottom on initial load
  scrollToBottom();
});
