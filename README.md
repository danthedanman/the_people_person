# The People Person

An interactive mental health hotline simulation game where you step into the role of a counselor to converse with callers in crisis, powered by the OpenAI GPT language model and Pygame.

## Requirements
- Python 3.8 or later
- [pip](https://pip.pypa.io/en/stable/)

This project also depends on the following Python packages (see `requirements.txt`):
```
pygame
openai
pyperclip
```

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/danthedanman/the-people-person.git
   cd the-people-person
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Launching the Game
From the project root directory, run:
```bash
python src/main.py
```
This will open a Pygame window and prompt you to:
1. Enter your OpenAI API key (paste with **Ctrl+V** and then hit enter).
2. Enter your gameplay name and hit enter.

## How to Play
You act as a counselor on a suicide prevention hotline. Your goal is to listen, empathize, and help callers improve their mental health.  If a caller's health drops to 2 or below, you lose the caller and get -1 point.  If you can get your caller to 8 or above, you have saved your caller and get +1 point.  (The game won't tell you which one, it will just say "Generating new caller" and give you the next caller, but you'll see your score updated and get the idea.)

### User Interface
- **Score:** Tracks your performance across calls.
- **Mental Health Slider:** Visual indicator (1–10) of the caller's current state.
- **Notifications:** Brief pop-ups showing changes in mental health.
- **Chat Area:** Displays the most recent messages from the caller and from you.
- **Input Box:** Type your responses here.
- **Quit Button:** End the day and view the leaderboard.

### Controls
- **Type your response** in the input box.
- Press **Enter** to send your message.
- Press **Shift + Enter** to insert a new line.
- Click **Quit** (or close the window) to end the session and view high scores.

## High Scores & Leaderboard
- Player scores are saved in `high_scores.json` and updated when you finish a session.
- After quitting, a leaderboard of top players will be displayed.

## Configuration
- The default language model is set to `gpt-4o` in `src/game.py` (constant `DEFAULT_MODEL`).
- You must provide a valid OpenAI API key to play.

## Logging & Debugging
- Build and development logs are maintained in `build_log.md`.
