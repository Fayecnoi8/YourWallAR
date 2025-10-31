# =============================================================================
#    *** بوت YourWallAR - الإصدار 3.0 (النظيف والمترجم) ***
#
#  (v3.0) إضافة مترجم API مجاني (MyMemory) لترجمة الوصف إلى العربية.
#  (v3.0) جعل الرسالة "ذكية" (تخفي الأسطر الفارغة).
#  (v3.0) جعل الرسالة "نظيفة" (إزالة التذييل وسطر "عبر Pexels").
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
# (v3.0) رابط API الترجمة المجاني
TRANSLATE_API_URL = "https://api.mymemory.translated.net/get"

# --- [2] الدوال المساعدة (إرسال الرسائل - آمنة) ---
# (هذه الدوال لم تتغير، فهي تعمل بشكل ممتاز)

def post_photo_to_telegram(image_url, text_caption):
    """(آمن) إرسال صورة + نص (مع خدعة الرفع)"""
    print(f"... جاري إرسال (الخلفية) إلى {CHANNEL_USERNAME} ...")
    response = None 
    try:
        print(f"   ... (1/2) جاري تحميل الصورة من: {image_url}")
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()
        image_data = image_response.content
        
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        # (v3.0) إذا كان نص التعليق فارغاً، أرسل None
        caption_to_send = text_caption if text_caption.strip() else None
        payload = { 'chat_id': CHANNEL_USERNAME, 'caption': caption_to_send, 'parse_mode': 'HTML'}
        files = {'photo': ('wallpaper.jpg', image_data, 'image/jpeg')} 
        
        print("   ... (2/2) جاري رفع الصورة إلى تيليجرام ...")
        response = requests.post(url, data=payload, files=files, timeout=90)
        response.raise_for_status()
        print(">>> تم إرسال (الخلفية) بنجاح!")
        
    except requests.exceptions.RequestException as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من تيليجرام')
        print(f"!!! فشل إrsال (الخلفية): {e} - {error_message}")
        sys.exit(1)

def post_text_to_telegram(text_content):
    """(آمن) إرسال رسالة خطأ نصية"""
    print(f"... جاري إrsال (رسالة خطأ) إلى {CHANNEL_USERNAME} ...")
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = { 'chat_id': CHANNEL_USERNAME, 'text': text_content, 'parse_mode': 'HTML' }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"!!! فشل إرسال (رسالة الخطأ النصية) أيضاً: {e}")


# --- [3] (جديد v3.0) دالة الترجمة ---

def translate_text(text_to_translate):
    """
    يترجم النص من الإنجليزية إلى العربية باستخدام API مجاني.
    إذا فشل، يُرجع النص الإنجليزي الأصلي.
    """
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
            print(f"!!! فشلت الترجمة (API status {data['responseStatus']}). العودة إلى الإنجليزية.")
            return text_to_translate # (الخطة الاحتياطية 1)
            
    except Exception as e:
        print(f"!!! حدث خطأ أثناء الاتصال بواجهة الترجمة: {e}")
        return text_to_translate # (الخطة الاحتياطية 2)


# --- [4] دالة جلب البيانات (Pexels) ---

def get_random_wallpaper(search_query):
    """
    يجلب صورة عشوائية عالية الجودة من Pexels بناءً على البحث.
    (v3.0) تم تحديثه ليكون "ذكي" ونظيف ويترجم.
    """
    print(f"... جاري جلب خلفية لـ: '{search_query}' (من Pexels)")
    headers = {'Authorization': PEXELS_API_KEY}
    params = {
        'query': search_query,
        'orientation': 'portrait',
        'per_page': 1,
        'page': random.randint(1, 100)
    }
    
    response_api = None
    try:
        response_api = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=30)
        response_api.raise_for_status()
        data = response_api.json()
        
        if not data.get('photos') or len(data['photos']) == 0:
            print(f"!!! فشل جلب البيانات: Pexels لم يُرجع أي صور للبحث '{search_query}'")
            return None, None, f"No results found for query: {search_query}"

        photo = data['photos'][0]
        
        image_url = photo['src']['large']
        description_en = photo.get('alt') # (الوصف الإنجليزي)
        photographer_name = photo['photographer']
        photographer_url = photo['photographer_url']
        
        # (v3.0) خطوة الترجمة
        description_ar = translate_text(description_en)
        
        print(">>> تم جلب الصورة بنجاح. جاري بناء الرسالة النظيفة...")
        
        # (v3.0) بناء الرسالة "الذكية" والنظيفة
        caption_parts = []
        
        if description_ar:
            caption_parts.append(f"📸 <b>{description_ar.capitalize()}</b>")
            
        if photographer_name:
            caption_parts.append(f"📷 <b>بواسطة:</b> <a href='{photographer_url}'>{photographer_name}</a>")
        
        # (ضم الأجزاء مع سطرين فارغين بينهما لـ "النظافة")
        final_caption = "\n\n".join(caption_parts)
        
        return image_url, final_caption, None # (لا يوجد خطأ)
        
    except requests.exceptions.HTTPError as e:
        error_details = f"HTTP Error: {e.response.status_code} ({e.response.reason})"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details} - {e.response.text}")
        return None, None, error_details
        
    except Exception as e:
        error_details = f"General Error: {str(e)}"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details}")
        return None, None, error_details

# --- [5] التشغيل الرئيسي (الذكي) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v3.0 - بوت YourWallAR - مترجم)...")
    
    SCHEDULE = {
        6: 'morning', 8: 'sunrise', 10: 'nature',
        12: 'city', 14: 'light', 16: 'nature',
        18: 'sunset', 20: 'night', 22: 'space',
        0: 'night sky' 
    }
    
    try:
        IRAQ_TZ = pytz.timezone('Asia/Baghdad')
    except pytz.UnknownTimeZoneError:
        print("!!! خطأ: لم يتم العثور على المنطقة الزمنية 'Asia/Baghdad'.")
        sys.exit(1)

    now_iraq = datetime.datetime.now(IRAQ_TZ)
    current_hour_iraq = now_iraq.hour
    
    print(f"الوقت الحالي (توقيت العراق): {now_iraq.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if current_hour_iraq in SCHEDULE:
        search_query = SCHEDULE[current_hour_iraq]
        print(f">>> (وقت مجدول: {current_hour_iraq}:00) - جاري تشغيل مهمة: '{search_query}'")
        
        image_url, caption, error_msg = get_random_wallpaper(search_query)
        
        if image_url: # (نحن نتحقق فقط من وجود الصورة)
            post_photo_to_telegram(image_url, caption) # (caption قد يكون فارغاً وهذا طبيعي)
        else:
            print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({search_query}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")
            
    else:
        print(f"... (الوقت: {current_hour_iraq}:00) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

