document.addEventListener("DOMContentLoaded", () => {
    const backupList = document.getElementById("backup-list");
    const registerForm = document.getElementById("register-form");
    const registerMessage = document.getElementById("register-message");

    // Handle registration form submission
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(registerForm);
        const username = formData.get("username");
        const password = formData.get("password");

        try {
            const response = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password }),
            });
            const result = await response.json();
            registerMessage.textContent = result.message;
        } catch (error) {
            registerMessage.textContent = "Ошибка регистрации.";
            console.error("Ошибка:", error);
        }
    });
});