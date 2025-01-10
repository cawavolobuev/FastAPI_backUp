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
async function generateLicense() {
    const inputField = document.getElementById("license-string");
    const stringValue = inputField.value;

    if (!stringValue) {
        alert("Введите строку перед отправкой запроса.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/licenses/generate", {
            method: "POST",
            headers: {
                "accept": "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(stringValue),
        });

        if (!response.ok) {
            const error = await response.json();
            alert(`Ошибка генерации лицензии: ${error.detail || response.statusText}`);
            return;
        }

        const data = await response.json();
        const licenseKey = data.key;

        // Отображение всплывающего окна с ключом лицензии
        alert(`Ключ лицензии успешно сгенерирован: ${licenseKey}`);
    } catch (error) {
        console.error("Ошибка генерации лицензии:", error);
        alert("Не удалось сгенерировать лицензию. Проверьте настройки сервера.");
    }
}


async function downloadLicense() {
    const usernameField = document.getElementById("license-username");
    const username = usernameField.value;

    if (!username) {
        alert("Введите имя пользователя перед загрузкой лицензии.");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/licenses/download?username=${encodeURIComponent(username)}`, {
            method: "GET",
            headers: {
                "accept": "application/json",
            },
        });

        if (!response.ok) {
            if (response.status === 500) {
                alert("Пожалуйста, сначала сгенерируйте лицензию.");
            } else {
                alert(`Ошибка загрузки лицензии: ${response.statusText}`);
            }
            return;
        }

        // Получаем имя файла из заголовков ответа
        const disposition = response.headers.get("Content-Disposition");
        const filename = disposition ? disposition.split("filename=")[1] : `license_${username}.lic`;

        // Скачиваем файл
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        alert("Лицензия успешно загружена.");
    } catch (error) {
        console.error("Ошибка загрузки лицензии:", error);
        alert("Не удалось загрузить лицензию. Проверьте настройки сервера.");
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


function registerUser() {
    const username = document.getElementById("new-username").value;
    const password = document.getElementById("new-password").value;

    if (!username || !password) {
        alert("Введите имя пользователя и пароль!");
        return;
    }

    fetch("/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
    })
        .then((response) => {
            if (response.ok) {
                alert("Пользователь успешно зарегистрирован!");
                location.reload(); // Перезагрузка страницы для обновления списка пользователей
            } else {
                response.json().then((data) => {
                    alert(`Ошибка: ${data.detail}`);
                });
            }
        })
        .catch((error) => {
            console.error("Ошибка при регистрации:", error);
            alert("Произошла ошибка при регистрации!");
        });
}

document.getElementById("registerButton").addEventListener("click", () => {
    document.getElementById("user-modal").style.display = "block";
});
document.getElementById("close-modal").addEventListener("click", () => {
    document.getElementById("user-modal").style.display = "none";
});