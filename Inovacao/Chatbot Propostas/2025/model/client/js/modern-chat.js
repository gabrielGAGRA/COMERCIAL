/**
 * Modern ChatGPT Interface JavaScript
 * Improved version with better error handling, modern JS features, and cleaner code
 */

class ChatInterface {
    constructor() {
        this.currentChatId = this.getChatIdFromURL() || this.generateUUID();
        this.isGenerating = false;
        this.controller = null;
        this.conversationHistory = [];

        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
        this.loadConversationHistory();

        console.log('ChatGPT Interface initialized');
    }

    initializeElements() {
        this.messageBox = document.getElementById('messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.stopButton = document.querySelector('.stop_generating');
        this.modelSelect = document.getElementById('model');
        this.conversationsList = document.querySelector('.conversations-list');

        // Initialize markdown renderer
        this.markdown = window.markdownit({
            highlight: function (str, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(str, { language: lang }).value;
                    } catch (__) { }
                }
                return '';
            }
        });
    }

    setupEventListeners() {
        // Send button click
        this.sendButton?.addEventListener('click', () => this.handleSendMessage());

        // Enter key to send (Shift+Enter for new line)
        this.messageInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });

        // Stop generation button
        this.stopButton?.addEventListener('click', () => this.stopGeneration());

        // Auto-resize textarea
        this.messageInput?.addEventListener('input', () => this.resizeTextarea());

        // Model selection change
        this.modelSelect?.addEventListener('change', (e) => {
            this.saveSettings();
            console.log(`Model changed to: ${e.target.value}`);
        });

        // Theme change
        const themeInputs = document.querySelectorAll('input[name="theme"]');
        themeInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.setTheme(e.target.value);
                }
            });
        });
    }

    getChatIdFromURL() {
        const path = window.location.pathname;
        const match = path.match(/\/chat\/(.+)/);
        return match ? match[1] : null;
    }

    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    async handleSendMessage() {
        const message = this.messageInput.value.trim();

        if (!message || this.isGenerating) {
            return;
        }

        // Clear input and add to UI
        this.messageInput.value = '';
        this.resizeTextarea();

        // Add user message to conversation
        this.addMessageToUI('user', message);
        this.conversationHistory.push({ role: 'user', content: message });

        // Start generating response
        await this.generateResponse(message);
    }

    async generateResponse(message) {
        this.isGenerating = true;
        this.toggleGeneratingState(true);

        const assistantMessageId = this.addMessageToUI('assistant', '');
        let responseContent = '';

        try {
            this.controller = new AbortController();

            const response = await fetch('/api/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    model: this.getSelectedModel(),
                    conversation_history: this.conversationHistory.slice(-10), // Last 10 messages
                    stream: true
                }),
                signal: this.controller.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.error) {
                                throw new Error(data.error);
                            }

                            if (data.content) {
                                responseContent += data.content;
                                this.updateMessageContent(assistantMessageId, responseContent);
                            }

                            if (data.done) {
                                break;
                            }
                        } catch (e) {
                            if (line.slice(6).trim() !== '') {
                                console.error('Error parsing SSE data:', e);
                            }
                        }
                    }
                }
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Request was aborted');
                responseContent = '*Response generation was stopped.*';
            } else {
                console.error('Error generating response:', error);
                responseContent = `*Error: ${error.message}*`;
            }

            this.updateMessageContent(assistantMessageId, responseContent);
        } finally {
            // Add assistant response to conversation history
            if (responseContent.trim()) {
                this.conversationHistory.push({ role: 'assistant', content: responseContent });
            }

            this.isGenerating = false;
            this.toggleGeneratingState(false);
            this.saveConversation();
        }
    }

    addMessageToUI(role, content) {
        const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        messageElement.id = messageId;

        const avatar = role === 'user' ?
            '<img src="/assets/img/user.png" alt="User">' :
            '<img src="/assets/img/gpt.png" alt="Assistant">';

        messageElement.innerHTML = `
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content" data-role="${role}">
                ${role === 'user' ? this.escapeHtml(content) : this.markdown.render(content)}
            </div>
        `;

        this.messageBox?.appendChild(messageElement);
        this.scrollToBottom();

        return messageId;
    }

    updateMessageContent(messageId, content) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            const contentElement = messageElement.querySelector('.message-content');
            if (contentElement) {
                contentElement.innerHTML = this.markdown.render(content);
                this.highlightCode();
                this.scrollToBottom();
            }
        }
    }

    toggleGeneratingState(generating) {
        if (this.sendButton) {
            this.sendButton.disabled = generating;
        }

        if (this.stopButton) {
            this.stopButton.style.display = generating ? 'block' : 'none';
        }

        if (this.messageInput) {
            this.messageInput.disabled = generating;
        }
    }

    stopGeneration() {
        if (this.controller) {
            this.controller.abort();
            this.controller = null;
        }
    }

    resizeTextarea() {
        if (this.messageInput) {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
        }
    }

    scrollToBottom() {
        if (this.messageBox) {
            this.messageBox.scrollTop = this.messageBox.scrollHeight;
        }
    }

    highlightCode() {
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }

    getSelectedModel() {
        return this.modelSelect?.value || 'gpt-4o';
    }

    // Settings management
    saveSettings() {
        const settings = {
            model: this.getSelectedModel(),
            theme: this.getCurrentTheme()
        };
        localStorage.setItem('chatgpt-settings', JSON.stringify(settings));
    }

    loadSettings() {
        try {
            const settings = JSON.parse(localStorage.getItem('chatgpt-settings') || '{}');

            if (settings.model && this.modelSelect) {
                this.modelSelect.value = settings.model;
            }

            if (settings.theme) {
                this.setTheme(settings.theme);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    getCurrentTheme() {
        const checkedTheme = document.querySelector('input[name="theme"]:checked');
        return checkedTheme ? checkedTheme.value : 'dark';
    }

    setTheme(theme) {
        const themeInput = document.querySelector(`input[name="theme"][value="${theme}"]`);
        if (themeInput) {
            themeInput.checked = true;
            document.documentElement.className = theme;
            localStorage.setItem('theme', theme);
        }
    }

    // Conversation management
    saveConversation() {
        const conversation = {
            id: this.currentChatId,
            title: this.generateConversationTitle(),
            messages: this.conversationHistory,
            timestamp: new Date().toISOString()
        };

        localStorage.setItem(`chat-${this.currentChatId}`, JSON.stringify(conversation));
        this.updateConversationsList();
    }

    loadConversationHistory() {
        try {
            const conversation = JSON.parse(localStorage.getItem(`chat-${this.currentChatId}`) || 'null');

            if (conversation && conversation.messages) {
                this.conversationHistory = conversation.messages;

                // Render conversation history
                conversation.messages.forEach(msg => {
                    this.addMessageToUI(msg.role, msg.content);
                });
            }
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    }

    generateConversationTitle() {
        if (this.conversationHistory.length > 0) {
            const firstUserMessage = this.conversationHistory.find(msg => msg.role === 'user');
            if (firstUserMessage) {
                return firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
            }
        }
        return 'New Conversation';
    }

    updateConversationsList() {
        // Implementation for updating conversations list in sidebar
        // This would be called to refresh the conversations list
    }

    // New conversation
    startNewConversation() {
        this.currentChatId = this.generateUUID();
        this.conversationHistory = [];

        // Clear message box
        if (this.messageBox) {
            this.messageBox.innerHTML = '';
        }

        // Update URL
        history.pushState({}, '', `/chat/${this.currentChatId}`);

        console.log('Started new conversation:', this.currentChatId);
    }
}

// Initialize the chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new ChatInterface();
});

// Handle browser back/forward navigation
window.addEventListener('popstate', () => {
    location.reload();
});
