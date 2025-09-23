# bot/handlers.py
from telebot import types
from database import db
from keyboards import Keyboards
from utils import ContentSender, AIHandler, check_subscription, send_subscription_message
from config import DEVELOPER_ID, bot

# دالة مساعدة للحصول على عدد المواد لكل مرحلة
def get_stage_subjects_count(stage):
    """الحصول على عدد المواد لكل مرحلة"""
    counts = {
        1: {'subjects': 11, 'explanations': 11, 'lab': 3, 'exams': 11, 'exam_models': 11},
        2: {'subjects': 11, 'explanations': 11, 'lab': 3, 'exams': 11, 'exam_models': 11},
        3: {'subjects': 8, 'explanations': 8, 'lab': 2, 'exams': 8, 'exam_models': 8},
        4: {'subjects': 7, 'explanations': 7, 'lab': 6, 'exams': 7, 'exam_models': 7}
    }
    return counts.get(stage, counts[4])

# ========== Bot Handlers ========== #
@bot.message_handler(commands=['start', 'admin'])
def handle_start(message):
    user_id = message.from_user.id
    
    # التحقق من الحظر
    if db.is_banned(user_id):
        bot.send_message(user_id, "⛔ تم حظرك من استخدام هذا البوت.")
        return
    
    is_admin = db.is_admin(user_id)
    is_developer = user_id == DEVELOPER_ID
    
    # التحقق من الاشتراك إذا كانت هناك قناة إجبارية
    if not check_subscription(user_id):
        send_subscription_message(message.chat.id)
        return
    
    # التحقق إذا كان المستخدم جديداً
    user_stage = db.get_user_stage(user_id)
    if not user_stage:
        # طلب الاسم الثلاثي من المستخدم الجديد
        msg = bot.send_message(
            message.chat.id,
            "👤 مرحباً بك! يرجى إرسال اسمك الثلاثي:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_user_name)
        return
    
    # إذا كان المستخدم مسجلاً مسبقاً، عرض القائمة الرئيسية لمرحلته
    stage = user_stage[0]
    stage_counts = get_stage_subjects_count(stage)
    stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
    
    welcome_msg = (
        f"أهلاً {user_stage[1]}\n"
        f"• بـوت المـرحلة الـ{stage_name} •\n"
        '• ڪل شيء هـنا لـوجه الله •\n'
        '• لـتوفـير الـوقـت والجـهد •\n'
        '• مـطور الـبوت @Shahm41•\n'
    )
    
    if message.text == '/admin' and not is_admin:
        bot.reply_to(message, "⛔ ليس لديك صلاحية المسؤول")
        return
    
    bot.send_message(message.chat.id, welcome_msg, reply_markup=Keyboards.main_menu(user_id, stage))

def process_user_name(message):
    """Process user's full name and show stage selection"""
    user_id = message.from_user.id
    full_name = message.text.strip()
    
    if len(full_name.split()) < 2:
        msg = bot.send_message(
            message.chat.id,
            "❌ يرجى إرسال الاسم الثلاثي بشكل صحيح (مثال:  عباس غزوان عبد):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_user_name)
        return
    
    # تسجيل المستخدم في قاعدة البيانات
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # عرض أزرار اختيار المرحلة
    bot.send_message(
        message.chat.id,
        f"👤 شكراً {full_name}\nالآن اختر مرحلتك الدراسية:",
        reply_markup=Keyboards.stage_selection_menu(full_name)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('register_stage'))
def handle_register_stage(call):
    """Handle stage selection for new user"""
    try:
        data = call.data.split(':')
        stage = int(data[1])
        full_name = ':'.join(data[2:])  # في حالة وجود : في الاسم
        
        user_id = call.from_user.id
        
        # تعيين المرحلة للمستخدم
        db.set_user_stage(user_id, full_name, stage)
        
        # إعلام المطور بمستخدم جديد
        if user_id == DEVELOPER_ID:
            new_user_info = (
                f"👤 مستخدم جديد:\n"
                f"🆔 ID: {user_id}\n"
                f"👤 الاسم: {full_name}\n"
                f"🎓 المرحلة: {stage}\n"
                f"📌 اليوزر: @{call.from_user.username}" if call.from_user.username else "📌 بدون يوزرنيم"
            )
            bot.send_message(DEVELOPER_ID, new_user_info)
        
        # عرض القائمة الرئيسية للمرحلة
        stage_counts = get_stage_subjects_count(stage)
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        welcome_msg = (
            f"أهلاً {full_name}\n"
            f"• بـوت المـرحلة الـ{stage_name} •\n"
            f"• المواد: {stage_counts['subjects']} | الشروحات: {stage_counts['explanations']} | المختبر: {stage_counts['lab']} •\n"
            '• ڪل شيء هـنا لـوجه الله •\n'
            '• لـتوفـير الـوقـت والجـهد •\n'
            '• مـطور الـبوت @Shahm41•\n'
        )
        
        bot.edit_message_text(
            welcome_msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.main_menu(user_id, stage)
        )
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def handle_check_subscription(call):
    user_id = call.from_user.id
    
    if check_subscription(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم يتم الاشتراك بعد، يرجى الاشتراك في القناة أولاً")

@bot.callback_query_handler(func=lambda call: call.data == 'delete_message')
def handle_delete_message(call):
    """Delete the current message"""
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        bot.answer_callback_query(call.id, "تم الإغلاق")

@bot.message_handler(commands=['بحث'])
def handle_search_command(message):
    # التحقق من أن الأمر أتى من مجموعة
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "⚠️ هذا الأمر متاح فقط في المجموعات")
        return
        
    # التحقق من وجود نص للبحث
    if not message.text or len(message.text.split()) < 2:
        bot.reply_to(message, "⚠️ يرجى إرسال نص للبحث مع الأمر. مثال: /بحث الكهرومغناطيسية")
        return
        
    # استخراج كلمة البحث
    search_query = ' '.join(message.text.split()[1:])
    search_channels = db.get_search_channels()
    
    if not search_channels:
        bot.reply_to(message, "⚠️ لم يتم إعداد قنوات للبحث بعد")
        return
        
    bot.reply_to(message, f"🔍 جاري البحث عن: {search_query}...")
    
    results_found = False
    for channel in search_channels:
        try:
            # البحث في القناة باستخدام الرسائل التي تم تخزينها
            result_msg = f"تم العثور على نتائج في قناة {channel[2]}:\n"
            result_msg += f"📌 رابط القناة: https://t.me/{channel[1]}\n"
            result_msg += f"🔍 كلمة البحث: {search_query}\n"
            result_msg += "🔗 رابط الرسالة: https://t.me/shahmplus/123"  # رابط مثال
            
            bot.send_message(message.chat.id, result_msg)
            results_found = True
        except Exception as e:
            print(f"Error searching in channel {channel[0]}: {e}")
    
    if not results_found:
        bot.reply_to(message, "⚠️ لم يتم العثور على نتائج لبحثك")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        user_id = call.from_user.id
        
        # التحقق من الحظر
        if db.is_banned(user_id):
            bot.answer_callback_query(call.id, "⛔ تم حظرك من استخدام هذا البوت")
            return
        
        is_admin = db.is_admin(user_id)
        is_developer = user_id == DEVELOPER_ID
        
        # التحقق من الاشتراك إذا كانت هناك قناة إجبارية
        if not check_subscription(user_id):
            bot.answer_callback_query(call.id, "❌ يرجى الاشتراك في القناة أولاً")
            send_subscription_message(call.message.chat.id)
            return
            
        data = call.data.split(':')
        
        if data[0].startswith('stage_'):
            handle_stage_callbacks(call, data)
        elif data[0] == 'main':
            handle_main_menu(call, data[1], is_admin)
        elif data[0] == 'admin':
            handle_admin_management(call, data[1], data[2:], is_developer)
        elif data[0] == 'comment':
            handle_comment(call, data[1], data[2:])
        elif data[0] == 'support':
            handle_support(call, data[1])
        elif data[0] == 'ai':
            handle_ai(call, data[1], data[2:])
        elif data[0] == 'support_reply':
            handle_support_reply_button(call, data[1])
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)}")
        print(f"Callback error: {e}")

