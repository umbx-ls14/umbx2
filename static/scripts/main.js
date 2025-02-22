document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('fileInput').files[0]);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showNotification('File uploaded successfully');
            setTimeout(() => window.location.reload(), 1000);
        }
    } catch (error) {
        showNotification('Upload failed');
    }
});

function copyDirectLink(link) {
    navigator.clipboard.writeText(link).then(() => {
        showNotification('Link copied to clipboard!');
    });
}

function showNotification(message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.classList.remove('notification-hidden');
    
    setTimeout(() => {
        notification.classList.add('notification-hidden');
    }, 3000);
}