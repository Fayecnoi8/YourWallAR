# =============================================================================
#    *** بوت YourWallAR - الإصدار 1.2 (التصحيح الذكي) ***
#
#  (v1.2) تم تغيير جودة الصورة من 'raw' (خام) إلى 'regular' (عالية)
#         لمنع فشل التحميل (Timeout).
#  (v1.2) أصبح البوت يرسل رسالة الخطأ "الحقيقية" من الـ API
#         إلى القناة مباشرة لتشخيص المشكلة.
# =============================================================================

import requests
import os
import sys
import datetime
import pytz

# --- [1] الإعدادات والمفاتيح السرية (3 مفاتيح مطلوبة) ---
try:
    BOT_TOKEN = os.environ['BOT_TOKEN']
    CHANNEL_USERNAME = os.environ['CHANNEL_USERNAME'] # يجب أن يبدأ بـ @
    UNSPLASH_ACCESS_KEY = os.environ['UNSPLASH_ACCESS_KEY']
    
except KeyError as e:
    print(f"!!! خطأ: متغير البيئة الأساسي غير موجود: {e}")
    print("!!! هل تذكرت إضافة (BOT_TOKEN, CHANNEL_USERNAME, UNSPLASH_ACCESS_KEY)؟")
    sys.exit(1)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

# --- [2] الدوال المساعدة (إرسال الرسائل - آمنة) ---

def post_photo_to_telegram(image_url, text_caption):
    """(آمن) إرسال صورة + نص (مع خدعة الرفع)"""
    print(f"... جاري إرسال (الخلفية) إلى {CHANNEL_USERNAME} ...")
    response = None 
    try:
        print(f"   ... (1/2) جاري تحميل الصورة من: {image_url}")
        # (v1.2) تم تغيير جودة الصورة من 'raw' إلى 'regular' (jpg)
        image_response = requests.get(image_url, timeout=60) # (لم نعد بحاجة لإضافة بارامترات للجودة)
        image_response.raise_for_status()
        image_data = image_response.content
        
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        payload = { 'chat_id': CHANNEL_USERNAME, 'caption': text_caption, 'parse_mode': 'HTML'}
        # (v1.2) تغيير نوع الملف إلى 'image/jpeg'
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


# --- [3] دالة جلب البيانات (Unsplash) ---

def get_random_wallpaper(search_query):
    """
    يجلب صورة عشوائية عالية الجودة من Unsplash بناءً على البحث.
    (v1.2) تم تعديل هذه الدالة لترجع الخطأ الفعلي.
    """
    print(f"... جاري جلب خلفية لـ: '{search_query}'")
    headers = {'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'}
    params = {
        'query': search_query,
        'orientation': 'portrait',
        'content_filter': 'high',
    }
    
    response_api = None
    try:
        response_api = requests.get(UNSPLASH_API_URL, headers=headers, params=params, timeout=30)
        response_api.raise_for_status() # سيفشل هنا إذا كان 401, 403, 404
        data = response_api.json()
        
        # (v1.2) استخدام 'regular' بدلاً من 'raw'
        image_url = data['urls']['regular'] 
        description = data.get('alt_description') or data.get('description') or "خلفية مميزة"
        photographer_name = data['user']['name']
        photographer_url = data['user']['links']['html']
        likes = data.get('likes', 0)
        
        print(f">>> تم جلب الصورة بنجاح: {description} (بواسطة {photographer_name})")
        
        caption = f"📸 <b>{description.capitalize()}</b>\n\n"
        caption += f"📷 <b>بواسطة:</b> <a href='{photographer_url}?utm_source=yourwall_bot&utm_medium=referral'>{photographer_name}</a>\n"
        caption += f"❤️ <b>الإعجابات:</b> {likes}\n\n"
        caption += f"---\n<i>*تابعنا للمزيد من @{CHANNEL_USERNAME.lstrip('@')}*</i>"
        
        return image_url, caption, None # (لا يوجد خطأ)
        
    except requests.exceptions.HTTPError as e:
        # (هذا هو الخطأ الأهم: 401, 403, 404)
        error_details = f"HTTP Error: {e.response.status_code} (Unauthorized / Not Found)"
        print(f"!!! فشل جلب البيانات من Unsplash: {error_details} - {e.response.text}")
        return None, None, error_details # (إرجاع رسالة الخطأ)
        
    except Exception as e:
        # (أخطاء أخرى مثل انقطاع الاتصال أو JSON)
        error_details = f"General Error: {str(e)}"
        print(f"!!! فشل جلب البيانات من Unsplash: {error_details}")
        return None, None, error_details # (إرجاع رسالة الخطأ)

# --- [4] التشغيل الرئيسي (الذكي) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v1.2 - بوت YourWallAR - تصحيح ذكي)...")
    
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
        
        # (v1.2) تم تعديل هذه الدالة لترجع 3 قيم
        image_url, caption, error_msg = get_random_wallpaper(search_query)
        
        if image_url and caption:
            # (نجاح)
            post_photo_to_telegram(image_url, caption)
        else:
            # (فشل)
            print(f"!!! فشل جلب الصورة. السبب: {error_msg}")
            # (إرسال رسالة الخطأ المحددة إلى تيليجرام)
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({search_query}).\n\n<b>السبب الفني:</b>\n<pre>{error_msg}</pre>")
            
    else:
        print(f"... (الوقت: {current_hour_iraq}:00) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()

