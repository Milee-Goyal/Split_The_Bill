"""
Generates 12 realistic synthetic test receipt images simulating real-world challenging conditions:
1. Dim light
2. Crumpled paper
3. Steep angle
4. Faded thermal print
5. Handwriting
6. Two scripts (Bilingual: Hindi & English)
7. Long bill part 1 & part 2
8. Wrong printed total (deliberate arithmetic error)
9. Family feast
10. Cafe with discounts and service charge
11. Brewery with VAT & Cess
12. Late night party bill
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_bills")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_fonts():
    try:
        font_mono = ImageFont.truetype("cour.ttf", 20)
        font_mono_bold = ImageFont.truetype("courbd.ttf", 22)
        font_small = ImageFont.truetype("cour.ttf", 16)
        font_hand = ImageFont.truetype("comic.ttf", 22)  # casual handwritten fallback
    except Exception:
        font_mono = ImageFont.load_default()
        font_mono_bold = font_mono
        font_small = font_mono
        font_hand = font_mono
    return font_mono, font_mono_bold, font_small, font_hand


def draw_receipt_base(lines, title="THE SPICE ROUTE", subtitle="AUTHENTIC BISTRO", date_str="12-OCT-2025 21:15"):
    font_mono, font_bold, font_small, _ = get_fonts()
    width = 460
    line_height = 26
    height = 140 + len(lines) * line_height + 100

    img = Image.new("RGB", (width, height), color=(250, 248, 243))
    draw = ImageDraw.Draw(img)

    # Top serrated / paper edge
    for x in range(0, width, 16):
        draw.polygon([(x, 0), (x + 8, 10), (x + 16, 0)], fill=(235, 230, 220))

    # Header
    draw.text((width // 2, 35), title, font=font_bold, fill=(40, 40, 40), anchor="mt")
    draw.text((width // 2, 65), subtitle, font=font_small, fill=(90, 90, 90), anchor="mt")
    draw.text((width // 2, 88), f"Date: {date_str} | Table #04", font=font_small, fill=(90, 90, 90), anchor="mt")
    draw.line([(25, 115), (width - 25, 115)], fill=(150, 150, 150), width=1)

    y = 130
    for left, right in lines:
        if left == "---":
            draw.line([(25, y + 10), (width - 25, y + 10)], fill=(180, 180, 180), width=1)
            y += 22
        elif left == "===":
            draw.line([(25, y + 8), (width - 25, y + 8)], fill=(70, 70, 70), width=2)
            y += 24
        elif left.startswith("**"):
            clean_left = left.replace("**", "")
            draw.text((25, y), clean_left, font=font_bold, fill=(20, 20, 20))
            draw.text((width - 25, y), right, font=font_bold, fill=(20, 20, 20), anchor="ra")
            y += line_height + 4
        else:
            draw.text((25, y), left, font=font_mono, fill=(50, 50, 50))
            draw.text((width - 25, y), right, font=font_mono, fill=(50, 50, 50), anchor="ra")
            y += line_height

    # Footer
    draw.text((width // 2, y + 25), "Thank you! Please visit again.", font=font_small, fill=(110, 110, 110), anchor="mt")
    return img


def apply_dim_light(img):
    enhancer = ImageEnhance.Brightness(img)
    dim = enhancer.enhance(0.52)
    # Warm amber tint for dim restaurant ambiance
    tint = Image.new("RGB", dim.size, (45, 30, 15))
    return Image.blend(dim, tint, 0.22)


def apply_crumpled(img):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Draw simulated dark crease lines and shadow wrinkles
    creases = [
        [(10, 80), (140, 190), (280, 160), (440, 310)],
        [(420, 90), (300, 220), (160, 350), (30, 480)],
        [(20, 400), (180, 430), (360, 520), (430, 600)],
    ]
    for pts in creases:
        draw.line(pts, fill=(170, 160, 150), width=2)
    return img.filter(ImageFilter.GaussianBlur(radius=0.4))


def apply_steep_angle(img):
    w, h = img.size
    # Perspective transform: Trapezoid shear
    coeffs = [
        1.1, 0.22, -30,
        0.05, 1.15, -20,
        0.0003, 0.0002
    ]
    return img.transform((w + 80, h + 80), Image.PERSPECTIVE, coeffs, Image.BILINEAR, fillcolor=(220, 218, 212))


def apply_faded_thermal(img):
    # Very pale gray, faded ink
    enhancer = ImageEnhance.Contrast(img)
    faded = enhancer.enhance(0.42)
    enhancer_b = ImageEnhance.Brightness(faded)
    faded = enhancer_b.enhance(1.25)
    return faded.filter(ImageFilter.GaussianBlur(0.35))


def apply_handwritten(lines, title="SHARMA DHABA & CAFE"):
    _, _, font_small, font_hand = get_fonts()
    width = 460
    height = 140 + len(lines) * 32 + 80
    img = Image.new("RGB", (width, height), color=(252, 250, 240))
    draw = ImageDraw.Draw(img)

    draw.text((width // 2, 35), title, font=font_hand, fill=(10, 40, 130), anchor="mt")
    draw.text((width // 2, 70), "Date: 14/10/2025  Bill No: 84", font=font_hand, fill=(30, 60, 150), anchor="mt")
    draw.line([(30, 105), (width - 30, 105)], fill=(120, 150, 220), width=2)

    y = 120
    for left, right in lines:
        if left in ["---", "==="]:
            draw.line([(30, y + 8), (width - 30, y + 8)], fill=(120, 150, 220), width=2)
            y += 24
        else:
            draw.text((35, y), left, font=font_hand, fill=(10, 40, 130))
            draw.text((width - 35, y), right, font=font_hand, fill=(10, 40, 130), anchor="ra")
            y += 32
    return img


def generate_all():
    print("Generating 12 receipt test images...")

    # 1. Dim Light
    lines_1 = [
        ("1x Paneer Butter Masala", "320.00"),
        ("2x Butter Naan", "120.00"),
        ("1x Jeera Rice", "160.00"),
        ("2x Fresh Lime Soda", "140.00"),
        ("---", ""),
        ("Subtotal", "740.00"),
        ("CGST (2.5%)", "18.50"),
        ("SGST (2.5%)", "18.50"),
        ("---", ""),
        ("**GRAND TOTAL**", "**777.00**"),
    ]
    img_1 = draw_receipt_base(lines_1, "HAVELI RESTAURANT")
    apply_dim_light(img_1).save(os.path.join(OUTPUT_DIR, "bill_01_dim_light.jpg"))

    # 2. Crumpled
    lines_2 = [
        ("1x Veg Hakka Noodles", "240.00"),
        ("1x Chilli Paneer Dry", "310.00"),
        ("1x Manchow Soup", "150.00"),
        ("---", ""),
        ("Subtotal", "700.00"),
        ("CGST (2.5%)", "17.50"),
        ("SGST (2.5%)", "17.50"),
        ("Service Charge (5%)", "35.00"),
        ("---", ""),
        ("**TOTAL DUE**", "**770.00**"),
    ]
    img_2 = draw_receipt_base(lines_2, "WOK & ROLL ASIAN")
    apply_crumpled(img_2).save(os.path.join(OUTPUT_DIR, "bill_02_crumpled.jpg"))

    # 3. Steep Angle
    lines_3 = [
        ("2x Margherita Pizza", "580.00"),
        ("1x Cheesy Garlic Bread", "190.00"),
        ("2x Peach Iced Tea", "220.00"),
        ("---", ""),
        ("Subtotal", "990.00"),
        ("CGST (2.5%)", "24.75"),
        ("SGST (2.5%)", "24.75"),
        ("---", ""),
        ("**TOTAL**", "**1039.50**"),
    ]
    img_3 = draw_receipt_base(lines_3, "PIZZA OVEN TRATTORIA")
    apply_steep_angle(img_3).save(os.path.join(OUTPUT_DIR, "bill_03_steep_angle.jpg"))

    # 4. Faded Thermal
    lines_4 = [
        ("1x Cappuccino Large", "220.00"),
        ("1x Blueberry Muffin", "180.00"),
        ("1x Espresso Shot", "140.00"),
        ("---", ""),
        ("Subtotal", "540.00"),
        ("CGST (2.5%)", "13.50"),
        ("SGST (2.5%)", "13.50"),
        ("---", ""),
        ("**GRAND TOTAL**", "**567.00**"),
    ]
    img_4 = draw_receipt_base(lines_4, "URBAN ROAST CAFE")
    apply_faded_thermal(img_4).save(os.path.join(OUTPUT_DIR, "bill_04_faded_thermal.jpg"))

    # 5. Handwritten
    lines_5 = [
        ("Dal Tadka", "180.00"),
        ("4 Tandoori Roti", "80.00"),
        ("Mix Veg", "200.00"),
        ("Boondi Raita", "90.00"),
        ("---", ""),
        ("Sub Total", "550.00"),
        ("Tax", "25.00"),
        ("---", ""),
        ("Total Amount", "575.00"),
    ]
    img_5 = apply_handwritten(lines_5, "ROYAL PUNJAB DHABA")
    img_5.save(os.path.join(OUTPUT_DIR, "bill_05_handwritten.jpg"))

    # 6. Two Scripts (Bilingual: Devanagari & English)
    lines_6 = [
        ("Paneer Makhani (पनीर)", "340.00"),
        ("Dal Makhani (दाल मखनी)", "280.00"),
        ("3x Butter Roti (रोटी)", "105.00"),
        ("Gulab Jamun (गुलाब जामुन)", "110.00"),
        ("---", ""),
        ("Subtotal", "835.00"),
        ("CGST (2.5%)", "20.88"),
        ("SGST (2.5%)", "20.88"),
        ("---", ""),
        ("**GRAND TOTAL**", "**876.76**"),
    ]
    img_6 = draw_receipt_base(lines_6, "PURANI DILLI RASOI", "Bilingual Authentic Cuisine")
    img_6.save(os.path.join(OUTPUT_DIR, "bill_06_two_scripts.jpg"))

    # 7. Long Bill (Part 1 & Part 2)
    lines_7a = [
        ("1x Crispy Corn", "210.00"),
        ("1x Spring Rolls", "220.00"),
        ("2x Chicken Tikka", "560.00"),
        ("1x Fish Fingers", "380.00"),
        ("---", ""),
        ("Page 1 Subtotal", "1370.00"),
        ("(Continued on Page 2)", "-->"),
    ]
    draw_receipt_base(lines_7a, "THE GRAND BANQUET - PART 1").save(os.path.join(OUTPUT_DIR, "bill_07_long_bill_p1.jpg"))

    lines_7b = [
        ("(From Page 1)", "1370.00"),
        ("1x Mutton Rogan Josh", "490.00"),
        ("4x Garlic Naan", "280.00"),
        ("1x Biryani Handi", "420.00"),
        ("4x Soft Drinks", "240.00"),
        ("---", ""),
        ("Total Subtotal", "2800.00"),
        ("CGST (2.5%)", "70.00"),
        ("SGST (2.5%)", "70.00"),
        ("Service Charge (8%)", "224.00"),
        ("---", ""),
        ("**GRAND TOTAL**", "**3164.00**"),
    ]
    draw_receipt_base(lines_7b, "THE GRAND BANQUET - PART 2").save(os.path.join(OUTPUT_DIR, "bill_07_long_bill_p2.jpg"))

    # 8. Wrong Printed Total (Deliberate cashier math mistake: subtotal 750 + tax 37.50 = 787.50, but printed 830.00!)
    lines_8 = [
        ("1x Veg Kadhai", "320.00"),
        ("1x Dal Tadka", "230.00"),
        ("4x Laccha Paratha", "200.00"),
        ("---", ""),
        ("Subtotal", "750.00"),
        ("CGST (2.5%)", "18.75"),
        ("SGST (2.5%)", "18.75"),
        ("---", ""),
        ("**PRINTED TOTAL**", "**830.00**"),  # Genuinely wrong printed total (+42.50 discrepancy!)
    ]
    draw_receipt_base(lines_8, "CORNER CORNER DINER").save(os.path.join(OUTPUT_DIR, "bill_08_wrong_printed_total.jpg"))

    # 9. Family Feast
    lines_9 = [
        ("2x Chicken Biryani", "700.00"),
        ("1x Tandoori Platter", "550.00"),
        ("1x Mutton Korma", "480.00"),
        ("4x Rumali Roti", "160.00"),
        ("2x Mango Lassi", "180.00"),
        ("---", ""),
        ("Subtotal", "2070.00"),
        ("CGST (2.5%)", "51.75"),
        ("SGST (2.5%)", "51.75"),
        ("---", ""),
        ("**GRAND TOTAL**", "**2173.50**"),
    ]
    draw_receipt_base(lines_9, "NAWAB'S FEAST").save(os.path.join(OUTPUT_DIR, "bill_09_family_feast.jpg"))

    # 10. Cafe with Discount and Service Charge
    lines_10 = [
        ("2x Avocado Toast", "560.00"),
        ("2x Caramel Macchiato", "440.00"),
        ("1x Cheesecake Slice", "260.00"),
        ("---", ""),
        ("Subtotal", "1260.00"),
        ("Discount (10%)", "-126.00"),
        ("Service Charge (5%)", "63.00"),
        ("CGST (2.5%)", "29.93"),
        ("SGST (2.5%)", "29.93"),
        ("---", ""),
        ("**GRAND TOTAL**", "**1256.86**"),
    ]
    draw_receipt_base(lines_10, "BLUE DOOR CAFE").save(os.path.join(OUTPUT_DIR, "bill_10_cafe_discounts.jpg"))

    # 11. Brewery with VAT & Food GST
    lines_11 = [
        ("2x Craft Beer Pitcher", "1200.00"),
        ("1x Loaded Nachos", "380.00"),
        ("1x BBQ Chicken Wings", "420.00"),
        ("---", ""),
        ("Subtotal", "2000.00"),
        ("VAT (Alcohol 10%)", "120.00"),
        ("GST (Food 5%)", "40.00"),
        ("Service Charge (7%)", "140.00"),
        ("---", ""),
        ("**TOTAL PAYABLE**", "**2300.00**"),
    ]
    draw_receipt_base(lines_11, "THE HOP YARD BREWERY").save(os.path.join(OUTPUT_DIR, "bill_11_brewery_vat.jpg"))

    # 12. Party Night
    lines_12 = [
        ("4x Mocktail Pitcher", "1200.00"),
        ("3x Veg Pizza Feast", "1350.00"),
        ("2x Pasta Alfredo", "760.00"),
        ("2x Brownie Sundae", "440.00"),
        ("---", ""),
        ("Subtotal", "3750.00"),
        ("Service Charge (10%)", "375.00"),
        ("CGST (2.5%)", "93.75"),
        ("SGST (2.5%)", "93.75"),
        ("---", ""),
        ("**GRAND TOTAL**", "**4312.50**"),
    ]
    draw_receipt_base(lines_12, "CELEBRATION CLUB LOUNGE").save(os.path.join(OUTPUT_DIR, "bill_12_party_night.jpg"))

    print("Successfully generated all 12 receipt images in test_bills/")


if __name__ == "__main__":
    generate_all()
