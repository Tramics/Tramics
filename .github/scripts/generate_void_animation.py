import os
import math
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any

def get_contributions(username: str) -> List[Dict[str, Any]]:
    url = f"https://github-contributions-api.jogruber.de/v4/{username}"
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return []
    return response.json().get('contributions', [])

def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)

def lerp_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(color1[0] + (color2[0] - color1[0]) * t),
        int(color1[1] + (color2[1] - color1[1]) * t),
        int(color1[2] + (color2[2] - color1[2]) * t),
    )

def generate_shimmer_text_frame(text: str, font: ImageFont.FreeTypeFont, width: int, height: int, frame_num: int) -> Image.Image:
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    letter_spacing = 12
    
    char_widths = []
    for char in text:
        bbox = draw.textbbox((0, 0), char, font=font)
        char_widths.append(bbox[2] - bbox[0])
    
    total_text_width = sum(char_widths) + letter_spacing * (len(text) - 1)
    
    x_start = int((width - total_text_width) / 2)
    
    bbox_first = draw.textbbox((0, 0), text[0], font=font)
    text_h = bbox_first[3] - bbox_first[1]
    y = int((height - text_h) / 2)

    color_a = (157, 78, 221)
    color_b = (224, 170, 255)
    color_c = (151, 125, 255)

    current_x = x_start
    for i, char in enumerate(text):
        phase = (frame_num * 0.15) + (i * 0.8)
        wave = (math.sin(phase) + 1.0) / 2.0

        if wave < 0.5:
            color = lerp_color(color_a, color_b, wave * 2.0)
        else:
            color = lerp_color(color_b, color_c, (wave - 0.5) * 2.0)

        glow_alpha = int(180 + 75 * wave)

        draw.text((current_x - 1, y), char, fill=(*color, glow_alpha // 3), font=font)
        draw.text((current_x + 1, y), char, fill=(*color, glow_alpha // 3), font=font)
        draw.text((current_x, y), char, fill=(*color, glow_alpha), font=font)

        current_x += char_widths[i] + letter_spacing

    return img

def generate_shimmer_text_gif(text: str, output_path: str) -> None:
    scale = 2
    width = 600 * scale
    height = 120 * scale

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48 * scale)
    except IOError:
        font = ImageFont.load_default()

    total_frames = 60
    frames = []

    for frame_num in range(total_frames):
        frame = generate_shimmer_text_frame(text, font, width, height, frame_num)
        frames.append(frame)

    final_width = width // scale
    final_height = height // scale
    resized_frames = [img.resize((final_width, final_height), Image.Resampling.LANCZOS) for img in frames]

    resized_frames[0].save(
        output_path,
        save_all=True,
        append_images=resized_frames[1:],
        duration=70,
        loop=0,
        optimize=True
    )

def generate_void_gif(username: str) -> None:
    contributions = get_contributions(username)

    scale = 2
    cols = 53
    rows = 7
    cell_size = 12 * scale
    padding = 3 * scale
    margin_left = 40 * scale
    margin_right = 20 * scale
    margin_top = 60 * scale
    margin_bottom = 40 * scale

    width = cols * (cell_size + padding) + margin_left + margin_right
    height = rows * (cell_size + padding) + margin_top + margin_bottom

    base_colors = ['#1a0533', '#3c096c', '#5a189a', '#7b2cbf', '#9d4edd']

    all_cells = []
    for week in range(cols):
        for day in range(rows):
            x = week * (cell_size + padding) + margin_left
            y = day * (cell_size + padding) + margin_top
            all_cells.append((x, y))

    levels = [min(contributions[i].get('level', 0), 4) if i < len(contributions) else 0 for i in range(len(all_cells))]
    cell_colors = [base_colors[level] for level in levels]

    active_indices = [i for i in range(len(all_cells)) if levels[i] > 0]

    fragments = {}
    for i in active_indices:
        x, y = all_cells[i]
        cx = int(x + cell_size / 2)
        cy = int(y + cell_size / 2)
        
        num_frags = random.randint(4, 8)
        cell_frags = []
        
        for _ in range(num_frags):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            frag_size = cell_size * random.uniform(0.15, 0.35)
            
            cell_frags.append({
                'angle': angle,
                'speed': speed,
                'size': frag_size,
                'color': cell_colors[i]
            })
        
        fragments[i] = cell_frags

    frames = []

    try:
        font_labels = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10 * scale)
    except IOError:
        font_labels = ImageFont.load_default()

    def draw_labels(draw_obj: ImageDraw.ImageDraw) -> None:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        days = ['Mon', 'Wed', 'Fri']
        
        for i, month in enumerate(months):
            week_idx = int(i * (cols / 12))
            x = week_idx * (cell_size + padding) + margin_left
            draw_obj.text((x, margin_top - 20 * scale), month, fill=hex_to_rgba('#9d4edd', 200), font=font_labels)
        
        for i, day in enumerate(days):
            row_idx = [1, 3, 5][i]
            y = row_idx * (cell_size + padding) + margin_top + cell_size // 2 - 5 * scale
            draw_obj.text((10 * scale, y), day, fill=hex_to_rgba('#9d4edd', 200), font=font_labels)

    def draw_grid_with_fragments(draw_obj: ImageDraw.ImageDraw, progress: float, phase: str) -> None:
        for i in range(len(all_cells)):
            x, y = all_cells[i]
            
            if i not in active_indices:
                draw_obj.rectangle([int(x), int(y), int(x + cell_size), int(y + cell_size)], fill=cell_colors[i])
                continue
            
            if phase == 'stable':
                draw_obj.rectangle([int(x), int(y), int(x + cell_size), int(y + cell_size)], fill=cell_colors[i])
            elif phase == 'shatter':
                cx = int(x + cell_size / 2)
                cy = int(y + cell_size / 2)
                
                remaining_size = int(cell_size * (1 - progress))
                if remaining_size > 1:
                    half_rem = remaining_size // 2
                    draw_obj.rectangle([cx - half_rem, cy - half_rem, cx + half_rem, cy + half_rem], fill=cell_colors[i])
                
                for frag in fragments[i]:
                    dist = frag['speed'] * progress
                    fx = int(cx + math.cos(frag['angle']) * dist)
                    fy = int(cy + math.sin(frag['angle']) * dist)
                    
                    alpha = int(255 * (1 - progress * 0.7))
                    color = hex_to_rgba(frag['color'], alpha)
                    f_size = int(frag['size'])
                    half_f = f_size // 2
                    
                    draw_obj.rectangle([fx - half_f, fy - half_f, fx + half_f, fy + half_f], fill=color)
            elif phase == 'reassemble':
                cx = int(x + cell_size / 2)
                cy = int(y + cell_size / 2)
                
                for frag in fragments[i]:
                    max_dist = frag['speed']
                    dist = max_dist * (1 - progress)
                    fx = int(cx + math.cos(frag['angle']) * dist)
                    fy = int(cy + math.sin(frag['angle']) * dist)
                    
                    alpha = int(255 * (0.3 + 0.7 * progress))
                    color = hex_to_rgba(frag['color'], alpha)
                    f_size = int(frag['size'])
                    half_f = f_size // 2
                    
                    draw_obj.rectangle([fx - half_f, fy - half_f, fx + half_f, fy + half_f], fill=color)
                
                reform_size = int(cell_size * progress)
                if reform_size > 1:
                    half_ref = reform_size // 2
                    draw_obj.rectangle([cx - half_ref, cy - half_ref, cx + half_ref, cy + half_ref], fill=cell_colors[i])

    for frame_num in range(15):
        img = Image.new('RGBA', (width, height), hex_to_rgba('#0d1117', 255))
        draw = ImageDraw.Draw(img)
        draw_labels(draw)
        draw_grid_with_fragments(draw, 0.0, 'stable')
        frames.append(img)

    for frame_num in range(30):
        img = Image.new('RGBA', (width, height), hex_to_rgba('#0d1117', 255))
        draw = ImageDraw.Draw(img)
        draw_labels(draw)
        progress = (frame_num + 1) / 30.0
        draw_grid_with_fragments(draw, progress, 'shatter')
        frames.append(img)

    for frame_num in range(15):
        img = Image.new('RGBA', (width, height), hex_to_rgba('#0d1117', 255))
        draw = ImageDraw.Draw(img)
        draw_labels(draw)
        draw_grid_with_fragments(draw, 1.0, 'shatter')
        frames.append(img)

    for frame_num in range(30):
        img = Image.new('RGBA', (width, height), hex_to_rgba('#0d1117', 255))
        draw = ImageDraw.Draw(img)
        draw_labels(draw)
        progress = (frame_num + 1) / 30.0
        draw_grid_with_fragments(draw, progress, 'reassemble')
        frames.append(img)

    for frame_num in range(15):
        img = Image.new('RGBA', (width, height), hex_to_rgba('#0d1117', 255))
        draw = ImageDraw.Draw(img)
        draw_labels(draw)
        draw_grid_with_fragments(draw, 0.0, 'stable')
        frames.append(img)

    if frames:
        final_width = width // scale
        final_height = height // scale
        resized_frames = [img.resize((final_width, final_height), Image.Resampling.LANCZOS) for img in frames]
        resized_frames[0].save(
            'dist/void-animation.gif',
            save_all=True,
            append_images=resized_frames[1:],
            duration=80,
            loop=0,
            optimize=True
        )

if __name__ == "__main__":
    username = os.environ.get('GITHUB_USER', 'Tramics')
    os.makedirs('dist', exist_ok=True)
    generate_void_gif(username)
    generate_shimmer_text_gif("THE VOID", 'dist/void-text.gif')