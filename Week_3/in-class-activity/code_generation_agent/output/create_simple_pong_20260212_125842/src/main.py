import streamlit as st
import numpy as np
import time
from PIL import Image, ImageDraw

class PongGame:
    def __init__(self):
        self.width = 400
        self.height = 300
        self.paddle_width = 10
        self.paddle_height = 60
        self.ball_size = 8
        self.reset_game()

    def reset_game(self):
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.ball_speed_x = 5 # Increased speed for better feel
        self.ball_speed_y = 5
        self.paddle1_y = self.height // 2 - self.paddle_height // 2
        self.paddle2_y = self.height // 2 - self.paddle_height // 2
        self.score1 = 0
        self.score2 = 0
        self.game_active = False

    def update(self, cmd):
        if not self.game_active:
            if cmd == 'start':
                self.game_active = True
            return

        # Simple Paddle Movement via Command string
        if 'w' in cmd and self.paddle1_y > 0:
            self.paddle1_y -= 15
        if 's' in cmd and self.paddle1_y < self.height - self.paddle_height:
            self.paddle1_y += 15

        # Ball movement logic
        self.ball_x += self.ball_speed_x
        self.ball_y += self.ball_speed_y

        # Ball collision with top and bottom
        if self.ball_y <= 0 or self.ball_y >= self.height - self.ball_size:
            self.ball_speed_y *= -1

        # Ball collision with paddles
        if (self.ball_x <= self.paddle_width and 
            self.paddle1_y <= self.ball_y <= self.paddle1_y + self.paddle_height):
            self.ball_speed_x *= -1
            self.ball_x = self.paddle_width

        # Simple AI for Player 2 (Right) since capturing 4 keys is hard in one input
        if self.ball_y > self.paddle2_y + self.paddle_height/2:
            self.paddle2_y += 3
        else:
            self.paddle2_y -= 3

        # Scoring
        if self.ball_x < 0:
            self.score2 += 1
            self.ball_x, self.ball_y = self.width//2, self.height//2
        if self.ball_x > self.width:
            self.score1 += 1
            self.ball_x, self.ball_y = self.width//2, self.height//2

    def render(self):
        img = Image.new('RGB', (self.width, self.height), color='black')
        draw = ImageDraw.Draw(img)
        # Paddles
        draw.rectangle([0, self.paddle1_y, self.paddle_width, self.paddle1_y + self.paddle_height], fill='white')
        draw.rectangle([self.width - self.paddle_width, self.paddle2_y, self.width, self.paddle2_y + self.paddle_height], fill='white')
        # Ball
        draw.ellipse([self.ball_x - 4, self.ball_y - 4, self.ball_x + 4, self.ball_y + 4], fill='white')
        return img

def main():
    st.set_page_config(page_title="Pong Game", page_icon="🏓")
    st.title("Streamlit Pong")

    # Persistent State
    if 'game' not in st.session_state:
        st.session_state.game = PongGame()

    # Controls
    cmd = st.text_input("Type 'w' (up), 's' (down), or 'start':").lower()
    
    # Update and Render
    st.session_state.game.update(cmd)
    
    col1, col2 = st.columns(2)
    col1.metric("Player 1", st.session_state.game.score1)
    col2.metric("Player 2 (AI)", st.session_state.game.score2)

    st.image(st.session_state.game.render(), use_container_width=True)

    # Auto-refresh
    time.sleep(0.1)
    st.rerun()

if __name__ == "__main__":
    main()