let recognition;
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US'; // You can change the language here
}

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Voice settings elements
    const genderSelect = document.getElementById('gender');
    const rateInput = document.getElementById('rate');
    const volumeInput = document.getElementById('volume');
    const rateValue = document.getElementById('rate-value');
    const volumeValue = document.getElementById('volume-value');

    // Add these new variables
    const micButton = document.getElementById('mic-button');
    let isRecording = false;

    // Add these near the top of your DOMContentLoaded function
    const botNameInput = document.getElementById('bot-name');
    const updateNameBtn = document.getElementById('update-name-btn');

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
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

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

            // Play audio response
            const audio = new Audio(`data:audio/mp3;base64,${data.audio}`);
            audio.play();

        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your message.', false);
        }
    }

    // Add this new function
    function toggleRecording() {
        if (!recognition) {
            alert('Speech recognition is not supported in your browser');
            return;
        }

        if (!isRecording) {
            // Start recording
            recognition.start();
            isRecording = true;
            micButton.classList.add('recording');
        } else {
            // Stop recording
            recognition.stop();
            isRecording = false;
            micButton.classList.remove('recording');
        }
    }

    // Add speech recognition event handlers
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        sendMessage();
    };

    recognition.onend = () => {
        isRecording = false;
        micButton.classList.remove('recording');
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        micButton.classList.remove('recording');
    };

    // Add click handler for mic button
    micButton.addEventListener('click', toggleRecording);

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // Add this function
    async function updateBotName() {
        const newName = botNameInput.value.trim();
        if (!newName) return;

        try {
            const response = await fetch('/update-name', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newName })
            });

            const data = await response.json();
            if (data.status === 'success') {
                addMessage(`My name has been updated to ${newName}!`, false);
            }
        } catch (error) {
            console.error('Error updating name:', error);
        }
    }

    // Add this event listener
    updateNameBtn.addEventListener('click', updateBotName);

    // Add this function to handle workspace clicks
    function openWorkspace(type) {
        fetch('/open-workspace', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ workspace: type })
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                window.open(data.url, '_blank');
            }
        })
        .catch(error => console.error('Error:', error));
    }
}); 