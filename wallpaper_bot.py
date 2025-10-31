# =============================================================================
#    *** بوت YourWallAR - الإصدار 2.0 (التبديل إلى Pexels) ***
#
#  (v2.0) تم التبديل بالكامل من Unsplash (الذي يسبب خطأ 401) إلى Pexels.
#  (v2.0) يتطلب الآن مفتاح سري جديد: PEXELS_API_KEY
#  (v2.0) يستخدم آلية بحث مختلفة للحصول على صور عشوائية.
# =============================================================================

import requests
import os
import sys
import datetime
import pytz
import random # (مطلوب لـ Pexels للحصول على صور عشوائية)

# --- [1] الإعدادات والمفاتيح السرية (3 مفاتيح مطلوبة) ---
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
    PEXELS_API_KEY = os.environ['PEXELS_API_KEY'] # (تم تغيير المفتاح)
    
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    print("!!! هل تذكرت إضافة (BOT_TOKEN, CHANNEL_USERNAME, PEXELS_API_KEY)؟")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
# (تم تغيير رابط الـ API إلى Pexels)
PEXELS_API_URL = "https://api.pexels.com/v1/search" 

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
        payload = { 'chat_id': CHANNEL_USERNAME, 'caption': text_caption, 'parse_mode': 'HTML'}
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
        print(f"!!! فشل إrsال (رسالة الخطأ النصية) أيضاً: {e}")


# --- [3] دالة جلب البيانات (Pexels) ---

def get_random_wallpaper(search_query):
    """
    يجلب صورة عشوائية عالية الجودة من Pexels بناءً على البحث.
    """
    print(f"... جاري جلب خلفية لـ: '{search_query}' (من Pexels)")
    
    # (Pexels يتطلب المفتاح في الـ Headers)
    headers = {'Authorization': PEXELS_API_KEY}
    
    # (Pexels ليس لديه 'random' حقيقي، لذا نبحث ونختار صفحة عشوائية)
    params = {
        'query': search_query,
        'orientation': 'portrait',
        'per_page': 1, # (نريد صورة واحدة فقط)
        'page': random.randint(1, 100) # (نختار صورة عشوائية من أول 100 صفحة)
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
        
        # (v2.0) استخدام 'large' أو 'original' من Pexels
        image_url = photo['src']['large'] # (جودة ممتازة وليست ضخمة)
        description = photo.get('alt') or "خلفية مميزة"
        photographer_name = photo['photographer']
        photographer_url = photo['photographer_url']
        
        print(f">>> تم جلب الصورة بنجاح: {description} (بواسطة {photographer_name})")
        
        caption = f"📸 <b>{description.capitalize()}</b>\n\n"
        caption += f"📷 <b>بواسطة:</b> <a href='{photographer_url}'>{photographer_name}</a>\n"
        caption += f"🌐 <b>(عبر Pexels.com)</b>\n\n"
        caption += f"---\n<i>*تابعنا للمزيد من @{CHANNEL_USERNAME.lstrip('@')}*</i>"
        
        return image_url, caption, None # (لا يوجد خطأ)
        
    except requests.exceptions.HTTPError as e:
        error_details = f"HTTP Error: {e.response.status_code} ({e.response.reason})"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details} - {e.response.text}")
        return None, None, error_details # (إرجاع رسالة الخطأ)
        
    except Exception as e:
        error_details = f"General Error: {str(e)}"
        print(f"!!! فشل جلب البيانات من Pexels: {error_details}")
        return None, None, error_details # (إرجاع رسالة الخطأ)

# --- [4] التشغيل الرئيسي (الذكي) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v2.0 - بوت YourWallAR - Pexels)...")
    
    # (جدول زمني آمن v1.1)
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
        
        if image_url and caption:
            post_photo_to_telegram(image_url, caption)
        else:
            print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({search_query}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")
            
    else:
        print(f"... (الوقت: {current_hour_iraq}:00) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

