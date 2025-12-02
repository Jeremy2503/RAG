"""
Quick test to check if OCR can extract text from the uploaded image.
"""
import easyocr
from PIL import Image
from pathlib import Path

# Path to your uploaded image
image_path = Path("./data/uploads/03e86745-2702-4621-be94-5205502020f8_hr-policies-and-procedure-template.png")

if not image_path.exists():
    print(f"[ERROR] Image not found: {image_path}")
    print("\nAvailable files in uploads:")
    for f in Path("./data/uploads").glob("*.png"):
        print(f"  - {f.name}")
    exit(1)

print(f"[OK] Found image: {image_path.name}")

# Open image
image = Image.open(image_path)
print(f"[INFO] Image size: {image.size[0]}x{image.size[1]} pixels")

# Initialize EasyOCR
print("[INFO] Initializing EasyOCR reader...")
reader = easyocr.Reader(['en'], gpu=False)
print("[OK] Reader initialized")

# Extract text
print("[INFO] Extracting text from image...")
results = reader.readtext(str(image_path), detail=0, paragraph=True)

if not results:
    print("[ERROR] No text detected!")
else:
    extracted_text = "\n".join(results)
    print(f"\n[OK] Successfully extracted {len(extracted_text)} characters\n")
    print("=" * 60)
    print("EXTRACTED TEXT:")
    print("=" * 60)
    print(extracted_text[:1000])  # First 1000 characters
    if len(extracted_text) > 1000:
        print(f"\n... (and {len(extracted_text) - 1000} more characters)")
    print("=" * 60)

