# =============================================================================
#    *** بوت YourWallAR - الإصدار 9.0 (إصلاح الاختبار اليدوي) ***
#
#  (v9.0) المشكلة: عند التشغيل اليدوي (workflow_dispatch) في وقت
#         "خارج الجدول"، الكود يقرر (بذكاء) أن لا ينشر شيئاً.
#  (v9.0) الحل: الكود سيفحص "نوع التشغيل".
#         - 1. إذا كان (يدوياً): سينفذ مهمة (الهاتف) فوراً للاختبار.
#         - 2. إذا كان (مجدولاً): سيحترم الجدول الزمني (6, 12, 18).
# =============================================================================

import requests
import os
import sys
import datetime
import random

# --- [1] الإعدادات والمفاتيح السرية (3 مفاتيح مطلوبة) ---
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
    PEXELS_API_KEY = os.environ['PEXELS_API_KEY']
    # (v9.0) قراءة "نوع التشغيل" من ملف YML
    GITHUB_EVENT_NAME = os.environ.get('GITHUB_EVENT_NAME')
    
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
PEXELS_API_URL = "https://api.pexels.com/v1/search"
TRANSLATE_API_URL = "https://api.mymemory.translated.net/get"

# --- [2] الدوال المساعدة (إرسال الرسائل - v9.0) ---
# (هذه الدوال لم تتغير عن v8.0، فهي تعمل بشكل صحيح)

def post_photo_by_url(image_url, text_caption):
    print(f"... (v9.0) جاري إرسال (الرابط المضمون) إلى تيليجرام: {image_url}")
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    caption_to_send = text_caption if text_caption and text_caption.strip() else None
    
    payload = {
        'chat_id': CHANNEL_USERNAME,
        'photo': image_url,
        'caption': caption_to_send,
        'parse_mode': 'HTML'
    }
    
    response_telegram = None
    try:
        response_telegram = requests.post(url, json=payload, timeout=60)
        response_telegram.raise_for_status()
        if response_telegram.json().get('ok') == True:
            print(">>> (v9.0) تم إرسال (رابط الخلفية) بنجاح!")
        else:
            raise Exception(f"Telegram API reported 'ok: false' - {response_telegram.text}")
            
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP Error: {e.response.status_code} - {e.response.text}"
        print(f"!!! (v9.0) فشل إرسال (رابط الخلفية): {error_message}")
        post_text_to_telegram(f"🚨 حدث خطأ أثناء إرسال الخلفية.\n\n<b>السبب:</b>\n<pre>{error_message}</pre>")
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(f"!!! (v9.0) فشل إرسال (رابط الخلفية): {error_message}")
        post_text_to_telegram(f"🚨 حدث خطأ فادح أثناء معالجة الخلفية.\n\n<b>السبب:</b>\n<pre>{error_message}</pre>")


def post_text_to_telegram(text_content):
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
        if data['responseStatus'] == 200 and data['responseData']['translatedText'] != text_to_translate:
            translated = data['responseData']['translatedText']
            print(f">>> تم الترجمة: '{translated}'")
            return translated
        else:
            return text_to_translate
    except Exception as e:
        print(f"!!! فشلت الترجمة: {e}. العودة إلى الإنجليزية.")
        return text_to_translate

# --- [4] دالة جلب البيانات (لم تتغير) ---