def handle_support_reply_button(call, ticket_id):
    """معالجة ضغط زر الرد على تذكرة الدعم"""
    try:
        if not db.is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "⛔ صلاحية مرفوضة")
            return
            
        # طلب رسالة الرد من الأدمن
        msg = bot.send_message(
            call.message.chat.id,
            f"📩 أرسل ردك على تذكرة الدعم #{ticket_id}:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_support_reply, ticket_id, call.message.message_id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)}")

def process_support_reply(message, ticket_id, original_message_id):
    """معالجة رد الأدمن على تذكرة الدعم"""
    try:
        if not message.text:
            bot.reply_to(message, "❌ يرجى إرسال نص الرد")
            return
        
        # الحصول على معلومات التذكرة
        ticket_info = db.get_ticket_info(ticket_id)
        if not ticket_info:
            bot.reply_to(message, "❌ التذكرة غير موجودة")
            return
        
        user_id = ticket_info[0]
        user_message = ticket_info[1]
        stage = ticket_info[2]
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        
        # إرسال الرد إلى المستخدم
        reply_msg = (
            f"📩 رد من الدعم على تذكرتك (المرحلة {stage_name}):\n\n"
            f"💬 سؤالك: {user_message}\n\n"
            f"✅ الرد: {message.text}"
        )
        
        try:
            bot.send_message(user_id, reply_msg)
            
            # حذف الرسالة الأصلية التي تحتوي على زر الرد
            try:
                bot.delete_message(message.chat.id, original_message_id)
            except:
                pass
                
            # إعلام الأدمن بنجاح الإرسال
            bot.reply_to(message, "✅ تم إرسال الرد إلى المستخدم بنجاح")
            
            # حذف التذكرة من قاعدة البيانات بعد الرد
            db.delete_support_ticket(ticket_id)
            
        except Exception as e:
            bot.reply_to(message, f"❌ فشل في إرسال الرد: {e}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في معالجة الرد: {str(e)}")

def handle_stage_callbacks(call, data):
    """Handle all stage-related callbacks"""
    user_id = call.from_user.id
    is_admin = db.is_admin(user_id)
    
    if data[0] == 'stage_1' or data[0] == 'stage_2' or data[0] == 'stage_3' or data[0] == 'stage_4':
        # معالجة القوائم الرئيسية للمراحل
        stage = int(data[0].split('_')[1])
        action = data[1] if len(data) > 1 else 'home'
        handle_stage_main_menu(call, stage, action)
        
    elif data[0] == 'stage_subject':
        # معالجة اختيار المادة في مرحلة معينة
        stage = int(data[1])
        subject_key = data[2]
        handle_stage_subject(call, stage, subject_key, is_admin)
        
    elif data[0] == 'stage_chapter':
        # معالجة اختيار الفصل في مرحلة معينة
        stage = int(data[1])
        subject_key = data[2]
        chapter_num = int(data[3])
        handle_stage_chapter(call, stage, subject_key, chapter_num, is_admin)
        
    elif data[0] == 'stage_view_content':
        # معالجة عرض المحتوى في مرحلة معينة
        stage = int(data[1])
        content_id = int(data[2])
        handle_stage_view_content(call, stage, content_id)
        
    elif data[0] == 'stage_upload':
        # معالجة رفع المحتوى في مرحلة معينة
        handle_stage_upload(call, data[1], data[2:], is_admin)
        
    elif data[0] == 'stage_delete_content':
        # معالجة حذف المحتوى في مرحلة معينة
        handle_stage_delete_content(call, data[1], data[2:], is_admin)
        
    elif data[0] == 'stage_comment':
        # معالجة التعليقات في مرحلة معينة
        handle_stage_comment(call, data[1], data[2:])

def handle_stage_main_menu(call, stage, action):
    """Handle main menu for specific stage"""
    if action == 'home':
        user_stage = db.get_user_stage(call.from_user.id)
        stage_counts = get_stage_subjects_count(stage)
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        
        bot.edit_message_text(
            f"• أهلاً بــك • \n"
            f'• بـوت المـرحلة الـ{stage_name} •\n'
            '• ڪل شيء هـنا لـوجه الله•\n'
            '• لـتوفـير الـوقـت والجـهد •\n'
            '• مـطور الـبوت @Shahm41•',
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.main_menu(call.from_user.id, stage)
        )
    else:
        category_map = {
            'subjects': 'subjects',
            'explanations': 'explanations',
            'lab': 'lab',
            'exams': 'exams'
        }
        
        if action not in category_map:
            bot.answer_callback_query(call.id, "❌ القسم غير موجود")
            return
            
        stage_counts = get_stage_subjects_count(stage)
        category_count = stage_counts.get(category_map[action], 0)
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        
        category_names = {
            'subjects': 'المواد الدراسية',
            'explanations': 'الشروحات',
            'lab': 'المختبر',
            'exams': 'الامتحانات'
        }
        
        bot.edit_message_text(
            f"اختر من {category_names[action]} (المرحلة {stage_name}) - العدد: {category_count}:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.stage_category_menu(stage, category_map[action], db.is_admin(call.from_user.id))
        )

