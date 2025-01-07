from PIL import Image, ImageDraw, ImageFont
import os


class TitleCardGenerator:
    def __init__(self):
        self.card_width = 400
        self.card_height = 150
        self.background_color = (255, 255, 255)  # White
        self.text_color = (0, 0, 0)  # Black

        # Use Noto Color Emoji font for emojis
        self.emoji_font = ImageFont.truetype("NotoColorEmoji.ttf", 20)
        self.text_font = ImageFont.truetype("arial.ttf", 20)
        self.title_font = ImageFont.truetype("arial.ttf", 24)

    def create_title_card(self, title, username, emoji_badges):
        # Create base image with transparency
        image = Image.new('RGBA', (self.card_width, self.card_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw rounded rectangle for card background
        draw.rounded_rectangle(
            [(0, 0), (self.card_width, self.card_height)],
            radius=20,
            fill=(255, 255, 255, 230)
        )

        # Add username
        draw.text((20, 20), username, font=self.text_font, fill=self.text_color)

        # Add emoji badges using Noto Color Emoji font
        emoji_x = draw.textlength(username, font=self.text_font) + 30
        draw.text((emoji_x, 20), emoji_badges, font=self.emoji_font, fill=self.text_color)

        # Add title
        draw.text((20, 50), title, font=self.title_font, fill=self.text_color)

        # Add engagement metrics
        draw.text((20, 100), "❤️ 99+", font=self.emoji_font, fill=self.text_color)
        draw.text((100, 100), "💬 99+", font=self.emoji_font, fill=self.text_color)

        return image


def main():
    # Test parameters
    title = "Journey from Concept to AI-Fueled Launch: Secrets of LLM Mastery"
    username = "memenome"
    emoji_badges = "🎮🎲🎯✨🎪🎨🎭🎪🔥"

    # Create title card generator instance
    generator = TitleCardGenerator()

    # Generate the title card
    card = generator.create_title_card(title, username, emoji_badges)

    # Save the image
    output_path = "test_title_card.png"
    card.save(output_path)
    print(f"Title card saved as: {output_path}")


if __name__ == "__main__":
    main()
