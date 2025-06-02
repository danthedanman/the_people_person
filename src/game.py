"""
Game logic for The People Person
"""
import os
import sys
import json
import openai
import pygame
import asyncio
from agents import Agent, Runner

# Default LLM model
DEFAULT_MODEL = "gpt-4o"

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap text into lines that fit within max_width using the given font."""
    words = text.split(' ')
    lines: list[str] = []
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wrap text into lines that fit within max_width using the given font."""
    words = text.split(' ')
    lines: list[str] = []
    current = ''
    for word in words:
        test = (current + ' ' + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

class Game:
    # Path to high scores file (persisted across runs)
    HIGH_SCORES_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'high_scores.json'
    )

    def __init__(self, api_key, player_name):
        # Configure OpenAI
        openai.api_key = api_key
        self.api_key = api_key
        self.player_name = player_name
        self.score = 0
        # Load existing high scores
        self.high_scores = self.load_high_scores()
        self.player_best_score = self.high_scores.get(player_name, 0)
        # References set from main
        self.screen = None
        self.clock = None
        # Fonts will be initialized in run()
        self.font_small = None
        self.font_medium = None
        # UI state: track last messages and notifications
        self.last_caller_text = ""
        self.last_player_text = ""
        self.notifications: list[dict] = []
        # Initialize previous health score for delta calculations
        self.prev_health_score = 5

    def load_high_scores(self):
        """Load high scores from disk, return dict mapping names to scores."""
        try:
            with open(self.HIGH_SCORES_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_high_scores(self):
        """Save updated high scores to disk."""
        # Update this player's high score if current score is higher
        if self.score > self.high_scores.get(self.player_name, 0):
            self.high_scores[self.player_name] = self.score
        with open(self.HIGH_SCORES_FILE, 'w') as f:
            json.dump(self.high_scores, f, indent=4)
    def add_notification(self, delta: int):
        """Add a fading notification for mental health change."""
        text = f"+{delta}" if delta > 0 else str(delta)
        self.notifications.append({'text': text, 'alpha': 255})

    def generate_personality(self):
        """Generate a one-paragraph personality for a suicidal hotline caller using Agent SDK."""
        prompt = (
            "Generate a one-paragraph personality description for a person "
            "calling a suicide hotline. Include their background, age, "
            "emotional state, and reasons they might be feeling distressed."
        )
        personality_agent = Agent(
            name="PersonalityGenerator",
            instructions="You are an expert in human behavior.",
            model=DEFAULT_MODEL
        )
        result = asyncio.run(Runner.run(personality_agent, prompt))
        return result.final_output.strip()

    def get_initial_caller(self, personality):
        """Start conversation by having caller speak first using Agent SDK."""
        instructions = (
            f"You are a suicidal hotline caller. Here is your personality: {personality}. "
            "Begin the conversation by expressing your feelings and asking for help."
        )
        start_agent = Agent(
            name="InitialCaller",
            instructions=instructions,
            model=DEFAULT_MODEL
        )
        result = asyncio.run(Runner.run(start_agent, ""))
        return result.final_output.strip()

    def get_caller_response(self, user_input, personality, chat_history):
        """Get the caller's next response based on conversation history using Agent SDK."""
        # Build conversation context text
        history_text = "".join(
            f"{speaker}: {msg}\n" for speaker, msg in chat_history
        )
        instructions = (
            f"You are a suicidal hotline caller. Here is your personality: {personality}. "
            "Given the conversation so far below and the counselor's latest message, respond as the caller in character."
        )
        # Combine conversation context and latest counselor message as input
        full_input = history_text + f"Counselor: {user_input}"
        conv_agent = Agent(
            name="CallerAgent",
            instructions=instructions,
            model=DEFAULT_MODEL
        )
        result = asyncio.run(Runner.run(conv_agent, full_input))
        return result.final_output.strip()

    def score_mental_health(self, chat_history):
        """Assess caller's mental health on a scale of 1-10 using Agent SDK."""
        # Build conversation context text from the last up to 3 messages
        snippet = chat_history[-3:]
        conv_text = "".join(
            f"{speaker}: {msg}\n" for speaker, msg in snippet
        )
        instructions = (
            "You are a mental health assessor. You will be given a conversation between a caller and a counselor in the input. "
            "Rate the caller's current mental health on a scale of 1 to 10, where 1 is very low and 10 is perfectly healthy. Respond with only the integer."
        )
        scoring_agent = Agent(
            name="MentalHealthAssessor",
            instructions=instructions
        )
        result = asyncio.run(Runner.run(scoring_agent, conv_text))
        content = result.final_output.strip()
        digits = ''.join(ch for ch in content if ch.isdigit())
        try:
            val = int(digits)
            return max(1, min(10, val))
        except ValueError:
            return 5

    def render_ui(self, input_text):
        """Render the game UI: background, chat, health, input box, quit button."""
        # Fetch screen dimensions
        w = self.screen.get_width()
        h = self.screen.get_height()
        # Draw placeholder background
        self.screen.blit(self.background, (0, 0))
        # Draw header panel
        self.screen.blit(self.header_panel, (0, 0))
        # Score display
        score_surf = self.font_medium.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_surf, (20, 15))
        # Mental health display
        health_surf = self.font_medium.render(
            f"Mental Health: {self.current_health_score}", True, (255, 255, 255)
        )
        self.screen.blit(health_surf, (220, 15))
        # Quit button
        quit_rect = pygame.Rect(w - 100, 15, 80, 30)
        pygame.draw.rect(self.screen, (200, 0, 0), quit_rect)
        quit_surf = self.font_small.render("Quit", True, (255, 255, 255))
        self.screen.blit(quit_surf, (quit_rect.x + 20, quit_rect.y + 5))
        self.quit_rect = quit_rect

        # Draw mental health slider
        header_h = self.header_panel.get_height()
        slider_x = 20
        slider_y = header_h + 10
        slider_width = w - 40
        slider_height = 10
        # Slider background
        pygame.draw.rect(
            self.screen,
            (100, 100, 100),
            (slider_x, slider_y, slider_width, slider_height)
        )
        # Slider fill based on health (1-10)
        fill_w = int((self.current_health_score - 1) / 9 * slider_width)
        pygame.draw.rect(
            self.screen,
            (0, 200, 0),
            (slider_x, slider_y, fill_w, slider_height)
        )
        # Draw notifications
        for notif in list(self.notifications):
            notif_surf = self.font_medium.render(notif['text'], True, (255, 255, 0))
            notif_surf.set_alpha(notif['alpha'])
            nx = w // 2 - notif_surf.get_width() // 2
            ny = slider_y - notif_surf.get_height() - 5
            self.screen.blit(notif_surf, (nx, ny))
            notif['alpha'] -= 4
            if notif['alpha'] <= 0:
                self.notifications.remove(notif)

        # Conversation area: show only latest caller and player messages
        header_h = self.header_panel.get_height()
        input_h = self.input_panel.get_height()
        region_start_y = header_h + slider_height + 20
        region_end_y = h - input_h - 20
        region_height = region_end_y - region_start_y
        mid_y = region_start_y + region_height // 2
        max_text_width = w - 60
        # Caller message in top half
        if self.last_caller_text:
            pref = "Caller: " + self.last_caller_text
            lines = wrap_text(pref, self.font_small, max_text_width)
            y = region_start_y
            for line in lines:
                surf = self.font_small.render(line, True, (240, 240, 240))
                self.screen.blit(surf, (30, y))
                y += surf.get_height() + 2
        # Player message in bottom half
        if self.last_player_text:
            pref2 = f"{self.player_name}: " + self.last_player_text
            lines2 = wrap_text(pref2, self.font_small, max_text_width)
            y2 = mid_y
            for line in lines2:
                surf = self.font_small.render(line, True, (200, 200, 255))
                self.screen.blit(surf, (30, y2))
                y2 += surf.get_height() + 2
        # Draw input panel
        self.screen.blit(self.input_panel, (20, h - self.input_panel.get_height()))
        # Input area
        input_h = self.input_panel.get_height()
        input_rect = pygame.Rect(
            20,
            h - input_h + 5,
            w - 40,
            input_h - 10
        )
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect, 2)
        # Render multi-line input text with wrapping
        raw_lines = input_text.split('\n')
        wrapped_lines: list[str] = []
        max_width = input_rect.width - 10
        for line in raw_lines:
            wrapped_lines.extend(wrap_text(line, self.font_small, max_width))
        # Only display the bottom-most lines that fit
        line_height = self.font_small.get_height() + 2
        max_lines = input_rect.height // line_height
        display_lines = wrapped_lines[-max_lines:]
        for idx, line in enumerate(display_lines):
            txt_surf = self.font_small.render(line, True, (255, 255, 255))
            self.screen.blit(
                txt_surf,
                (
                    input_rect.x + 5,
                    input_rect.y + 5 + idx * line_height
                )
            )

    def get_player_input(self):
        """Handle text input and detect quit button."""
        input_text = ''
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_high_scores()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.quit_rect.collidepoint(event.pos):
                        return None
                if event.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    if event.key == pygame.K_RETURN:
                        # Shift+Enter for newline, Enter alone to submit
                        if mods & pygame.KMOD_SHIFT:
                            input_text += '\n'
                        else:
                            return input_text
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode
            self.render_ui(input_text)
            pygame.display.flip()
            self.clock.tick(30)

    def show_leaderboard(self):
        """Display the leaderboard until user exits."""
        sorted_scores = sorted(
            self.high_scores.items(), key=lambda x: x[1], reverse=True
        )
        while True:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    pygame.quit()
                    sys.exit()
            self.screen.fill((0, 0, 0))
            title = self.font_medium.render("Leaderboard", True, (255, 255, 255))
            self.screen.blit(title, (300, 50))
            y = 120
            for name, sc in sorted_scores[:10]:
                line = f"{name}: {sc}"
                surf = self.font_small.render(line, True, (255, 255, 255))
                self.screen.blit(surf, (300, y))
                y += 30
            pygame.display.flip()
            self.clock.tick(30)

    def run(self):
        """Main game loop: handles calls, conversation, and scoring using Agent SDK."""
        # Initialize fonts
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)

        # Initialize placeholder panels
        w, h = self.screen.get_size()
        self.background = pygame.Surface((w, h))
        self.background.fill((20, 20, 40))
        header_h = 60
        self.header_panel = pygame.Surface((w, header_h))
        self.header_panel.fill((50, 50, 70))
        chat_h = h - header_h - 100
        self.chat_panel = pygame.Surface((w - 40, chat_h))
        self.chat_panel.fill((30, 30, 50))
        self.input_panel = pygame.Surface((w - 40, 80))
        self.input_panel.fill((40, 40, 60))

        # Game state
        # Initialize last messages and health state
        self.last_caller_text = ""
        self.last_player_text = ""
        self.current_health_score = 5
        # prev_health_score initialized in __init__

        # Loop over calls
        while True:
            # Show loading indicator while generating new caller
            self.screen.blit(self.background, (0, 0))
            self.screen.blit(self.header_panel, (0, 0))
            loading_text = "Generating new caller..."
            load_surf = self.font_medium.render(loading_text, True, (255, 255, 255))
            self.screen.blit(load_surf, (
                w // 2 - load_surf.get_width() // 2,
                h // 2 - load_surf.get_height() // 2
            ))
            pygame.display.flip()
            self.clock.tick(30)
            # 1. Generate new caller personality
            personality = self.generate_personality()
            # Reset last messages for new call
            self.last_caller_text = ""
            self.last_player_text = ""

            # 2. Initial caller message
            first_text = self.get_initial_caller(personality)
            # Track chat history for LLM
            chat_history = [("Caller", first_text)]
            # Update UI
            self.last_caller_text = first_text

            # 3. Score initial mental health
            mh = self.score_mental_health(chat_history)
            # Show delta notification
            delta = mh - self.prev_health_score
            self.add_notification(delta)
            self.prev_health_score = mh
            self.current_health_score = mh

            # Immediate termination
            if self.current_health_score <= 2:
                self.score -= 1
                continue
            if self.current_health_score >= 8:
                self.score += 1
                continue

            # 4. Conversation loop
            while True:
                # Get player input (blocking until Enter)
                user_input = self.get_player_input()
                if user_input is None:
                    # Exit game
                    self.save_high_scores()
                    self.show_leaderboard()
                # Record and display player message immediately
                self.last_player_text = user_input
                chat_history.append(("You", user_input))
                # Show 'Thinking...' for caller
                self.last_caller_text = "Thinking..."
                # Render updated UI
                self.render_ui("")
                pygame.display.flip()
                self.clock.tick(30)
                # Get caller response
                caller_text = self.get_caller_response(user_input, personality, chat_history)
                self.last_caller_text = caller_text
                chat_history.append(("Caller", caller_text))
                # Update mental health
                mh = self.score_mental_health(chat_history)
                delta = mh - self.prev_health_score
                self.add_notification(delta)
                self.prev_health_score = mh
                self.current_health_score = mh
                # Check for call end
                if self.current_health_score <= 2:
                    self.score -= 1
                    break
                if self.current_health_score >= 8:
                    self.score += 1
                    break
                    break