def handle_stage_subject(call, stage, subject_key, is_admin):
    """Handle subject selection for specific stage"""
    subject = db.get_stage_subject(stage, subject_key)
    if not subject:
        bot.answer_callback_query(call.id, "❌ المادة غير موجودة")
        return
    
    # إذا كانت من فئة المختبر أو الامتحانات، عرض المحتوى مباشرة بدون فصول
    if subject[3] in ['lab', 'exams', 'exam_models']:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        content_list = db.get_stage_chapter_content_list(stage, subject_key, 1)  # استخدام فصل افتراضي (1) للمواد بدون فصول
        
        if len(content_list) == 1:
            content_data = db.get_stage_content_by_id(stage, content_list[0][0])
            ContentSender.send_stage_single_content(
                call.message.chat.id, 
                stage,
                content_data,
                content_id=content_list[0][0],
                subject_key=subject_key,
                chapter_num=1,
                is_admin=is_admin
            )
        elif len(content_list) > 1:
            ContentSender.send_stage_content_list(
                call.message.chat.id,
                stage,
                subject_key,
                1,
                content_list,
                is_admin
            )
        else:
            bot.send_message(call.message.chat.id, "⚠️ لا يوجد محتوى متاح بعد.")
        
        # إضافة زر العودة وزر رفع محتوى جديد للمسؤولين
        markup = types.InlineKeyboardMarkup()
        if is_admin:
            markup.add(types.InlineKeyboardButton(
                "➕ رفع محتوى جديد",
                callback_data=f'stage_upload:type:{stage}:{subject_key}'
            ))
        
        markup.add(types.InlineKeyboardButton(
            "العودة",
            callback_data=f'stage_{stage}:{subject[3]}'
        ))
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        bot.send_message(
            call.message.chat.id,
            f"▫️ {subject[0]} (المرحلة {stage_name})",
            reply_markup=markup
        )
        return
        
    # عرض قائمة الفصول للمواد العادية
    stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
    bot.edit_message_text(
        f"اختر الفصل - {subject[0]} (المرحلة {stage_name}):",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=Keyboards.stage_chapters_menu(stage, subject_key, is_admin)
    )

def handle_stage_chapter(call, stage, subject_key, chapter_num, is_admin):
    """Handle chapter selection for specific stage"""
    subject = db.get_stage_subject(stage, subject_key)
    if not subject:
        bot.answer_callback_query(call.id, "❌ المادة غير موجودة")
        return
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    content_list = db.get_stage_chapter_content_list(stage, subject_key, chapter_num)
    
    if len(content_list) == 1:
        content_data = db.get_stage_content_by_id(stage, content_list[0][0])
        ContentSender.send_stage_single_content(
            call.message.chat.id, 
            stage,
            content_data,
            content_id=content_list[0][0],
            subject_key=subject_key,
            chapter_num=chapter_num,
            is_admin=is_admin
        )
    elif len(content_list) > 1:
        ContentSender.send_stage_content_list(
            call.message.chat.id,
            stage,
            subject_key,
            chapter_num,
            content_list,
            is_admin
        )
    else:
        bot.send_message(call.message.chat.id, "⚠️ لا يوجد محتوى متاح لهذا الفصل بعد.")
    
    markup = types.InlineKeyboardMarkup()
    if is_admin:
        markup.add(types.InlineKeyboardButton(
            "➕ رفع محتوى جديد",
            callback_data=f'stage_upload:type:{stage}:{subject_key}:{chapter_num}'
        ))
    
    markup.add(types.InlineKeyboardButton(
        "العودة",
        callback_data=f'stage_{stage}:{subject[3]}'
    ))
    
    stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
    bot.send_message(
        call.message.chat.id,
        f"▫️ {subject[0]} - الفصل {chapter_num} (المرحلة {stage_name})",
        reply_markup=markup
    )

def handle_stage_view_content(call, stage, content_id):
    """Handle viewing specific content for stage"""
    try:
        content_id = int(content_id)
        content_data = db.get_stage_content_by_id(stage, content_id)
        
        if not content_data:
            bot.answer_callback_query(call.id, "❌ المحتوى غير موجود")
            return
        
        # الحصول على معلومات الفصل والمادة لعرض زر الحذف إذا كان أدمن
        subject_key = content_data[5]
        chapter_num = content_data[6]
        is_admin = db.is_admin(call.from_user.id)
        
        ContentSender.send_stage_single_content(
            call.message.chat.id,
            stage,
            content_data,
            content_id=content_id,
            subject_key=subject_key,
            chapter_num=chapter_num,
            is_admin=is_admin
        )
        
        bot.answer_callback_query(call.id, "تم عرض المحتوى المحدد")
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {str(e)}")
        print(f"Content view error: {e}")

def handle_stage_upload(call, action, ref_data, is_admin):
    """Handle content upload for specific stage"""
    if not is_admin:
        bot.answer_callback_query(call.id, "⛔ صلاحية مرفوضة")
        return
    
    stage = int(ref_data[0])
    subject_key = ref_data[1]
    chapter_num = int(ref_data[2]) if len(ref_data) > 2 else None
    
    subject = db.get_stage_subject(stage, subject_key)
    if not subject:
        bot.answer_callback_query(call.id, "❌ المادة غير موجودة")
        return
    
    if action == 'type':
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        location = f"للفصل {chapter_num} من " if chapter_num else ""
        bot.edit_message_text(
            f"اختر نوع المحتوى لرفعه {location}مادة {subject[0]} (المرحلة {stage_name}):",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.stage_upload_type_menu(stage, subject_key, chapter_num)
        )
    elif action in ['video', 'doc', 'photo', 'text']:
        content_type_map = {
            'video': 'فيديو',
            'doc': 'ملف',
            'photo': 'صورة',
            'text': 'نص'
        }
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        location = f"للفصل {chapter_num} من مادة {subject[0]}" if chapter_num else f"للمادة {subject[0]}"
        msg = bot.send_message(
            call.message.chat.id,
            f"⬆️ أرسل {content_type_map[action]} {location} (المرحلة {stage_name}):\n"
            f"(اسم المادة: {subject[0]})\n\n"
            "📌 الرجاء إرسال الوصف أولاً (أو اكتب 'بدون' لعدم إضافة وصف):",
            reply_markup=types.ForceReply()
        )
        
        bot.register_next_step_handler(msg, process_stage_description, stage, subject_key, chapter_num, action, call.from_user.id)

def process_stage_description(message, stage, subject_key, chapter_num, action, added_by):
    """Process description for stage content upload"""
    try:
        description = message.text if message.text.lower() != 'بدون' else None
        
        content_type_map = {
            'video': '🎥 الآن، أرسل الفيديو:',
            'doc': '📄 الآن، أرسل الملف:',
            'photo': '🖼️ الآن، أرسل الصورة:',
            'text': '📝 الآن، أرسل النص:'
        }
        
        msg = bot.send_message(
            message.chat.id,
            content_type_map[action],
            reply_markup=types.ForceReply()
        )
        
        bot.register_next_step_handler(msg, process_stage_content_upload, stage, subject_key, chapter_num, action, description, added_by)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إدخال الوصف: {str(e)}")

