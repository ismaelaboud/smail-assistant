function startChat() {
    document.getElementById('landing-page').style.display = 'none';
    document.getElementById('chat-app').style.display = 'flex';
    loadChatHistory();
}

let recognition;
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
}

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const micButton = document.getElementById('mic-button');
    let isRecording = false;

    // Voice settings elements
    const genderSelect = document.getElementById('gender');
    const rateInput = document.getElementById('rate');
    const volumeInput = document.getElementById('volume');
    const rateValue = document.getElementById('rate-value');
    const volumeValue = document.getElementById('volume-value');

    function updateVoiceSettings() {
        fetch('/update-voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                gender: genderSelect.value,
                rate: rateInput.value,
                volume: volumeInput.value
            })
        });
    }

    // Update display values and send settings to server
    rateInput.addEventListener('input', () => {
        rateValue.textContent = rateInput.value;
        updateVoiceSettings();
    });

    volumeInput.addEventListener('input', () => {
        volumeValue.textContent = volumeInput.value;
        updateVoiceSettings();
    });

    genderSelect.addEventListener('change', updateVoiceSettings);

    function addMessage(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        // Format the message if it's from the bot and contains formatting markers
        if (!isUser) {
            // Replace ### with section headers
            message = message.replace(/###\s*(.*?)\s*###/g, '<h3>$1</h3>');
            
            // Replace ** ** with bold text
            message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            // Convert bullet points
            message = message.replace(/####\s*(.*?)(?=####|$)/g, '<div class="section">$1</div>');
            message = message.replace(/\n-\s*(.*)/g, '<li>$1</li>');
            
            // Handle lists
            if (message.includes('<li>')) {
                message = message.replace(/((?:<li>.*<\/li>)+)/g, '<ul>$1</ul>');
            }
            
            messageDiv.innerHTML = message;
        } else {
            messageDiv.textContent = message;
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    const stopAudioButton = document.getElementById('stop-audio');
    let currentAudio = null;

    function playAudioResponse(audioBase64) {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
            stopAudioButton.style.display = 'none';
        }

        if (audioBase64) {
            currentAudio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
            
            currentAudio.onplay = () => {
                stopAudioButton.style.display = 'flex';
            };

            currentAudio.onended = () => {
                stopAudioButton.style.display = 'none';
                currentAudio = null;
            };

            currentAudio.play();
        }
    }

    stopAudioButton.addEventListener('click', () => {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
            stopAudioButton.style.display = 'none';
        }
    });

    // Update the sendMessage function to its original version
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        userInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            addMessage(data.text, false);

            if (data.audio) {
                playAudioResponse(data.audio);
            }

        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your message.', false);
        }
    }

    function toggleRecording() {
        if (!recognition) {
            alert('Speech recognition is not supported in your browser');
            return;
        }

        if (!isRecording) {
            // Request microphone permission explicitly
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(function(stream) {
                    recognition.start();
                    isRecording = true;
                    micButton.classList.add('recording');
                    userInput.placeholder = 'Listening...';
                    
                    // Add visual feedback
                    addMessage("Listening... Speak now", false);
                })
                .catch(function(err) {
                    console.error('Microphone access denied:', err);
                    addMessage("Please enable microphone access to use voice input", false);
                });
        } else {
            recognition.stop();
            isRecording = false;
            micButton.classList.remove('recording');
            userInput.placeholder = 'Type your message...';
        }
    }

    // Modified speech recognition handlers
    recognition.onstart = () => {
        console.log('Speech recognition started');
        userInput.placeholder = 'Listening...';
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        // Show the transcript in the input field
        userInput.value = finalTranscript || interimTranscript;

        // If we have a final transcript and it's not empty
        if (finalTranscript && finalTranscript.trim().length > 0) {
            sendMessage();
        }
    };

    recognition.onend = () => {
        console.log('Speech recognition ended');
        isRecording = false;
        micButton.classList.remove('recording');
        userInput.placeholder = 'Type your message...';
        
        // If no text was captured, provide feedback
        if (!userInput.value.trim()) {
            addMessage("I couldn't hear anything. Please try again.", false);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        micButton.classList.remove('recording');
        userInput.placeholder = 'Type your message...';
        
        let errorMessage;
        switch(event.error) {
            case 'no-speech':
                errorMessage = "No speech was detected. Please try again.";
                break;
            case 'audio-capture':
                errorMessage = "No microphone was found. Ensure it is plugged in and enabled.";
                break;
            case 'not-allowed':
                errorMessage = "Microphone access was denied. Please enable it in your browser settings.";
                break;
            case 'network':
                errorMessage = "Network error occurred. Please check your connection.";
                break;
            default:
                errorMessage = `Error: ${event.error}. Please try again.`;
        }
        addMessage(errorMessage, false);
    };

    micButton.addEventListener('click', toggleRecording);
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Add these at the top with other constants
    const toggleButton = document.getElementById('toggle-sidebar');
    const settingsPanel = document.querySelector('.settings-panel');
    let isSidebarVisible = true;

    // Add toggle functionality
    toggleButton.addEventListener('click', () => {
        isSidebarVisible = !isSidebarVisible;
        settingsPanel.classList.toggle('hidden');
        document.querySelector('.container').classList.toggle('sidebar-hidden');
        
        // Rotate toggle button icon
        toggleButton.querySelector('svg').style.transform = 
            isSidebarVisible ? 'rotate(0deg)' : 'rotate(180deg)';
        
        // Save preference
        localStorage.setItem('sidebarVisible', isSidebarVisible);
    });

    // Load saved preference
    const savedSidebarState = localStorage.getItem('sidebarVisible');
    if (savedSidebarState !== null) {
        isSidebarVisible = savedSidebarState === 'true';
        if (!isSidebarVisible) {
            settingsPanel.classList.add('hidden');
            document.querySelector('.container').classList.add('sidebar-hidden');
            toggleButton.querySelector('svg').style.transform = 'rotate(180deg)';
        }
    }

    // Update the usePrompt function
    function usePrompt(prompt) {
        const userInput = document.getElementById('user-input');
        userInput.value = prompt;
        userInput.focus();
        // Optional: Automatically send the message
        // sendMessage();
    }

    // Make sure usePrompt is accessible globally
    window.usePrompt = usePrompt;

    // Add this function to load chat history
    async function loadChatHistory() {
        if (!document.getElementById('chat-messages')) return;
        
        try {
            const response = await fetch('/get-chats');
            if (!response.ok) throw new Error('Failed to load chat history');
            
            const chats = await response.json();
            const chatMessages = document.getElementById('chat-messages');
            const historyList = document.getElementById('chat-history-list');
            
            // Clear existing history
            historyList.innerHTML = '';
            
            // Add chat history items
            chats.forEach(chat => {
                const historyItem = document.createElement('div');
                historyItem.className = 'chat-history-item';
                historyItem.innerHTML = `
                    <div class="chat-timestamp">${chat.timestamp}</div>
                    <div class="chat-preview">${chat.message}</div>
                `;
                
                // Add click handler to show full conversation
                historyItem.addEventListener('click', () => {
                    // Clear chat messages
                    chatMessages.innerHTML = '';
                    
                    // Add the selected conversation
                    const userDiv = document.createElement('div');
                    userDiv.className = 'message user-message';
                    userDiv.textContent = chat.message;
                    chatMessages.appendChild(userDiv);
                    
                    const botDiv = document.createElement('div');
                    botDiv.className = 'message bot-message';
                    botDiv.textContent = chat.response;
                    chatMessages.appendChild(botDiv);
                    
                    // Scroll to bottom
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                });
                
                historyList.appendChild(historyItem);
            });
            
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    // Add after your existing DOMContentLoaded event listener
    document.querySelectorAll('.sidebar-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            document.querySelectorAll('.sidebar-nav-btn').forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Hide all sections
            document.querySelectorAll('.sidebar-section').forEach(section => {
                section.style.display = 'none';
            });
            
            // Show the selected section
            const sectionId = btn.dataset.section + '-section';
            document.getElementById(sectionId).style.display = 'block';
            
            // Load chat history if that section is selected
            if (btn.dataset.section === 'chat-history') {
                loadChatHistory();
            }
        });
    });

    // Add this to your existing DOMContentLoaded event listener
    const voiceSettingsToggle = document.getElementById('voice-settings-toggle');
    const voiceSettingsContent = document.getElementById('voice-settings-content');

    voiceSettingsToggle.addEventListener('click', () => {
        voiceSettingsContent.classList.toggle('show');
        voiceSettingsToggle.classList.toggle('active');
    });

    // Close voice settings when clicking outside
    document.addEventListener('click', (e) => {
        if (!voiceSettingsToggle.contains(e.target) && 
            !voiceSettingsContent.contains(e.target)) {
            voiceSettingsContent.classList.remove('show');
            voiceSettingsToggle.classList.remove('active');
        }
    });
}); 