# =============================================================================
#    *** بوت YourWallAR - الإصدار 4.0 (بوت الأجهزة الذكي) ***
#
#  (v4.0) تم تغيير "فلسفة" البوت بالكامل:
#         - النشر الآن بناءً على نوع الجهاز (هاتف، تابلت، كمبيوتر)
#         - بدلاً من النشر بناءً على وقت اليوم (صباح، مساء).
#  (v4.0) تم رفع جودة الصورة المطلوبة من 'large' إلى 'large2x' (جودة عالية جداً).
#  (v4.0) تم تعديل دالة format_telegram_post لتكون ذكية وتقبل "عنوان" مخصص.
# =============================================================================

import requests
import os
import sys
import datetime
import pytz
import random

# --- [1] الإعدادات والمفاتيح السرية (3 مفاتيح مطلوبة) ---
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
    PEXELS_API_KEY = os.environ['PEXELS_API_KEY']
    
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    print("!!! هل تذكرت إضافة (BOT_TOKEN, CHANNEL_USERNAME, PEXELS_API_KEY)؟")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
PEXELS_API_URL = "https://api.pexels.com/v1/search"
TRANSLATE_API_URL = "https://api.mymemory.translated.net/get"

# --- [2] الدوال المساعدة (إرسال الرسائل - آمنة) ---
# (هذه الدوال لم تتغير، فهي تعمل بشكل ممتاز)

def post_photo_to_telegram(image_url, text_caption):
    """(آمن) إرسال صورة + نص (مع خدعة الرفع)"""
    print(f"... جاري إرسال (الخلفية) إلى {CHANNEL_USERNAME} ...")
    response = None 
    try:
        print(f"   ... (1/2) جاري تحميل الصورة من: {image_url}")
        image_response = requests.get(image_url, timeout=90) # (زيادة الوقت إلى 90 ثانية للجودة العالية)
        image_response.raise_for_status()
        image_data = image_response.content
        
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        caption_to_send = text_caption if text_caption.strip() else None
        payload = { 'chat_id': CHANNEL_USERNAME, 'caption': caption_to_send, 'parse_mode': 'HTML'}
        files = {'photo': ('wallpaper.jpg', image_data, 'image/jpeg')} 
        
        print("   ... (2/2) جاري رفع الصورة إلى تيليجرام ...")
        response = requests.post(url, data=payload, files=files, timeout=90)
        response.raise_for_status()
        print(">>> تم إرسال (الخلفية) بنجاح!")
        
    except requests.exceptions.RequestException as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من تيليجرام')
        print(f"!!! فشل إرسال (الخلفية): {e} - {error_message}")
        sys.exit(1)

def post_text_to_telegram(text_content):
    """(آمن) إرسال رسالة خطأ نصية"""
    print(f"... جاري إرسال (رسالة خطأ) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = { 'chat_id': CHANNEL_USERNAME, 'text': text_content, 'parse_mode': 'HTML' }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل إرسال (رسالة الخطأ النصية) أيضاً: {e}")

# --- [3] دالة الترجمة (لم تتغير) ---

def translate_text(text_to_translate):
    """يترجم النص من الإنجليزية إلى العربية (إذا فشل، يُرجع الإنجليزية)."""
    if not text_to_translate:
        return None
        
    print(f"... جاري ترجمة الوصف: '{text_to_translate}'")
    params = {'q': text_to_translate, 'langpair': 'en|ar'}
    try:
        response = requests.get(TRANSLATE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['responseStatus'] == 200:
            translated = data['responseData']['translatedText']
            print(f">>> تم الترجمة: '{translated}'")
            return translated
        else:
            return text_to_translate
    except Exception as e:
        print(f"!!! فشلت الترجمة: {e}. العودة إلى الإنجليزية.")
        return text_to_translate

# --- [4] دالة جلب البيانات (v4.0 - مطورة) ---

def get_random_wallpaper(search_query, orientation):
    """
    يجلب صورة عشوائية عالية الجودة من Pexels (v4.0).
    """
    print(f"... جاري جلب خلفية لـ: '{search_query}' (الاتجاه: {orientation})")
    headers = {'Authorization': PEXELS_API_KEY}
    params = {
        'query': search_query,
        'orientation': orientation,
        'per_page': 1,
        'page': random.randint(1, 100) # (اختيار عشوائي)
    }
    
    response_api = None
    try:
        response_api = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        response_api.raise_for_status()
        data = response_api.json()
        
        if not data.get('photos') or len(data['photos']) == 0:
            error_msg = f"No results found for query: {search_query} / {orientation}"
            print(f"!!! فشل جلب البيانات: {error_msg}")
            return None, None, error_msg

        photo = data['photos'][0]
        
        # (v4.0) استخدام 'large2x' لجودة أعلى جداً
        image_url = photo['src']['large2x'] 
        description_en = photo.get('alt')
        photographer_name = photo['photographer']
        photographer_url = photo['photographer_url']
        
        description_ar = translate_text(description_en)
        
        print(">>> تم جلب الصورة بنجاح. جاري بناء الرسالة...")
        
        # إرجاع البيانات الخام
        return image_url, description_ar, photographer_name, photographer_url, None
        
    except requests.exceptions.HTTPError as e:
        error_details = f"HTTP Error: {e.response.status_code} ({e.response.reason})"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details} - {e.response.text}")
        return None, None, None, None, error_details
        
    except Exception as e:
        error_details = f"General Error: {str(e)}"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details}")
        return None, None, None, None, error_details

