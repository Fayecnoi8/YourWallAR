# =============================================================================
#    *** بوت YourWallAR - الإصدار 4.1 (إصلاح التايم آوت) ***
#
#  (v4.1) المشكلة: v4.0 (جودة large2x) تسبب تايم آوت بسبب "خدعة الرفع".
#  (v4.1) الحل: تم تغيير طريقة الإرسال. بدلاً من تحميل ثم رفع الصورة،
#         نقوم الآن بإرسال "رابط" الصورة (URL) مباشرة إلى تيليجرام.
#         هذا يحل مشكلة التايم آوت ويحافظ على الجودة العالية.
#  (v4.1) تم الحفاظ على جودة 'large2x' (أو حتى 'original' يمكن استخدامها الآن).
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

# --- [2] الدوال المساعدة (إرسال الرسائل - v4.1) ---

def post_photo_by_url(image_url, text_caption):
    """(v4.1 - الطريقة الذكية) إرسال رابط الصورة (URL) مباشرة إلى تيليجرام."""
    print(f"... جاري إرسال (رابط الخلفية) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    
    # (هنا السحر: نرسل 'photo' كرابط نصي، وليس كملف)
    payload = {
        'chat_id': CHANNEL_USERNAME,
        'photo': image_url, # (تيليجرام سيقوم بتحميل هذا الرابط)
        'caption': text_caption if text_caption.strip() else None,
        'parse_mode': 'HTML'
    }
    
    response = None
    try:
        # (نرسل كـ JSON، وليس كـ 'files')
        response = requests.post(url, json=payload, timeout=60) 
        response.raise_for_status()
        print(">>> تم إرسال (رابط الخلفية) بنجاح!")
        
    except requests.exceptions.RequestException as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من تيليجرام')
        print(f"!!! فشل إرسال (رابط الخلفية): {e} - {error_message}")
        # (خطة احتياطية: أرسل رسالة خطأ نصية إذا فشل إرسال الرابط)
        post_text_to_telegram(f"🚨 حدث خطأ أثناء إرسال رابط الصورة.\n\n<b>السبب:</b>\n<pre>{error_message}</pre>")

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

# --- [4] دالة جلب البيانات (v4.1 - جودة عالية) ---

def get_random_wallpaper(search_query, orientation):
    """
    يجلب صورة عشوائية عالية الجودة من Pexels (v4.1).
    """
    print(f"... جاري جلب خلفية لـ: '{search_query}' (الاتجاه: {orientation})")
    headers = {'Authorization': PEXELS_API_KEY}
    params = {
        'query': search_query,
        'orientation': orientation,
        'per_page': 1,
        'page': random.randint(1, 100),
        'size': 'large2x' # (v4.1) نطلب جودة عالية جداً (أو 'original')
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
        
        # (v4.1) استخدام 'large2x' أو حتى 'original' ممكن الآن
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

# --- [5] دالة تنسيق الرسالة (لم تتغير) ---

def format_telegram_post(title, description, photographer_name, photographer_url):
    """(v4.0) يبني الرسالة الذكية والنظيفة بناءً على الطلبات الجديدة."""
    caption_parts = []
    
    if title:
        caption_parts.append(f"<b>{title}</b>")
        
    if description:
        caption_parts.append(f"<i>«{description.capitalize()}»</i>")
            
    if photographer_name:
        caption_parts.append(f"📷 <b>بواسطة:</b> <a href='{photographer_url}'>{photographer_name}</a>")
    
    final_caption = "\n\n".join(caption_parts)
    return final_caption

# --- [6] التشغيل الرئيسي (v4.1 - يستخدم إرسال الرابط) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v4.1 - بوت YourWallAR - إرسال بالرابط)...")
    
    SCHEDULE = {
        6: {'task': 'phone', 'query': 'nature wallpaper', 'orientation': 'portrait', 'title': '📱 خلفية هاتف (Android/iOS)'},
        12: {'task': 'tablet', 'query': 'minimalist wallpaper', 'orientation': 'landscape', 'title': '💻 خلفية آيباد/تابلت'},
        18: {'task': 'pc', 'query': '4k wallpaper', 'orientation': 'landscape', 'title': '🖥️ خلفية كمبيوتر (PC/Mac)'}
    }
    
    try:
        TARGET_TZ = pytz.timezone('Etc/GMT-3') # (توقيت العراق GMT+3)
    except pytz.UnknownTimeZoneError:
        print("!!! خطأ: لم يتم العثور على المنطقة الزمنية 'Etc/GMT-3'.")
        sys.exit(1)

    now_tz = datetime.datetime.now(TARGET_TZ)
    current_hour_tz = now_tz.hour
    
    print(f"الوقت الحالي (توقيت الهدف GMT+3): {now_tz.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # (اختبار يدوي: اجعل هذا صحيحاً لفرض التشغيل للاختبار)
    MANUAL_TEST_RUN = False 
    
    if current_hour_tz in SCHEDULE or MANUAL_TEST_RUN:
        
        task_key = current_hour_tz
        if MANUAL_TEST_RUN:
            task_key = 6 # (لتشغيل مهمة الهاتف كاختبار)
            
        task = SCHEDULE[task_key]
        print(f">>> (وقت مجدول: {current_hour_tz}:00) - جاري تشغيل مهمة: '{task['task']}'")
        
        image_url, description, photo_name, photo_url, error_msg = get_random_wallpaper(
            task['query'], 
            task['orientation']
        )
        
        if image_url:
            caption = format_telegram_post(task['title'], description, photo_name, photo_url)
            # (v4.1) استخدام الدالة الجديدة التي ترسل الرابط
            post_photo_by_url(image_url, caption)
        else:
            print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({task['task']}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")
            
    else:
        print(f"... (الوقت: {current_hour_tz}:00) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

