# =============================================================================
#    *** بوت YourWallAR - الإصدار 4.2 (إصلاح التوقيت + الخطة الاحتياطية) ***
#
#  (v4.2) إصلاح الخطأ المنطقي: تم توحيد التوقيت بالكامل إلى UTC.
#         - تم إزالة 'pytz' والاعتماد على توقيت GitHub (UTC).
#         - تم تعديل 'SCHEDULE' ليعكس أوقات UTC (6، 12، 18).
#  (v4.2) إضافة "خطة احتياطية":
#         - الكود سيحاول أولاً إرسال الصورة "بالرابط" (الأسرع).
#         - إذا فشل، سيحاول ثانياً إرسالها "بالرفع" (الأبطأ ولكن موثوق).
#         - إذا فشل كلاهما، يرسل رسالة خطأ نصية.
# =============================================================================

import requests
import os
import sys
import datetime
# (v4.2) تم إزالة 'pytz' لأنه سبب المشكلة
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

# --- [2] الدوال المساعدة (إرسال الرسائل - v4.2) ---

def post_photo_by_url(image_url, text_caption):
    """(v4.2 - الخطة أ: الأسرع) إرسال رابط الصورة (URL) مباشرة إلى تيليجرام."""
    print(f"... (الخطة أ) جاري إرسال (رابط الخلفية) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    payload = {
        'chat_id': CHANNEL_USERNAME,
        'photo': image_url, 
        'caption': text_caption if text_caption.strip() else None,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, json=payload, timeout=60) 
    response.raise_for_status() # (إذا فشل، سيتم التقاطه بواسطة try/except في main)
    print(">>> (الخطة أ) تم الإرسال بنجاح!")

def post_photo_by_upload(image_url, text_caption):
    """(v4.2 - الخطة ب: الاحتياطية) إرسال صورة + نص (مع خدعة الرفع)"""
    print(f"... (الخطة ب) فشلت الخطة أ. جاري تجربة (رفع الخلفية) إلى {CHANNEL_USERNAME} ...")
    response = None 
    
    print(f"   ... (1/2) جاري تحميل الصورة من: {image_url}")
    image_response = requests.get(image_url, timeout=90)
    image_response.raise_for_status()
    image_data = image_response.content
    
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    caption_to_send = text_caption if text_caption.strip() else None
    payload = { 'chat_id': CHANNEL_USERNAME, 'caption': caption_to_send, 'parse_mode': 'HTML'}
    files = {'photo': ('wallpaper.jpg', image_data, 'image/jpeg')} 
    
    print("   ... (2/2) جاري رفع الصورة إلى تيليجرام ...")
    response = requests.post(url, data=payload, files=files, timeout=90)
    response.raise_for_status() # (إذا فشل، سيتم التقاطه بواسطة try/except في main)
    print(">>> (الخطة ب) تم الإرسال بنجاح!")

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
    if not text_to_translate: return None
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

# --- [4] دالة جلب البيانات (v4.2 - تعطي رابطين) ---

def get_random_wallpaper(search_query, orientation):
    print(f"... جاري جلب خلفية لـ: '{search_query}' (الاتجاه: {orientation})")
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': search_query, 'orientation': orientation, 'per_page': 1, 'page': random.randint(1, 100)}
    
    response_api = None
    try:
        response_api = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        response_api.raise_for_status()
        data = response_api.json()
        
        if not data.get('photos') or len(data['photos']) == 0:
            error_msg = f"No results found for query: {search_query} / {orientation}"
            print(f"!!! فشل جلب البيانات: {error_msg}")
            return None, None, None, None, None, error_msg

        photo = data['photos'][0]
        
        # (v4.2) إرجاع رابطين: واحد للسرعة، وواحد للرفع الاحتياطي
        image_url_fast = photo['src']['large2x'] # (للخطة أ)
        image_url_safe = photo['src']['large'] # (للخطة ب - حجم أصغر وأكثر أماناً للرفع)
        
        description_en = photo.get('alt')
        photographer_name = photo['photographer']
        photographer_url = photo['photographer_url']
        
        description_ar = translate_text(description_en)
        
        print(">>> تم جلب الصورة بنجاح. جاري بناء الرسالة...")
        return image_url_fast, image_url_safe, description_ar, photographer_name, photographer_url, None
        
    except requests.exceptions.HTTPError as e:
        error_details = f"HTTP Error: {e.response.status_code} ({e.response.reason})"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details} - {e.response.text}")
        return None, None, None, None, None, error_details
    except Exception as e:
        error_details = f"General Error: {str(e)}"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details}")
        return None, None, None, None, None, error_details

