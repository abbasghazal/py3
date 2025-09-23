# bot/utils.py
import requests
from config import OPENROUTER_API_KEY, bot, OPENROUTER_API_URL
from database import db

class ContentSender:
    @staticmethod
    def send_stage_content_list(chat_id, stage, subject_name, chapter_num, content_list, is_admin=False):
        """Send list of available content for a chapter in specific stage"""
        if not content_list:
            bot.send_message(chat_id, "⚠️ لا يوجد محتوى متاح لهذا الفصل بعد.")
            return False
        
        subject = db.get_stage_subject(stage, subject_name)
        if not subject:
            return False
        
        from keyboards import Keyboards
        markup = Keyboards.stage_content_list_menu(stage, subject[2], chapter_num, content_list, is_admin)
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        
        # تحديد نوع المحتوى بناءً على الفئة
        category_names = {
            'subjects': 'مادة',
            'explanations': 'شرح',
            'lab': 'مختبر',
            'exams': 'امتحان',
            'exam_models': 'نموذج امتحان'
        }
        
        content_type = category_names.get(subject[3], 'محتوى')
        
        if chapter_num and subject[3] not in ['lab', 'exams', 'exam_models']:
            message = f"📂 محتوى الفصل {chapter_num} - {subject[0]} ({content_type} - المرحلة {stage_name}):\nاختر المحتوى الذي تريد عرضه:"
        else:
            message = f"📂 محتوى {subject[0]} ({content_type} - المرحلة {stage_name}):\nاختر المحتوى الذي تريد عرضه:"
        
        bot.send_message(chat_id, message, reply_markup=markup)
        return True

    @staticmethod
    def send_stage_single_content(chat_id, stage, content_data, content_id=None, subject_key=None, chapter_num=None, is_admin=False):
        """Send specific content item with comments and delete option if admin for specific stage"""
        content_type, file_id, text, description, added_by, subject_key, chapter_num = content_data
        
        try:
            subject = db.get_stage_subject(stage, subject_key)
            subject_name = subject[0] if subject else "مادة غير معروفة"
            
            caption = f"📝 الوصف: {description}\n\n" if description else ""
            stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
            
            # تحديد نوع المحتوى بناءً على الفئة
            category_names = {
                'subjects': 'مادة',
                'explanations': 'شرح',
                'lab': 'مختبر',
                'exams': 'امتحان',
                'exam_models': 'نموذج امتحان'
            }
            
            content_category = category_names.get(subject[3] if subject else 'subjects', 'محتوى')
            
            full_caption = f"{caption}📚 {subject_name} | 🎓 المرحلة {stage_name} | 📖 {content_category}"
            
            if content_type == 'video':
                msg = bot.send_video(chat_id, file_id, caption=full_caption.strip())
            elif content_type == 'document':
                msg = bot.send_document(chat_id, file_id, caption=full_caption.strip())
            elif content_type == 'photo':
                msg = bot.send_photo(chat_id, file_id, caption=full_caption.strip())
            elif content_type == 'text' and text:
                msg = bot.send_message(chat_id, f"{full_caption}\n\n{text}")
            
            from telebot import types
            markup = types.InlineKeyboardMarkup()
            
            if content_id:
                comments = db.get_comments(content_id, stage)
                if comments:
                    comments_text = "💬 التعليقات:\n\n"
                    for i, comment in enumerate(comments[:3], 1):
                        user_name = comment[3] or f"مستخدم {comment[0]}"
                        comments_text += f"{i}. {user_name}: {comment[1][:50]}...\n"
                    
                    if len(comments) > 3:
                        comments_text += f"\n📎 وهناك {len(comments) - 3} تعليقاً آخر"
                    
                    bot.send_message(chat_id, comments_text)
            
            if content_id:
                markup.add(types.InlineKeyboardButton("💬 عرض جميع التعليقات", callback_data=f'stage_comment:list:{stage}:{content_id}'))
                markup.add(types.InlineKeyboardButton("➕ إضافة تعليق", callback_data=f'stage_comment:add:{stage}:{content_id}'))
            
            if is_admin:
                markup.add(types.InlineKeyboardButton("🗑️ حذف هذا المحتوى", callback_data=f'stage_delete_content:select:{stage}:{subject_key}:{chapter_num}'))
            
            bot.send_message(chat_id, "خيارات إضافية:", reply_markup=markup)
            return True
        except Exception as e:
            print(f"Error sending content: {e}")
            bot.send_message(chat_id, f"❌ خطأ في عرض المحتوى: {e}")
            return False

    @staticmethod
    def notify_new_stage_content(stage, subject_key, chapter_num, content_type, description, added_by_name):
        """Notify all users about new content in specific stage"""
        subject = db.get_stage_subject(stage, subject_key)
        if not subject:
            return False
        
        content_type_names = {
            'video': 'فيديو',
            'document': 'ملف',
            'photo': 'صورة',
            'text': 'نص'
        }
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        chapter_info = f" - الفصل {chapter_num}" if chapter_num and subject[3] not in ['lab', 'exams', 'exam_models'] else ""
        
        # تحديد نوع المحتوى بناءً على الفئة
        category_names = {
            'subjects': 'مادة',
            'explanations': 'شرح',
            'lab': 'مختبر',
            'exams': 'امتحان',
            'exam_models': 'نموذج امتحان'
        }
        
        content_category = category_names.get(subject[3], 'محتوى')
        
        message = (
            f"📢 إشعار جديد (المرحلة {stage_name}):\n"
            f"قام الأدمن {added_by_name} برفع {content_type_names.get(content_type, 'محتوى')} جديد\n"
            f"📚 لـ {content_category} {subject[0]}{chapter_info}\n"
            f"📝 الوصف: {description if description else 'لا يوجد وصف'}"
        )
        
        users = db.get_all_users()
        success = 0
        failures = 0
        
        for user_id in users:
            try:
                # إرسال الإشعار فقط لمستخدمي نفس المرحلة
                user_stage_data = db.get_user_stage(user_id)
                if user_stage_data and user_stage_data[0] == stage:
                    bot.send_message(user_id, message)
                    success += 1
            except Exception as e:
                print(f"Failed to send notification to {user_id}: {e}")
                failures += 1
                
        return success, failures

class AIHandler:
    @staticmethod
    def ask_question(prompt):
        """Send question to OpenRouter API and get response"""
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenRouter API error: {e}")
            return "❌ حدث خطأ أثناء الحصول على الإجابة. يرجى المحاولة لاحقاً."

def check_subscription(user_id):
    """Check if user is subscribed to required channel"""
    channel_info = db.get_required_channel()
    if not channel_info:
        return True
    
    try:
        chat_member = bot.get_chat_member(channel_info[0], user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def send_subscription_message(chat_id):
    """Send message asking user to subscribe to channel"""
    channel_info = db.get_required_channel()
    if not channel_info:
        return False
    
    from telebot import types
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "اشترك في القناة أولاً",
        url=f"https://t.me/{channel_info[1]}"
    ))
    markup.add(types.InlineKeyboardButton(
        "✅ لقد اشتركت",
        callback_data="check_subscription"
    ))
    
    bot.send_message(
        chat_id,
        f"📢 يرجى الاشتراك في القناة الرسمية @{channel_info[1]} أولاً لتتمكن من استخدام البوت",
        reply_markup=markup
    )
    return True