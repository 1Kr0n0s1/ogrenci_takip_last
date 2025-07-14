# Öğrenci Takip Sistemi (Cloud)

A student tracking application with a GUI built using CustomTkinter, interacting with a backend API.

## Setup

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd OgrenciTakipApp
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure the API URL:
   - Update the `API_URL` in `src/core/utilities.py` with your PythonAnywhere API endpoint.

4. Run the application:
   ```bash
   python run.py
   ```

## Project Structure

- `src/main.py`: Main application entry point, initializes the login window.
- `src/windows/`: Contains all window classes (Login, Register, Popups, etc.).
- `src/core/`: Core application logic and utilities.
- `run.py`: Script to start the application.

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies.

## Notes

- Ensure the backend API is running at the specified `API_URL`.
- The application supports light/dark themes and exports schedules as JPG/PDF.