def get_random_wallpaper(search_query, orientation):
    print(f"... جاري جلب خلفية لـ: '{search_query}' (الاتجاه: {orientation})")
    headers = {'Authorization': PEXELS_API_KEY}
    params = {'query': search_query, 'orientation': orientation, 'per_page': 5, 'page': random.randint(1, 100)}
    
    response_api = None
    try:
        response_api = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        response_api.raise_for_status()
        data = response_api.json()
        
        if not data.get('photos') or len(data['photos']) == 0:
            error_msg = f"No results found for query: {search_query} / {orientation}"
            print(f"!!! فشل جلب البيانات: {error_msg}")
            return None, None, None, None, error_msg

        photo = random.choice(data['photos'])
        
        if orientation == 'portrait':
            image_url_source = photo['src']['portrait']
        else:
            image_url_source = photo['src']['landscape']
        
        description_en = photo.get('alt')
        photographer_name = photo['photographer']
        photographer_url = photo['photographer_url']
        
        description_ar = translate_text(description_en)
        
        print(">>> تم جلب الصورة بنجاح. جاري بناء الرسالة...")
        return image_url_source, description_ar, photographer_name, photographer_url, None
        
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
    caption_parts = []
    if title: caption_parts.append(f"<b>{title}</b>")
    if description: caption_parts.append(f"<i>«{description.capitalize()}»</i>")
    if photographer_name: caption_parts.append(f"📷 <b>بواسطة:</b> <a href='{photographer_url}'>{photographer_name}</a>")
    final_caption = "\n\n".join(caption_parts)
    return final_caption

# --- [6] التشغيل الرئيسي (v9.0 - إصلاح الاختبار اليدوي) ---

# (الجدول بتوقيت UTC ليطابق ملف YML)
SCHEDULE = {
    6: {'task': 'phone', 'query': 'nature wallpaper', 'orientation': 'portrait', 'title': '📱 خلفية هاتف (Android/iOS)'},
    12: {'task': 'tablet', 'query': 'minimalist wallpaper', 'orientation': 'landscape', 'title': '💻 خلفية آيباد/تابلت'},
    18: {'task': 'pc', 'query': '4k wallpaper', 'orientation': 'landscape', 'title': '🖥️ خلفية كمبيوتر (PC/Mac)'}
}

def run_task(task_key):
    """دالة مخصصة لتشغيل مهمة محددة"""
    if task_key not in SCHEDULE:
        print(f"!!! خطأ: المهمة '{task_key}' غير معروفة.")
        return
        
    task = SCHEDULE[task_key]
    print(f">>> (مهمة: {task_key}) - جاري تشغيل مهمة: '{task['task']}'")
    
    image_url, description, photo_name, photo_url, error_msg = get_random_wallpaper(
        task['query'], 
        task['orientation']
    )
    
    if image_url: # (إذا نجح جلب البيانات)
        caption = format_telegram_post(task['title'], description, photo_name, photo_url)
        post_photo_by_url(image_url, caption)
    else:
        # (فشل جلب البيانات من Pexels)
        print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
        post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({task['task']}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")


def main():
    print("==========================================")
    print(f"بدء تشغيل (v9.0 - بوت YourWallAR - إصلاح الاختبار اليدوي)...")
    
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    current_hour_utc = now_utc.hour
    
    print(f"الوقت الحالي (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"نوع التشغيل (Event Name): {GITHUB_EVENT_NAME}")
    
    # =================================================================
    # (v9.0) *** التغيير الأهم (إصلاح الاختبار اليدوي) ***
    # =================================================================
    if GITHUB_EVENT_NAME == 'workflow_dispatch':
        # (1) هذا تشغيل يدوي (للاختبار)
        print(">>> (تشغيل يدوي) - جاري تشغيل 'مهمة الهاتف' كاختبار...")
        run_task('phone') # (تشغيل مهمة الهاتف كاختبار افتراضي)
        
    elif current_hour_utc in SCHEDULE:
        # (2) هذا تشغيل مجدول
        task_key = [k for k, v in SCHEDULE.items() if k == current_hour_utc][0]
        print(f">>> (تشغيل مجدول) - الوقت {current_hour_utc}:00 UTC. جاري تشغيل مهمة...")
        run_task(task_key)
        
    else:
        # (3) هذا تشغيل مجدول ولكن في وقت "خارج الجدول"
        print(f"... (الوقت: {current_hour_utc}:00 UTC) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")
    # =================================================================

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