# --- [5] دالة تنسيق الرسالة (لم تتغير) ---

def format_telegram_post(title, description, photographer_name, photographer_url):
    caption_parts = []
    if title: caption_parts.append(f"<b>{title}</b>")
    if description: caption_parts.append(f"<i>«{description.capitalize()}»</i>")
    if photographer_name: caption_parts.append(f"📷 <b>بواسطة:</b> <a href='{photographer_url}'>{photographer_name}</a>")
    final_caption = "\n\n".join(caption_parts)
    return final_caption

# --- [6] التشغيل الرئيسي (v4.2 - إصلاح التوقيت) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v4.2 - بوت YourWallAR - إصلاح التوقيت)...")
    
    # (v4.2) الجدول الآن بتوقيت UTC ليطابق ملف YML
    # (6 UTC = 9 صباحاً بتوقيت العراق)
    # (12 UTC = 3 مساءً بتوقيت العراق)
    # (18 UTC = 9 مساءً بتوقيت العراق)
    SCHEDULE = {
        6: {'task': 'phone', 'query': 'nature wallpaper', 'orientation': 'portrait', 'title': '📱 خلفية هاتف (Android/iOS)'},
        12: {'task': 'tablet', 'query': 'minimalist wallpaper', 'orientation': 'landscape', 'title': '💻 خلفية آيباد/تابلت'},
        18: {'task': 'pc', 'query': '4k wallpaper', 'orientation': 'landscape', 'title': '🖥️ خلفية كمبيوتر (PC/Mac)'}
    }
    
    # (v4.2) الكود الآن يتحقق من توقيت UTC الخاص بالخادم مباشرة
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_hour_utc = now_utc.hour
    
    print(f"الوقت الحالي (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if current_hour_utc in SCHEDULE:
        task = SCHEDULE[current_hour_utc]
        print(f">>> (وقت مجدول: {current_hour_utc}:00 UTC) - جاري تشغيل مهمة: '{task['task']}'")
        
        img_fast, img_safe, desc, photo_name, photo_url, error_msg = get_random_wallpaper(
            task['query'], 
            task['orientation']
        )
        
        if img_fast: # (إذا نجح جلب البيانات)
            caption = format_telegram_post(task['title'], desc, photo_name, photo_url)
            try:
                # (الخطة أ: محاولة إرسال الرابط السريع)
                post_photo_by_url(img_fast, caption)
            except Exception as e_url:
                print(f"!!! (الخطة أ) فشلت: {e_url}")
                try:
                    # (الخطة ب: محاولة الرفع الآمن)
                    post_photo_by_upload(img_safe, caption)
                except Exception as e_upload:
                    # (الخطة ج: فشل كل شيء)
                    print(f"!!! (الخطة ب) فشلت أيضاً: {e_upload}")
                    post_text_to_telegram(f"🚨 حدث خطأ فادح أثناء إرسال الخلفية ({task['task']}).\n\n<b>السبب:</b>\n<pre>{e_upload}</pre>")
        else:
            # (فشل جلب البيانات من Pexels)
            print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({task['task']}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")
            
    else:
        print(f"... (الوقت: {current_hour_utc}:00 UTC) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

