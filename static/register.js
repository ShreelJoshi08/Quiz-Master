function togglePassword(fieldId, button) {
    const passwordField = document.getElementById(fieldId);
    const icon = button.querySelector('i');
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        icon.classList.remove('bi-eye-fill');
        icon.classList.add('bi-eye-slash-fill');
    } else {
        passwordField.type = 'password';
        icon.classList.remove('bi-eye-slash-fill');
        icon.classList.add('bi-eye-fill');
    }
}

// In your login.html or login.js
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value
    };
    const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const result = await response.json();
    if (response.ok) {
        alert('Login successful!');
        // Redirect or handle login
    } else {
        alert(result.error || 'Login failed');
    }
});