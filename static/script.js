document.addEventListener('DOMContentLoaded', () => {
    const loginButton = document.getElementById('loginButton');
    const authSection = document.getElementById('auth-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const licensePage = document.getElementById('license-page');
    const licenseButton = document.getElementById('licenseButton');
    const registerButton = document.getElementById('registerButton');
    const modal = document.getElementById('user-modal');
    const overlay = document.getElementById('modal-overlay');
    const closeModalButton = document.getElementById('close-modal');
    const closeLicenseButton = document.getElementById('close-license');
    const activateModal = document.getElementById('activate-modal');
    const closeActivateModal = document.getElementById('close-activate-modal');
    const usersDisplay = document.getElementById('users-display');


    dashboardSection.style.display = 'none';
    licensePage.style.display = 'none';

    loginButton.addEventListener('click', () => {
        const login = document.getElementById('login').value;
        const password = document.getElementById('password').value;

        if (login === 'admin' && password === 'admin') {
            authSection.style.display = 'none';
            dashboardSection.style.display = 'block';
            usersDisplay.style.display = 'block';
            loadUsers();
        } else {
            alert('Invalid login or password');
        }
    });

    licenseButton.addEventListener('click', () => {
        dashboardSection.style.display = 'none';
        licensePage.style.display = 'block';
    });

    closeLicenseButton.addEventListener('click', () => {
        licensePage.style.display = 'none';
        dashboardSection.style.display = 'block';
    });

    registerButton.addEventListener('click', () => {
        modal.classList.add('active');
        overlay.classList.add('active');
    });

    closeModalButton.addEventListener('click', () => {
        modal.classList.remove('active');
        overlay.classList.remove('active');
    });

    overlay.addEventListener('click', () => {
        modal.classList.remove('active');
        overlay.classList.remove('active');
        activateModal.classList.remove('active');
    });
    closeActivateModal.addEventListener('click', () => {
        activateModal.classList.remove('active');
        overlay.classList.remove('active');
    });

});

registerButton.addEventListener('click', () => {
    const username = document.getElementById('new-username').value;
    const password = document.getElementById('new-password').value;

    if (username && password) {
        fetch('http://127.0.0.1:8000/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => {
            if (response.ok) {
                alert('User registered successfully');
                document.getElementById('new-username').value = '';
                document.getElementById('new-password').value = '';
                loadUsers();
            } else {
                alert('Failed to register user');
            }
        })
        .catch(err => alert('Error: ' + err));
    } else {
        alert('Please fill in both fields');
    }
});

function loadUsers() {
    fetch('http://127.0.0.1:8000/users')
        .then(response => response.json())
        .then(data => {
            const usersDisplay = document.getElementById('users-display');
            usersDisplay.innerHTML = '<strong>Зарегистрированные пользователи:</strong><br>';
            data.users.forEach(user => {
                const userElement = document.createElement('div');
                userElement.textContent = user.username;
                usersDisplay.appendChild(userElement);
            });

            const userList = document.getElementById('user-list');
            userList.style.display = 'block';
            const userListUl = userList.querySelector('ul');
            userListUl.innerHTML = '';
            data.users.forEach(user => {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.href = `/user/${user.id}`;
                link.textContent = user.username;
                li.appendChild(link);
                userListUl.appendChild(li);
            });
        })
        .catch(err => console.error('Error loading users:', err));
}
function generateLicense() {
    const username = document.getElementById('license-username').value;

    if (username) {
        const licenseContent = `License for user: ${username}`;
        const blob = new Blob([licenseContent], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${username}-license.exe`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        alert('License generated and downloaded!');
    } else {
        alert('Please enter a username');
    }
}

function activateLicense() {
    const username = document.getElementById('activate-username').value;

    if (username) {
        const licenseContent = `Activated license for user: ${username}`;
        const blob = new Blob([licenseContent], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${username}-activated-license.exe`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        alert('License activated and downloaded!');
        document.getElementById('activate-username').value = '';
    } else {
        alert('Please enter a username');
    }
}