# --- [5] دالة تنسيق الرسالة (v4.0 - جديدة) ---

def format_telegram_post(title, description, photographer_name, photographer_url):
    """(v4.0) يبني الرسالة الذكية والنظيفة بناءً على الطلبات الجديدة."""
    caption_parts = []
    
    if title:
        caption_parts.append(f"<b>{title}</b>")
        
    if description:
        # (إضافة اقتباسات حول الوصف المترجم)
        caption_parts.append(f"<i>«{description.capitalize()}»</i>")
            
    if photographer_name:
        caption_parts.append(f"📷 <b>بواسطة:</b> <a href='{photographer_url}'>{photographer_name}</a>")
    
    # (ضم الأجزاء مع سطرين فارغين بينهما لـ "النظافة")
    final_caption = "\n\n".join(caption_parts)
    return final_caption

# --- [6] التشغيل الرئيسي (v4.0 - ذكي حسب الجهاز) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v4.0 - بوت YourWallAR - بوت الأجهزة)...")
    
    # (v4.0) تم تغيير الجدول الزمني بالكامل
    # (ملاحظة: هذا الجدول يحدد فقط "ماذا" سيحدث إذا كانت الساعة مطابقة)
    SCHEDULE = {
        # (توقيت العراق: 9 صباحاً)
        6: {'task': 'phone', 'query': 'nature wallpaper', 'orientation': 'portrait', 'title': '📱 خلفية هاتف (Android/iOS)'},
        # (توقيت العراق: 3 عصراً)
        12: {'task': 'tablet', 'query': 'minimalist wallpaper', 'orientation': 'landscape', 'title': '💻 خلفية آيباد/تابلت'},
        # (توقيت العراق: 9 مساءً)
        18: {'task': 'pc', 'query': '4k wallpaper', 'orientation': 'landscape', 'title': '🖥️ خلفية كمبيوتر (PC/Mac)'}
    }
    
    try:
        # (ملاحظة: توقيت العراق حالياً GMT+3، لذا سنستخدم UTC+3)
        # (هذا يعني أن 9 صباحاً = 6 UTC، و 3 عصراً = 12 UTC، و 9 مساءً = 18 UTC)
        # (إذا كان التوقيت الصيفي يتغير، يجب تعديل هذا)
        TARGET_TZ = pytz.timezone('Etc/GMT-3') 
    except pytz.UnknownTimeZoneError:
        print("!!! خطأ: لم يتم العثور على المنطقة الزمنية 'Etc/GMT-3'.")
        sys.exit(1)

    now_tz = datetime.datetime.now(TARGET_TZ)
    current_hour_tz = now_tz.hour
    
    print(f"الوقت الحالي (توقيت الهدف GMT+3): {now_tz.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if current_hour_tz in SCHEDULE:
        task = SCHEDULE[current_hour_tz]
        print(f">>> (وقت مجدول: {current_hour_tz}:00) - جاري تشغيل مهمة: '{task['task']}'")
        
        image_url, description, photo_name, photo_url, error_msg = get_random_wallpaper(
            task['query'], 
            task['orientation']
        )
        
        if image_url:
            caption = format_telegram_post(task['title'], description, photo_name, photo_url)
            post_photo_to_telegram(image_url, caption)
        else:
            print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({task['task']}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")
            
    else:
        print(f"... (الوقت: {current_hour_tz}:00) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

