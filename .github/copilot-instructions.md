# Copilot Instructions

## 🧠 General Behavior
- Follow instructions exactly as written in comments or prompts.
- Do not assume missing details — ask or leave TODOs if unsure.
- Prioritize simplicity, clarity, and readability of code.
- Use only the technologies, libraries, and patterns already used in this project unless explicitly told to add something new.
- Always specify the complete file path as to where to make changes, since the code base is huge.

## 🧹 Code Style
- Match the existing code style and formatting (indentation, naming, etc.).
- Use concise, meaningful variable and function names.
- Comment non-trivial logic with short, clear explanations.
- Avoid overly complex one-liners or unnecessary abstractions.

## 🛠️ Languages & Tools
- Language: **Python 3.10+**
- Frameworks: **FastAPI**, **SQLAlchemy**, **Pydantic**
- Database: **PostgreSQL**
- Testing: **Pytest**

## 🧪 Testing
- Always write corresponding unit tests when creating new functions or modules.
- Use mocks/stubs where necessary to isolate units.
- Follow the `tests/` directory structure and naming conventions.

## 📁 Project Structure Guidelines
- Organize by feature, not type (e.g. `user/handlers.py`, not `handlers/user.py`)
- Place new routes in `routes/`
- Place business logic in `services/`
- Place DB access logic in `repositories/`

## ❗Important Rules
- Never hardcode secrets, passwords, or API keys.
- Prefer environment variables and config files for sensitive settings.
- Do not write code that depends on global mutable state.
- Always validate input and handle errors gracefully.

## ✅ Example Task Prompt
> “Create a FastAPI route for user login, validate credentials from the DB using SQLAlchemy, and return a JWT token. Use services and repositories to keep logic modular.”

---

This will ensure GitHub Copilot (and even human contributors) follow consistent development patterns across your project.

---

Would you like a version for a **JavaScript/TypeScript** project or a **full-stack app**?
