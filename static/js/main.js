document.addEventListener('DOMContentLoaded', function() {
    const pdfForm = document.getElementById('pdf-upload-form');
    const pdfInput = document.getElementById('pdf-upload');
    const uploadStatus = document.getElementById('upload-status');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatWindow = document.getElementById('chat-window');

    // Helper to add chat bubble
    function addBubble(text, sender) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + sender;
        bubble.textContent = text;
        chatWindow.appendChild(bubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // PDF Upload
    pdfForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (!pdfInput.files.length) {
            uploadStatus.textContent = 'Please select a PDF file.';
            uploadStatus.style.color = '#ff0077';
            return;
        }
        const formData = new FormData();
        formData.append('pdf', pdfInput.files[0]);
        uploadStatus.textContent = 'Uploading...';
        uploadStatus.style.color = '#1561e8';
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                uploadStatus.textContent = 'PDF uploaded and processed!';
                uploadStatus.style.color = '#009bdf';
            } else {
                uploadStatus.textContent = data.error || 'Upload failed.';
                uploadStatus.style.color = '#ff0077';
            }
        })
        .catch(() => {
            uploadStatus.textContent = 'Upload failed.';
            uploadStatus.style.color = '#ff0077';
        });
    });

    // Chat
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;
        addBubble(message, 'user');
        userInput.value = '';
        addBubble('...', 'assistant'); // Loading indicator
        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        })
        .then(res => res.json())
        .then(data => {
            // Remove loading bubble
            const bubbles = chatWindow.getElementsByClassName('chat-bubble');
            if (bubbles.length) {
                const last = bubbles[bubbles.length - 1];
                if (last.classList.contains('assistant') && last.textContent === '...') {
                    chatWindow.removeChild(last);
                }
            }
            if (data.success) {
                addBubble(data.answer, 'assistant');
            } else {
                addBubble(data.error || 'Error occurred.', 'assistant');
            }
        })
        .catch(() => {
            // Remove loading bubble
            const bubbles = chatWindow.getElementsByClassName('chat-bubble');
            if (bubbles.length) {
                const last = bubbles[bubbles.length - 1];
                if (last.classList.contains('assistant') && last.textContent === '...') {
                    chatWindow.removeChild(last);
                }
            }
            addBubble('Network error. Please try again.', 'assistant');
        });
    });
}); 