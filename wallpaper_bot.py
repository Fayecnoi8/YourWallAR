# =============================================================================
#    *** بوت YourWallAR - الإصدار 1.0 ***
#
#  (ذكي) يعمل كل ساعة، لكنه ينشر فقط في الأوقات المجدولة.
#  (ذكي) يغير بحثه (query) بناءً على الوقت (صباح، مساء، ليل).
#  (احترافي) يجلب صور عمودية (portrait) مناسبة للهاتف.
#  (احترافي) يرسل الصورة مع اسم المصور ووصفها.
# =============================================================================

import requests
import os
import sys
import datetime
import pytz # (مكتبة للتعامل مع المناطق الزمنية)

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
        # (استخدام جودة .png عالية)
        image_response = requests.get(image_url + "&fm=png&w=1080&q=80", timeout=60)
        image_response.raise_for_status()
        image_data = image_response.content
        
        url = f"{TELEGRAM_API_URL}/sendPhoto"
        payload = { 'chat_id': CHANNEL_USERNAME, 'caption': text_caption, 'parse_mode': 'HTML'}
        files = {'photo': ('wallpaper.png', image_data, 'image/png')}
        
        print("   ... (2/2) جاري رفع الصورة إلى تيليجرام ...")
        response = requests.post(url, data=payload, files=files, timeout=90)
        response.raise_for_status()
        print(">>> تم إرسال (الخلفية) بنجاح!")
        
    except requests.exceptions.RequestException as e:
        error_message = getattr(response, 'text', 'لا يوجد رد من تيليجرام')
        print(f"!!! فشل إرسال (الخلفية): {e} - {error_message}")
        # (إذا فشلت الصورة، لا ترسل شيئاً، لأن قناة الخلفيات لا قيمة لها بدون صور)
        sys.exit(1) # نوقف التشغيل إذا فشلت الصورة

def post_text_to_telegram(text_content):
    """(آمن) إرسال رسالة خطأ نصية فقط إذا فشل الـ API"""
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
    """
    print(f"... جاري جلب خلفية لـ: '{search_query}'")
    headers = {'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'}
    params = {
        'query': search_query,
        'orientation': 'portrait', # (أهم جزء: صور عمودية للهاتف)
        'content_filter': 'high',  # (فلتر أمان)
    }
    
    try:
        response = requests.get(UNSPLASH_API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # (الاستفادة القصوى من الـ API)
        image_url = data['urls']['raw'] # (أعلى جودة)
        description = data.get('alt_description') or data.get('description') or "خلفية مميزة"
        photographer_name = data['user']['name']
        photographer_url = data['user']['links']['html']
        likes = data.get('likes', 0)
        
        print(f">>> تم جلب الصورة بنجاح: {description} (بواسطة {photographer_name})")
        
        # تنسيق الرسالة
        caption = f"📸 <b>{description.capitalize()}</b>\n\n"
        caption += f"📷 <b>بواسطة:</b> <a href='{photographer_url}?utm_source=yourwall_bot&utm_medium=referral'>{photographer_name}</a>\n"
        caption += f"❤️ <b>الإعجابات:</b> {likes}\n\n"
        caption += f"---\n<i>*تابعنا للمزيد من @{CHANNEL_USERNAME.lstrip('@')}*</i>"
        
        return image_url, caption
        
    except Exception as e:
        print(f"!!! فشل جلب البيانات من Unsplash: {e}")
        return None, None

# --- [4] التشغيل الرئيسي (الذكي) ---
def main():
    print("==========================================")
    print(f"بدء تشغيل (v1.0 - بوت YourWallAR - ذكي)...")
    
    # (الجدول الزمني الذكي بتوقيت العراق)
    # هذا هو جدولك، محول إلى قاموس (dictionary)
    SCHEDULE = {
        6: 'morning',
        8: 'morning light',
        10: 'nature',
        12: 'architecture',
        14: 'noon',
        16: 'afternoon',
        18: 'sunset',
        20: 'night', # (تم تغيير 7م و 9م إلى 8م و 10م)
        22: 'stars',
        0: 'dark aesthetic'
    }
    
    # تحديد المنطقة الزمنية (توقيت العراق/بغداد)
    try:
        IRAQ_TZ = pytz.timezone('Asia/Baghdad')
    except pytz.UnknownTimeZoneError:
        print("!!! خطأ: لم يتم العثور على المنطقة الزمنية 'Asia/Baghdad'.")
        sys.exit(1)

    # جلب الوقت الحالي بتوقيت العراق
    now_iraq = datetime.datetime.now(IRAQ_TZ)
    current_hour_iraq = now_iraq.hour
    
    print(f"الوقت الحالي (توقيت العراق): {now_iraq.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # التحقق من الجدول
    if current_hour_iraq in SCHEDULE:
        search_query = SCHEDULE[current_hour_iraq]
        print(f">>> (وقت مجدول: {current_hour_iraq}:00) - جاري تشغيل مهمة: '{search_query}'")
        
        image_url, caption = get_random_wallpaper(search_query)
        
        if image_url and caption:
            post_photo_to_telegram(image_url, caption)
        else:
            print("!!! فشل جلب الصورة أو تنسيقها، تخطي النشر.")
            post_text_to_telegram(f"🚨 حدث خطأ أثناء جلب خلفية ({search_query}). يرجى المراجعة.")
            
    else:
        print(f"... (الوقت: {current_hour_iraq}:00) - لا توجد مهمة مجدولة لهذا الوقت. تخطي.")

    print("==========================================")
    print("... اكتملت المهمة.")

if __name__ == "__main__":
    main()
