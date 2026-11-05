"""
Generates ultra-high quality 1080x1920 (9:16) viral TikTok graphics for the campaign.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper
from bidi.algorithm import get_display
import os

def render_arabic(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def create_gradient(width, height, c1, c2, c3):
    base = Image.new("RGBA", (width, height), c1)
    top = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(top)
    for y in range(height):
        ratio = y / height
        if ratio < 0.5:
            local_ratio = ratio * 2
            r = int(c1[0] + (c2[0] - c1[0]) * local_ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * local_ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * local_ratio)
        else:
            local_ratio = (ratio - 0.5) * 2
            r = int(c2[0] + (c3[0] - c2[0]) * local_ratio)
            g = int(c2[1] + (c3[1] - c2[1]) * local_ratio)
            b = int(c2[2] + (c3[2] - c2[2]) * local_ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    return top

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def generate_tiktok_cover():
    W, H = 1080, 1920
    # Background gradient: Dark slate to deep purple/midnight
    bg = create_gradient(W, H, (10, 15, 29), (15, 23, 42), (30, 27, 75))
    
    # Ambient glows
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([(-100, 200), (500, 800)], fill=(37, 99, 235, 90))
    glow_draw.ellipse([(600, 1100), (1200, 1700)], fill=(168, 85, 247, 80))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    bg = Image.alpha_composite(bg, glow)
    
    draw = ImageDraw.Draw(bg)
    
    font_bold = "C:/Windows/Fonts/segoeuib.ttf"
    font_arial = "C:/Windows/Fonts/arialbd.ttf"
    
    # Fonts
    f_badge = ImageFont.truetype(font_arial, 34)
    f_hook = ImageFont.truetype(font_arial, 70)
    f_sub = ImageFont.truetype(font_arial, 42)
    f_code = ImageFont.truetype(font_bold, 48)
    f_arabic = ImageFont.truetype(font_arial, 52)
    f_btn = ImageFont.truetype(font_arial, 46)
    
    # 1. Top Category Pill
    draw_rounded_rect(draw, [W//2 - 250, 160, W//2 + 250, 230], radius=35, fill=(30, 41, 59, 220), outline=(59, 130, 246), width=3)
    pill_text = render_arabic("⚠️ مشكلة كل مستخدمي الكمبيوتر")
    draw.text((W//2, 195), pill_text, font=f_badge, fill=(56, 189, 248), anchor="mm")
    
    # 2. Main Shocking Hook (Huge headline)
    hook_line1 = render_arabic("أكبر مقلب بيحصلك")
    hook_line2 = render_arabic("وأنت بتكتب بالكيبورد! 🤦‍♂️")
    draw.text((W//2, 340), hook_line1, font=f_hook, fill=(255, 255, 255), anchor="mm")
    draw.text((W//2, 440), hook_line2, font=f_hook, fill=(244, 63, 94), anchor="mm")
    
    sub_text = render_arabic("تكتب سطرين بحماس.. وتتفاجأ إنك بتكتب طلاسم؟")
    draw.text((W//2, 540), sub_text, font=f_sub, fill=(148, 163, 184), anchor="mm")
    
    # 3. Before Card (The Frustration)
    card1_y1, card1_y2 = 640, 920
    draw_rounded_rect(draw, [80, card1_y1, W - 80, card1_y2], radius=30, fill=(15, 23, 42, 230), outline=(239, 68, 68), width=3)
    
    label_before = render_arabic("❌ اللي بيظهرلك في الشات (كوارث):")
    draw.text((W - 130, card1_y1 + 50), label_before, font=f_sub, fill=(248, 113, 113), anchor="ra")
    
    typo_text = "hgsbl ugd;l dhughl ,vplm hggi"
    draw_rounded_rect(draw, [120, card1_y1 + 110, W - 120, card1_y1 + 220], radius=16, fill=(26, 16, 27), outline=(127, 29, 29), width=2)
    draw.text((W//2, card1_y1 + 165), typo_text, font=f_code, fill=(252, 165, 165), anchor="mm")
    
    # 4. Animated Transformation Indicator
    draw_rounded_rect(draw, [W//2 - 90, 950, W//2 + 90, 1070], radius=60, fill=(37, 99, 235), outline=(96, 165, 250), width=4)
    draw.text((W//2, 995), "⬇️", font=ImageFont.truetype(font_arial, 42), fill=(255, 255, 255), anchor="mm")
    draw.text((W//2, 1040), render_arabic("ضغطة واحدة"), font=ImageFont.truetype(font_arial, 24), fill=(224, 242, 254), anchor="mm")

    # 5. After Card (The Magic Solution)
    card2_y1, card2_y2 = 1100, 1380
    draw_rounded_rect(draw, [80, card2_y1, W - 80, card2_y2], radius=30, fill=(15, 23, 42, 230), outline=(34, 197, 94), width=4)
    
    label_after = render_arabic("✨ النتيجة الفورية بدون مسح حرف:")
    draw.text((W - 130, card2_y1 + 50), label_after, font=f_sub, fill=(74, 222, 128), anchor="ra")
    
    solved_text = render_arabic("السلام عليكم ياعالم ورحمة الله")
    draw_rounded_rect(draw, [120, card2_y1 + 110, W - 120, card2_y1 + 220], radius=16, fill=(6, 36, 24), outline=(22, 101, 52), width=2)
    draw.text((W//2, card2_y1 + 165), solved_text, font=f_arabic, fill=(134, 239, 172), anchor="mm")
    
    # 6. Bottom Call to Action Card
    draw_rounded_rect(draw, [80, 1460, W - 80, 1720], radius=35, fill=(30, 41, 59, 240), outline=(96, 165, 250), width=2)
    
    tag1 = render_arabic("🚀 اختصار فوري: Ctrl + Shift + Z")
    tag2 = render_arabic("🆓 مجاني ومفتوح المصدر بالكامل")
    tag3 = render_arabic("📲 يعمل في كل برامج الويندوز والمتصفح")
    
    draw.text((W//2, 1515), tag1, font=f_btn, fill=(56, 189, 248), anchor="mm")
    draw.text((W//2, 1585), tag2, font=f_sub, fill=(255, 255, 255), anchor="mm")
    draw.text((W//2, 1655), tag3, font=f_sub, fill=(148, 163, 184), anchor="mm")
    
    # 7. Bottom Teaser
    teaser = render_arabic("مين بيحصله الموقف ده؟ اعترفوا في الكومنتات! 👇")
    draw.text((W//2, 1790), teaser, font=f_btn, fill=(253, 224, 71), anchor="mm")
    
    out_path = "assets/tiktok/tiktok_cover.png"
    bg.save(out_path, format="PNG")
    print(f"Generated {out_path} successfully ({W}x{H})")

if __name__ == "__main__":
    generate_tiktok_cover()
