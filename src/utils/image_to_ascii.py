from io import BytesIO
import requests
from PIL import Image, ImageEnhance


def image_to_ascii(image_url: str, height: int = 40, width: int = 100) -> str:
    """Convert a remote image to ASCII art.

    Args:
        image_url: Direct URL to the image to convert.
        height: Target output height (rows) of the ASCII art.
        width: Target output width (columns) of the ASCII art.

    Returns:
        A newline-delimited string of ASCII art sized to ``height`` x ``width``.
        Returns an empty string on failure.

    Notes:
        - Uses high-quality LANCZOS resampling to preserve detail when resizing.
        - Converts to 8-bit grayscale and boosts contrast/brightness/sharpness
          to improve character distinction.
        - Maps darker pixels to denser characters; lighter pixels to sparser ones.
    """
    try:
        # Download image bytes (no auth assumed). Add a timeout if needed.
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download image: {response.status_code}")
        image = Image.open(BytesIO(response.content))

        # Resize image with better quality (preserves edges and detail)
        image = image.resize((width, height), Image.Resampling.LANCZOS)

        # Convert to grayscale (single channel: 0=black, 255=white)
        image = image.convert("L")

        # Character ramp from dense (left) to sparse (right). Trailing space is intentional.
        # Works on both dark and light backgrounds when mapping is inverted below.
        ascii_chars = "MNHQ$OC?7>!:-;. "

        # Boost local contrast/brightness/sharpness to enhance mid-tone separation
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)

        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.3)

        ascii_art = []
        for y in range(height):
            line = ""
            for x in range(width):
                pixel = image.getpixel((x, y))
                # Map: darker pixels -> lower grayscale -> higher density characters
                # Invert grayscale so 0 (black) selects first dense chars.
                char_index = int((255 - pixel) / 255 * (len(ascii_chars) - 1))
                line += ascii_chars[char_index]
            ascii_art.append(line)

        return "\n".join(ascii_art)

    except Exception as e:
        # Fail safely: return empty string so callers can handle gracefully
        print(f"Failed generate ascii art: {e}")
        return ""


if __name__ == "__main__":
    # test the function with the image url
    image_url = "https://github.com/Soumojit28.png"
    print(image_to_ascii(image_url))