def process_stage_content_upload(message, stage, subject_key, chapter_num, action, description, added_by):
    """Process content upload for specific stage"""
    try:
        subject = db.get_stage_subject(stage, subject_key)
        if not subject:
            raise ValueError("المادة غير موجودة")
        
        if action == 'video':
            if not message.video:
                raise ValueError("لم يتم إرسال فيديو")
            file_id = message.video.file_id
            content_type = 'video'
            text = None
        elif action == 'doc':
            if not message.document:
                raise ValueError("لم يتم إرسال ملف")
            file_id = message.document.file_id
            content_type = 'document'
            text = None
        elif action == 'photo':
            if not message.photo:
                raise ValueError("لم يتم إرسال صورة")
            file_id = message.photo[-1].file_id  # نأخذ أعلى دقة للصورة
            content_type = 'photo'
            text = None
        elif action == 'text':
            if not message.text:
                raise ValueError("لم يتم إرسال نص")
            file_id = None
            content_type = 'text'
            text = message.text
        
        content_number = db.add_stage_content(
            stage=stage,
            subject_key=subject_key,
            chapter_num=chapter_num if chapter_num else 1,  # فصل افتراضي للمواد بدون فصول
            content_type=content_type,
            file_id=file_id,
            text=text,
            description=description,
            added_by=added_by
        )
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        location = f"الفصل {chapter_num} من " if chapter_num else ""
        bot.reply_to(
            message,
            f"✅ تم رفع {content_type} بنجاح لـ{location}مادة {subject[0]} (المرحلة {stage_name})\n"
            f"📝 الوصف: {description if description else 'لا يوجد وصف'}\n"
            f"🔢 الرقم التسلسلي: {content_number}"
        )
        
        # إرسال إشعار لجميع المستخدمين
        added_by_name = message.from_user.first_name or "أدمن"
        ContentSender.notify_new_stage_content(
            stage=stage,
            subject_key=subject_key,
            chapter_num=chapter_num,
            content_type=content_type,
            description=description,
            added_by_name=added_by_name
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ فشل الرفع: {str(e)}")

def handle_stage_delete_content(call, action, data, is_admin):
    """Handle content deletion for specific stage"""
    if not is_admin:
        bot.answer_callback_query(call.id, "⛔ صلاحية مرفوضة")
        return
    
    if action == 'select':
        # عرض قائمة المحتوى للحذف
        stage = int(data[0])
        subject_key = data[1]
        chapter_num = int(data[2])
        
        content_list = db.get_stage_chapter_content_list(stage, subject_key, chapter_num)
        if not content_list:
            bot.answer_callback_query(call.id, "⚠️ لا يوجد محتوى للحذف")
            return
            
        markup = Keyboards.stage_delete_content_menu(stage, subject_key, chapter_num, content_list)
        bot.edit_message_text(
            "اختر المحتوى الذي تريد حذفه:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    elif action == 'confirm':
        # تأكيد الحذف
        stage = int(data[0])
        content_id = int(data[1])
        content_data = db.get_stage_content_by_id(stage, content_id)
        
        if not content_data:
            bot.answer_callback_query(call.id, "❌ المحتوى غير موجود")
            return
            
        markup = Keyboards.confirm_delete_menu(stage, content_id)
        bot.edit_message_text(
            "⚠️ هل أنت متأكد من حذف هذا المحتوى؟",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    elif action == 'execute':
        # تنفيذ الحذف
        stage = int(data[0])
        content_id = int(data[1])
        
        if db.delete_stage_content(stage, content_id):
            bot.answer_callback_query(call.id, "✅ تم حذف المحتوى بنجاح")
            bot.edit_message_text(
                "✅ تم حذف المحتوى بنجاح",
                call.message.chat.id,
                call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "❌ فشل في حذف المحتوى")
            
    elif action == 'cancel':
        # إلغاء الحذف
        bot.answer_callback_query(call.id, "تم الإلغاء")
        bot.delete_message(call.message.chat.id, call.message.message_id)

def handle_stage_comment(call, action, data):
    """Handle comments for specific stage"""
    if action == 'add':
        if not data:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        stage = int(data[0])
        content_id = int(data[1])
        content_data = db.get_stage_content_by_id(stage, content_id)
        content_title = content_data[3] if content_data else "محتوى غير معروف"
        
        msg = bot.send_message(
            call.message.chat.id,
            f"💬 أرسل تعليقك أو استفسارك حول المحتوى: {content_title} (المرحلة {['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]})",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_stage_comment, stage, content_id, call.from_user.id, content_title)
        
    elif action == 'list':
        if not data:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        stage = int(data[0])
        content_id = int(data[1])
        comments = db.get_comments(content_id, stage)
        
        if not comments:
            bot.answer_callback_query(call.id, "⚠️ لا توجد تعليقات بعد")
            return
            
        message = f"💬 التعليقات على المحتوى (المرحلة {['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]}):\n\n"
        for i, comment in enumerate(comments, 1):
            user_info = f"{comment[3]}" if comment[3] else f"@{comment[4]}" if comment[4] else f"المستخدم {comment[0]}"
            message += f"📌 {i}. {user_info}\n"
            message += f"   📅 {comment[2]}\n"
            message += f"   💬 {comment[1]}\n\n"
            
        # إضافة زر لإضافة تعليق جديد
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ إضافة تعليق جديد", callback_data=f'stage_comment:add:{stage}:{content_id}'))
        markup.add(types.InlineKeyboardButton("إغلاق", callback_data='delete_message'))
        
        try:
            bot.send_message(call.message.chat.id, message, reply_markup=markup)
        except:
            # إذا كانت الرسالة طويلة جداً، تقسيمها
            if len(message) > 4000:
                parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
                for part in parts[:-1]:
                    bot.send_message(call.message.chat.id, part)
                bot.send_message(call.message.chat.id, parts[-1], reply_markup=markup)
            else:
                raise

def process_stage_comment(message, stage, content_id, user_id, content_title):
    """Process comment addition for specific stage"""
    try:
        if not message.text:
            bot.reply_to(message, "❌ يرجى إرسال نص التعليق")
            return
        
        # إضافة التعليق إلى قاعدة البيانات
        if db.add_comment(content_id, user_id, message.text, content_title, stage):
            bot.reply_to(message, "✅ تم إضافة تعليقك بنجاح")
        else:
            raise ValueError("فشل في إضافة التعليق")
        
        # إعلام المطور بتعليق جديد
        user_info = f"{message.from_user.first_name} (@{message.from_user.username})" if message.from_user.username else message.from_user.first_name
        notify_msg = (
            f"💬 تعليق جديد (المرحلة {['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]}):\n"
            f"👤 المستخدم: {user_info}\n"
            f"🆔 ID: {user_id}\n"
            f"📌 على المحتوى: {content_title}\n\n"
            f"💬 النص: {message.text}"
        )
        bot.send_message(DEVELOPER_ID, notify_msg)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إضافة التعليق: {str(e)}")

def handle_main_menu(call, action, is_admin):
    """Handle main menu callbacks"""
    # الحصول على مرحلة المستخدم
    user_stage = db.get_user_stage(call.from_user.id)
    stage = user_stage[0] if user_stage else 4
    
    if action == 'home':
        stage_counts = get_stage_subjects_count(stage)
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        
        bot.edit_message_text(
            f"• أهلاً بــك • \n"
            f'• بـوت المـرحلة الـ{stage_name} •\n'
            f'• المواد: {stage_counts["subjects"]} | الشروحات: {stage_counts["explanations"]} | المختبر: {stage_counts["lab"]} •\n'
            '• ڪل شيء هـنا لـوجه الله•\n'
            '• لـتوفـير الـوقـت والجـهد •\n'
            '• مـطور الـبوت @Shahm41•',
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.main_menu(call.from_user.id, stage)
        )
    else:
        category_map = {
            'subjects': 'subjects',
            'explanations': 'explanations',
            'lab': 'lab',
            'exams': 'exams'
        }
        
        if action not in category_map:
            bot.answer_callback_query(call.id, "❌ القسم غير موجود")
            return
            
        stage_counts = get_stage_subjects_count(stage)
        category_count = stage_counts.get(category_map[action], 0)
        
        category_names = {
            'subjects': 'المواد الدراسية',
            'explanations': 'الشروحات',
            'lab': 'المختبر',
            'exams': 'الامتحانات'
        }
            
        bot.edit_message_text(
            f"اختر من {category_names[action]} - العدد: {category_count}:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.stage_category_menu(stage, category_map[action], is_admin)
        )

def handle_admin_management(call, action, data_list, is_developer):
    """Handle admin management callbacks"""
    if not is_developer:
        bot.answer_callback_query(call.id, "⛔ صلاحية مرفوضة")
        return
    
    if action == 'manage':
        # عرض قائمة إدارة الأدمن
        bot.edit_message_text(
            "🔐 لوحة إدارة الأدمن:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.admin_management_menu()
        )
        
    elif action == 'admin_section':
        # قسم الأدمنية
        bot.edit_message_text(
            "👥 قسم إدارة الأدمنية:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.admin_section_menu()
        )
        
    elif action == 'ban_section':
        # قسم الحظر
        bot.edit_message_text(
            "🚫 قسم إدارة الحظر:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.ban_section_menu()
        )
        
    elif action == 'stats_section':
        # قسم الإحصائيات
        bot.edit_message_text(
            "📊 قسم الإحصائيات والإذاعة:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.stats_section_menu()
        )
        
    elif action == 'add':
        # إضافة أدمن جديد
        msg = bot.send_message(
            call.message.chat.id,
            "🔢 أرسل معرف المستخدم (ID) الذي تريد ترقيته إلى أدمن:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_add_admin)
        
    elif action == 'remove':
        # إزالة أدمن
        admins = db.get_admins()
        if len(admins) <= 1:  # لا يمكن حذف المطور
            bot.answer_callback_query(call.id, "⚠️ لا يوجد أدمن لإزالتهم")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for admin_id, username, full_name in admins:
            if admin_id != DEVELOPER_ID:  # لا يمكن حذف المطور
                btn_text = f"➖ {full_name or username or admin_id}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'admin:remove_confirm:{admin_id}'))
        
        markup.add(types.InlineKeyboardButton("العودة", callback_data='admin:admin_section'))
        
        bot.edit_message_text(
            "اختر الأدمن الذي تريد إزالته:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    elif action == 'remove_confirm':
        # تأكيد إزالة الأدمن
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        admin_id = int(data_list[0])
        admins = db.get_admins()
        target_admin = next((a for a in admins if a[0] == admin_id), None)
        
        if not target_admin or admin_id == DEVELOPER_ID:
            bot.answer_callback_query(call.id, "❌ لا يمكن إزالة هذا الأدمن")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ تأكيد الإزالة", callback_data=f'admin:remove_execute:{admin_id}'),
            types.InlineKeyboardButton("❌ إلغاء", callback_data='admin:admin_section')
        )
        
        bot.edit_message_text(
            f"⚠️ هل أنت متأكد من إزالة الأدمن:\n"
            f"ID: {admin_id}\n"
            f"Username: @{target_admin[1]}\n"
            f"Name: {target_admin[2]}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    elif action == 'remove_execute':
        # تنفيذ إزالة الأدمن
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        admin_id = int(data_list[0])
        
        if db.remove_admin(admin_id):
            bot.answer_callback_query(call.id, "✅ تم إزالة الأدمن بنجاح")
            bot.edit_message_text(
                "✅ تم إزالة الأدمن بنجاح",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=Keyboards.admin_section_menu()
            )
        else:
            bot.answer_callback_query(call.id, "❌ فشل في إزالة الأدمن")
            
    elif action == 'list':
        # عرض قائمة الأدمن
        admins = db.get_admins()
        message = "👥 قائمة الأدمن:\n\n"
        
        for admin_id, username, full_name in admins:
            role = " (المطور)" if admin_id == DEVELOPER_ID else ""
            message += f"🔹 {full_name or 'بدون اسم'}\n"
            message += f"   👤 @{username}\n" if username else "   👤 بدون يوزرنيم\n"
            message += f"   🆔 {admin_id}{role}\n\n"
        
        bot.edit_message_text(
            message,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.admin_section_menu()
        )
        
    elif action == 'new_users':
        # عرض المستخدمين الجدد
        new_users = db.get_new_users()
        if not new_users:
            bot.answer_callback_query(call.id, "⚠️ لا يوجد مستخدمين جدد")
            return
            
        message = "👤 المستخدمين الجدد:\n\n"
        for user_id, first_name, last_name, username in new_users:
            message += f"🔹 {first_name} {last_name}\n" if first_name or last_name else "🔹 مستخدم جديد\n"
            message += f"   👤 @{username}\n" if username else "   👤 بدون يوزرنيم\n"
            message += f"   🆔 {user_id}\n\n"
        
        bot.send_message(
            call.message.chat.id,
            message,
            reply_markup=Keyboards.stats_section_menu()
        )
        
    elif action == 'user_stats':
        # عرض إحصائية المستخدمين
        user_count = db.count_users()
        bot.answer_callback_query(
            call.id,
            f"👥 عدد المستخدمين: {user_count}",
            show_alert=True
        )
        
    elif action == 'broadcast':
        # إرسال إذاعة
        msg = bot.send_message(
            call.message.chat.id,
            "📢 أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_broadcast_message)
        
    elif action == 'channel_manage':
        # إدارة القناة الإجبارية
        bot.edit_message_text(
            "📌 إدارة القناة الإجبارية:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.channel_management_menu()
        )
        
    elif action == 'channel_add':
        # إضافة قناة إجبارية
        msg = bot.send_message(
            call.message.chat.id,
            "📢 أرسل معرف القناة أو رابطها (مثل @shahmplus أو https://t.me/shahmplus):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_add_channel)
        
    elif action == 'channel_remove':
        # إزالة القناة الإجبارية
        if db.remove_required_channel():
            bot.answer_callback_query(call.id, "✅ تم إزالة القناة الإجبارية بنجاح")
            bot.edit_message_text(
                "✅ تم إزالة القناة الإجبارية بنجاح",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=Keyboards.channel_management_menu()
            )
        else:
            bot.answer_callback_query(call.id, "❌ فشل في إزالة القناة أو لا توجد قناة لإزالتها")
            
    elif action == 'search_channels':
        # إدارة قنوات البحث
        bot.edit_message_text(
            "🔍 إدارة قنوات البحث:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.search_channels_management()
        )
        
    elif action == 'add_search_channel':
        # إضافة قناة بحث
        msg = bot.send_message(
            call.message.chat.id,
            "🔍 أرسل معرف القناة أو رابطها لإضافتها للبحث:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_add_search_channel)
        
    elif action == 'remove_search_channel':
        # إزالة قناة بحث
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        channel_id = data_list[0]
        if db.remove_search_channel(channel_id):
            bot.answer_callback_query(call.id, "✅ تم إزالة القناة بنجاح")
            bot.edit_message_text(
                "✅ تم إزالة القناة بنجاح",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=Keyboards.search_channels_management()
            )
        else:
            bot.answer_callback_query(call.id, "❌ فشل في إزالة القناة")
            
    elif action == 'manage_comments':
        # إدارة التعليقات
        bot.edit_message_text(
            "💬 إدارة التعليقات والاستفسارات:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.admin_comments_menu()
        )
        
    elif action == 'ai_manage':
        # إدارة الذكاء الاصطناعي
        bot.edit_message_text(
            "🤖 إدارة خدمة الذكاء الاصطناعي:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.ai_management_menu()
        )
        
    elif action == 'ai_toggle':
        # تفعيل/تعطيل الذكاء الاصطناعي
        settings = db.get_ai_settings()
        new_enabled = not settings[0]
        db.update_ai_settings(enabled=new_enabled)
        
        status = "✅ تم تفعيل الخدمة" if new_enabled else "❌ تم تعطيل الخدمة"
        bot.answer_callback_query(call.id, status)
        bot.edit_message_text(
            "🤖 إدارة خدمة الذكاء الاصطناعي:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.ai_management_menu()
        )
        
    elif action == 'ai_restrict_toggle':
        # تقييد/عدم تقييد الذكاء الاصطناعي
        settings = db.get_ai_settings()
        new_restricted = not settings[1]
        db.update_ai_settings(restricted=new_restricted)
        
        status = "✅ تم تقييد الخدمة" if new_restricted else "❌ تم إلغاء تقييد الخدمة"
        bot.answer_callback_query(call.id, status)
        bot.edit_message_text(
            "🤖 إدارة خدمة الذكاء الاصطناعي:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.ai_management_menu()
        )
        
    elif action == 'ai_users':
        # إدارة مستخدمي الذكاء الاصطناعي
        bot.edit_message_text(
            "👤 إدارة المستخدمين المسموح لهم باستخدام الذكاء الاصطناعي:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.ai_users_menu()
        )
        
    elif action == 'add_ai_user':
        # إضافة مستخدم للذكاء الاصطناعي
        msg = bot.send_message(
            call.message.chat.id,
            "👤 أرسل معرف المستخدم (ID) الذي تريد منحه صلاحية استخدام الذكاء الاصطناعي:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_add_ai_user)
        
    elif action == 'remove_ai_user':
        # إزالة مستخدم من الذكاء الاصطناعي
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        user_id = int(data_list[0])
        if db.remove_ai_user(user_id):
            bot.answer_callback_query(call.id, "✅ تم إزالة المستخدم بنجاح")
            bot.edit_message_text(
                "👤 إدارة المستخدمين المسموح لهم باستخدام الذكاء الاصطناعي:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=Keyboards.ai_users_menu()
            )
        else:
            bot.answer_callback_query(call.id, "❌ فشل في إزالة المستخدم")
            
    elif action == 'ban_user':
        # حظر مستخدم
        msg = bot.send_message(
            call.message.chat.id,
            "🚫 أرسل معرف المستخدم (ID) الذي تريد حظره:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_ban_user)
        
    elif action == 'unban_user':
        # إلغاء حظر مستخدم
        msg = bot.send_message(
            call.message.chat.id,
            "✅ أرسل معرف المستخدم (ID) الذي تريد إلغاء حظره:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_unban_user)
        
    elif action == 'support_tickets':
        # تذاكر الدعم
        bot.edit_message_text(
            "📩 تذاكر الدعم المفتوحة:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=Keyboards.support_tickets_menu()
        )
        
    elif action == 'view_ticket':
        # عرض تذكرة دعم
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        ticket_id = int(data_list[0])
        ticket_info = db.get_ticket_info(ticket_id)
        
        if not ticket_info:
            bot.answer_callback_query(call.id, "❌ التذكرة غير موجودة")
            return
            
        message = (
            f"📩 تذكرة الدعم #{ticket_id}\n"
            f"👤 المرسل: {ticket_info[3]} (@{ticket_info[4]})\n"
            f"📅 التاريخ: {ticket_info[5]}\n"
            f"🎓 المرحلة: {['أولى', 'ثانية', 'ثالثة', 'رابعة'][ticket_info[2]-1]}\n\n"
            f"💬 الرسالة:\n{ticket_info[1]}"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 الرد على التذكرة", callback_data=f'support_reply:{ticket_id}'))
        markup.add(types.InlineKeyboardButton("العودة", callback_data='admin:support_tickets'))
        
        bot.send_message(
            call.message.chat.id,
            message,
            reply_markup=markup
        )
        
    elif action == 'reply_ticket':
        # الرد على تذكرة دعم
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        ticket_id = int(data_list[0])
        handle_support_reply_button(call, ticket_id)
        
    elif action == 'close_ticket':
        # إغلاق تذكرة دعم
        if not data_list:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        ticket_id = int(data_list[0])
        if db.delete_support_ticket(ticket_id):
            bot.answer_callback_query(call.id, "✅ تم حذف التذكرة")
            bot.send_message(
                call.message.chat.id,
                f"✅ تم حذف تذكرة الدعم #{ticket_id}",
                reply_markup=Keyboards.admin_management_menu()
            )
        else:
            bot.answer_callback_query(call.id, "❌ فشل في حذف التذكرة")

def process_add_admin(message):
    try:
        user_id = int(message.text)
        if user_id == message.from_user.id:
            raise ValueError("لا يمكنك إضافة نفسك كأدمن")
            
        # الحصول على معلومات المستخدم
        try:
            user = bot.get_chat(user_id)
            username = user.username
            full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        except:
            username = None
            full_name = None
            
        if db.add_admin(
            user_id=user_id,
            username=username,
            full_name=full_name,
            added_by=message.from_user.id
        ):
            bot.reply_to(
                message,
                f"✅ تمت ترقية المستخدم إلى أدمن بنجاح\n"
                f"👤 الاسم: {full_name or 'غير معروف'}\n"
                f"🆔 ID: {user_id}\n"
                f"📌 اليوزر: @{username}" if username else "📌 بدون يوزرنيم"
            )
        else:
            raise ValueError("فشل في إضافة الأدمن")
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إضافة الأدمن: {str(e)}")

def process_add_channel(message):
    try:
        text = message.text.strip()
        channel_id = None
        channel_username = None
        
        # تحليل المعرف من الرابط
        if text.startswith('https://t.me/'):
            channel_username = text.split('/')[-1]
        elif text.startswith('@'):
            channel_username = text[1:]
        else:
            channel_username = text
        
        # الحصول على معلومات القناة
        try:
            chat = bot.get_chat(f"@{channel_username}")
            channel_id = str(chat.id)
            channel_title = chat.title
        except Exception as e:
            raise ValueError("تعذر الحصول على معلومات القناة. تأكد من إضافة البوت كمسؤول في القناة")
        
        # إضافة القناة إلى قاعدة البيانات
        if db.add_required_channel(
            channel_id=channel_id,
            channel_username=channel_username,
            channel_title=channel_title,
            added_by=message.from_user.id
        ):
            bot.reply_to(
                message,
                f"✅ تم تعيين القناة الإجبارية بنجاح\n"
                f"📌 العنوان: {channel_title}\n"
                f"👥 اليوزر: @{channel_username}\n"
                f"🆔 المعرف: {channel_id}"
            )
        else:
            raise ValueError("فشل في تعيين القناة الإجبارية")
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إضافة القناة: {str(e)}")

def process_add_search_channel(message):
    try:
        text = message.text.strip()
        channel_username = None
        
        # تحليل المعرف من الرابط
        if text.startswith('https://t.me/'):
            channel_username = text.split('/')[-1]
        elif text.startswith('@'):
            channel_username = text[1:]
        else:
            channel_username = text
        
        # الحصول على معلومات القناة
        try:
            chat = bot.get_chat(f"@{channel_username}")
            channel_id = str(chat.id)
            channel_title = chat.title
        except Exception as e:
            raise ValueError("تعذر الحصول على معلومات القناة. تأكد من صحة الرابط")
        
        # إضافة القناة إلى قاعدة البيانات
        if db.add_search_channel(
            channel_id=channel_id,
            channel_username=channel_username,
            channel_title=channel_title,
            added_by=message.from_user.id
        ):
            bot.reply_to(
                message,
                f"✅ تم إضافة قناة البحث بنجاح\n"
                f"📌 العنوان: {channel_title}\n"
                f"👥 اليوزر: @{channel_username}\n"
                f"🆔 المعرف: {channel_id}"
            )
        else:
            raise ValueError("فشل في إضافة قناة البحث")
            
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إضافة قناة البحث: {str(e)}")

def process_broadcast_message(message):
    try:
        users = db.get_all_users()
        total = len(users)
        success = 0
        failures = 0
        
        # إعداد رسالة التقدم
        progress_msg = bot.send_message(
            message.chat.id,
            f"⏳ جارِ إرسال الرسالة إلى {total} مستخدم..."
        )
        
        # إرسال الرسالة إلى جميع المستخدمين
        for user_id in users:
            try:
                if message.content_type == 'text':
                    bot.send_message(user_id, message.text)
                elif message.content_type == 'photo':
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
                elif message.content_type == 'video':
                    bot.send_video(user_id, message.video.file_id, caption=message.caption)
                elif message.content_type == 'document':
                    bot.send_document(user_id, message.document.file_id, caption=message.caption)
                success += 1
            except Exception as e:
                print(f"Failed to send broadcast to {user_id}: {e}")
                failures += 1
            
            # تحديث رسالة التقدم كل 50 مستخدم
            if (success + failures) % 50 == 0:
                try:
                    bot.edit_message_text(
                        f"⏳ جارِ إرسال الرسالة...\n"
                        f"✅ تم بنجاح: {success}\n"
                        f"❌ فشل: {failures}\n"
                        f"📊 الإجمالي: {total}",
                        progress_msg.chat.id,
                        progress_msg.message_id
                    )
                except:
                    pass
        
        # إرسال النتيجة النهائية
        bot.edit_message_text(
            f"📊 نتائج الإذاعة:\n"
            f"✅ تم بنجاح: {success}\n"
            f"❌ فشل: {failures}\n"
            f"📊 الإجمالي: {total}",
            progress_msg.chat.id,
            progress_msg.message_id
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في الإذاعة: {str(e)}")

def handle_comment(call, action, data):
    if action == 'add':
        if not data:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        content_id = int(data[0])
        content_data = db.get_content_by_id(content_id)
        content_title = content_data[3] if content_data else "محتوى غير معروف"
        
        msg = bot.send_message(
            call.message.chat.id,
            f"💬 أرسل تعليقك أو استفسارك حول المحتوى: {content_title}",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_comment, content_id, call.from_user.id, content_title)
        
    elif action == 'list':
        if not data:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        content_id = int(data[0])
        comments = db.get_comments(content_id)
        
        if not comments:
            bot.answer_callback_query(call.id, "⚠️ لا توجد تعليقات بعد")
            return
            
        message = f"💬 التعليقات على المحتوى:\n\n"
        for i, comment in enumerate(comments, 1):
            user_info = f"{comment[3]}" if comment[3] else f"@{comment[4]}" if comment[4] else f"المستخدم {comment[0]}"
            message += f"📌 {i}. {user_info}\n"
            message += f"   📅 {comment[2]}\n"
            message += f"   💬 {comment[1]}\n\n"
            
        # إضافة زر لإضافة تعليق جديد
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ إضافة تعليق جديد", callback_data=f'comment:add:{content_id}'))
        markup.add(types.InlineKeyboardButton("إغلاق", callback_data='delete_message'))
        
        try:
            bot.send_message(call.message.chat.id, message, reply_markup=markup)
        except:
            # إذا كانت الرسالة طويلة جداً، تقسيمها
            if len(message) > 4000:
                parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
                for part in parts[:-1]:
                    bot.send_message(call.message.chat.id, part)
                bot.send_message(call.message.chat.id, parts[-1], reply_markup=markup)
            else:
                raise
        
    elif action == 'admin_view':
        # عرض التعليق للإداريين
        if not data:
            bot.answer_callback_query(call.id, "❌ خطأ في البيانات")
            return
            
        comment_id = int(data[0])
        comments = db.get_all_comments()
        target_comment = next((c for c in comments if c[0] == comment_id), None)
        
        if not target_comment:
            bot.answer_callback_query(call.id, "❌ التعليق غير موجود")
            return
            
        message = (
            f"💬 التعليق #{target_comment[0]}\n"
            f"👤 المستخدم: {target_comment[3]} (@{target_comment[4]})\n"
            f"📅 التاريخ: {target_comment[2]}\n"
            f"🎓 المرحلة: {['أولى', 'ثانية', 'ثالثة', 'رابعة'][target_comment[6]-1]}\n"
            f"📝 عنوان المحتوى: {target_comment[5]}\n\n"
            f"💬 النص:\n{target_comment[1]}"
        )
        
        bot.send_message(call.message.chat.id, message)
        
def process_comment(message, content_id, user_id, content_title):
    try:
        if not message.text:
            bot.reply_to(message, "❌ يرجى إرسال نص التعليق")
            return
        
        # إضافة التعليق إلى قاعدة البيانات
        if db.add_comment(content_id, user_id, message.text, content_title):
            bot.reply_to(message, "✅ تم إضافة تعليقك بنجاح")
        else:
            raise ValueError("فشل في إضافة التعليق")
        
        # إعلام المطور بتعليق جديد
        user_info = f"{message.from_user.first_name} (@{message.from_user.username})" if message.from_user.username else message.from_user.first_name
        notify_msg = (
            f"💬 تعليق جديد:\n"
            f"👤 المستخدم: {user_info}\n"
            f"🆔 ID: {user_id}\n"
            f"📌 على المحتوى: {content_title}\n\n"
            f"💬 النص: {message.text}"
        )
        bot.send_message(DEVELOPER_ID, notify_msg)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إضافة التعليق: {str(e)}")

def handle_support(call, action):
    if action == 'contact':
        # الحصول على مرحلة المستخدم
        user_stage = db.get_user_stage(call.from_user.id)
        stage = user_stage[0] if user_stage else 4
        
        msg = bot.send_message(
            call.message.chat.id,
            f"📩 أرسل رسالتك إلى الدعم (المرحلة {['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]}):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_support_ticket, stage)

def process_support_ticket(message, stage):
    """معالجة إرسال تذكرة دعم جديدة"""
    try:
        if not message.text:
            bot.reply_to(message, "❌ يرجى إرسال نص الرسالة")
            return
            
        # إضافة التذكرة إلى قاعدة البيانات والحصول على ID
        ticket_id = db.add_support_ticket(message.from_user.id, message.text, stage)
        
        if ticket_id:
            bot.reply_to(message, f"✅ تم إرسال تذكرتك بنجاح (#{ticket_id})\nسيتواصل معك الدعم قريباً")
            
            # إعلام المطورين بتذكرة جديدة مع زر للرد
            user_info = f"{message.from_user.first_name} (@{message.from_user.username})" if message.from_user.username else message.from_user.first_name
            stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
            
            notify_msg = (
                f"📩 تذكرة دعم جديدة #{ticket_id} (المرحلة {stage_name}):\n"
                f"👤 المستخدم: {user_info}\n"
                f"🆔 ID: {message.from_user.id}\n\n"
                f"💬 الرسالة: {message.text}"
            )
            
            # إرسال الإشعار لجميع الأدمنية مع زر للرد
            admins = db.get_admins()
            for admin_id, username, full_name in admins:
                try:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(
                        "📩 الرد على التذكرة", 
                        callback_data=f'support_reply:{ticket_id}'
                    ))
                    
                    bot.send_message(admin_id, notify_msg, reply_markup=markup)
                except Exception as e:
                    print(f"Failed to send notification to admin {admin_id}: {e}")
                    
        else:
            bot.reply_to(message, "❌ فشل في إرسال التذكرة")
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في إرسال التذكرة: {str(e)}")

def handle_ai(call, action, data):
    settings = db.get_ai_settings()
    
    # التحقق من تفعيل الخدمة
    if not settings[0]:
        bot.answer_callback_query(call.id, "❌ خدمة الذكاء الاصطناعي معطلة حالياً")
        return
        
    # التحقق من تقييد الخدمة
    if settings[1] and not db.is_ai_allowed(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ غير مسموح لك باستخدام هذه الخدمة")
        return
        
    if action == 'ask':
        # الحصول على مرحلة المستخدم
        user_stage = db.get_user_stage(call.from_user.id)
        stage = user_stage[0] if user_stage else 4
        
        msg = bot.send_message(
            call.message.chat.id,
            f"🤖 أرسل سؤالك للذكاء الاصطناعي (المرحلة {['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]}):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_ai_question)

def process_ai_question(message):
    try:
        if not message.text:
            bot.reply_to(message, "❌ يرجى إرسال سؤال")
            return
            
        # إظهار رسالة "جار المعالجة"
        processing_msg = bot.reply_to(message, "⏳ جارِ معالجة سؤالك...")
        
        # إرسال السؤال إلى OpenRouter
        response = AIHandler.ask_question(message.text)
        
        # حذف رسالة "جار المعالجة"
        try:
            bot.delete_message(message.chat.id, processing_msg.message_id)
        except:
            pass
        
        # إرسال الإجابة
        bot.reply_to(message, f"🤖 الذكاء الاصطناعي:\n\n{response}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ في معالجة السؤال: {str(e)}")

def process_add_ai_user(message):
    try:
        user_id = int(message.text)
        if db.add_ai_user(user_id, message.from_user.id):
            bot.reply_to(message, f"✅ تمت إضافة المستخدم {user_id} إلى قائمة المسموح لهم")
        else:
            bot.reply_to(message, "❌ فشل في إضافة المستخدم أو المستخدم موجود مسبقاً")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

def process_ban_user(message):
    try:
        user_id = int(message.text)
        if db.ban_user(user_id):
            bot.reply_to(message, f"✅ تم حظر المستخدم {user_id} بنجاح")
        else:
            bot.reply_to(message, "❌ فشل في حظر المستخدم أو المستخدم غير موجود")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

def process_unban_user(message):
    try:
        user_id = int(message.text)
        if db.unban_user(user_id):
            bot.reply_to(message, f"✅ تم إلغاء حظر المستخدم {user_id} بنجاح")
        else:
            bot.reply_to(message, "❌ فشل في إلغاء الحظر أو المستخدم غير موجود")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")