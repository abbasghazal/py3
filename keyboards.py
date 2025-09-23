# bot/keyboards.py
from telebot import types
from database import db
from config import DEVELOPER_ID

class Keyboards:
    @staticmethod
    def main_menu(user_id, stage=4):
        """Main menu for specific stage"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        stage_name = ['أولى', 'ثانية', 'ثالثة', 'رابعة'][stage-1]
        
        buttons = [
            types.InlineKeyboardButton("المواد الدراسية", callback_data=f'stage_{stage}:subjects'),
            types.InlineKeyboardButton("الشروحات", callback_data=f'stage_{stage}:explanations'),
            types.InlineKeyboardButton("المختبر", callback_data=f'stage_{stage}:lab'),
            types.InlineKeyboardButton("الامتحانات", callback_data=f'stage_{stage}:exams'),
            types.InlineKeyboardButton("📬 تواصل مع الدعم", callback_data='support:contact'),
            types.InlineKeyboardButton("🤖 الذكاء الاصطناعي", callback_data='ai:ask')
        ]
        markup.add(*buttons)
        
        if user_id == DEVELOPER_ID:
            markup.add(types.InlineKeyboardButton("🔐 إدارة الأدمن", callback_data='admin:manage'))
            
        return markup

    @staticmethod
    def stage_category_menu(stage, category, is_admin=False):
        """Category menu for specific stage"""
        subjects = db.get_stage_subjects_by_category(stage, category)
        
        # ترتيب المواد بشكل منظم حسب النوع
        if category == 'subjects':
            # ترتيب المواد الدراسية أبجدياً
            subjects.sort(key=lambda x: x[0])
        elif category == 'explanations':
            # ترتيب الشروحات أبجدياً
            subjects.sort(key=lambda x: x[0])
        elif category == 'lab':
            # ترتيب المختبرات أبجدياً
            subjects.sort(key=lambda x: x[0])
        elif category == 'exams':
            # ترتيب الامتحانات أبجدياً
            subjects.sort(key=lambda x: x[0])
        elif category == 'exam_models':
            # ترتيب نماذج الامتحانات أبجدياً
            subjects.sort(key=lambda x: x[0])
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # تقسيم المواد إلى صفوف من 2 أزرار لكل صف
        for i in range(0, len(subjects), 2):
            row = subjects[i:i+2]
            buttons = []
            for name_ar, key in row:
                # تقصير النص إذا كان طويلاً
                display_name = name_ar
                if len(display_name) > 15:
                    display_name = display_name[:15] + "..."
                buttons.append(types.InlineKeyboardButton(display_name, callback_data=f'stage_subject:{stage}:{key}'))
            
            # إضافة الأزرار للصف
            if len(buttons) == 2:
                markup.row(buttons[0], buttons[1])
            else:
                markup.add(buttons[0])
        
        # زر العودة
        back_button = types.InlineKeyboardButton("العودة", callback_data=f'stage_{stage}:home')
        markup.add(back_button)
        
        return markup

    @staticmethod
    def stage_chapters_menu(stage, subject_key, is_admin=False):
        """Chapters menu for specific stage"""
        subject = db.get_stage_subject(stage, subject_key)
        if not subject:
            return None
            
        if subject[3] in ['lab', 'exams', 'exam_models']:
            return None
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        for i in range(1, 7, 2):
            buttons = [
                types.InlineKeyboardButton(f"الفصل {i}", callback_data=f'stage_chapter:{stage}:{subject_key}:{i}'),
                types.InlineKeyboardButton(f"الفصل {i+1}", callback_data=f'stage_chapter:{stage}:{subject_key}:{i+1}') if i+1 <= 6 else None
            ]
            markup.add(*[btn for btn in buttons if btn is not None])
        
        markup.add(types.InlineKeyboardButton("العودة", callback_data=f'stage_{stage}:{subject[3]}'))
        return markup

    @staticmethod
    def stage_content_list_menu(stage, subject_key, chapter_num, content_list, is_admin=False):
        """Generate inline keyboard for content list in specific stage"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for content_id, content_type, description in content_list:
            icon = '🎥' if content_type == 'video' else '📄' if content_type == 'document' else '🖼️' if content_type == 'photo' else '📝'
            btn_text = f"{icon} {description[:20]}..." if description else f"{icon} محتوى {content_id}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'stage_view_content:{stage}:{content_id}'))
        
        if is_admin:
            markup.add(types.InlineKeyboardButton("🗑️ حذف محتوى", callback_data=f'stage_delete_content:select:{stage}:{subject_key}:{chapter_num}'))
        
        if content_list:
            first_content_id = content_list[0][0]
            markup.add(types.InlineKeyboardButton("💬 إضافة تعليق/استفسار", callback_data=f'stage_comment:add:{stage}:{first_content_id}'))
        
        markup.add(types.InlineKeyboardButton("العودة", callback_data=f'stage_chapter:{stage}:{subject_key}:{chapter_num}'))
        return markup

    @staticmethod
    def stage_upload_type_menu(stage, subject_key, chapter_num=None):
        """Upload type menu for specific stage"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        ref = f"{stage}:{subject_key}:{chapter_num}" if chapter_num else f"{stage}:{subject_key}"
        
        buttons = [
            types.InlineKeyboardButton("🎥 فيديو", callback_data=f'stage_upload:video:{ref}'),
            types.InlineKeyboardButton("📄 ملف", callback_data=f'stage_upload:doc:{ref}'),
            types.InlineKeyboardButton("🖼️ صورة", callback_data=f'stage_upload:photo:{ref}'),
            types.InlineKeyboardButton("📝 نص", callback_data=f'stage_upload:text:{ref}'),
            types.InlineKeyboardButton("↩️ رجوع", 
                callback_data=f'stage_chapter:{stage}:{subject_key}:{chapter_num}' if chapter_num else f'stage_subject:{stage}:{subject_key}')
        ]
        markup.add(*buttons)
        return markup

    @staticmethod
    def stage_delete_content_menu(stage, subject_key, chapter_num, content_list):
        """Generate keyboard for content deletion in specific stage"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for content_id, content_type, description in content_list:
            icon = '🎥' if content_type == 'video' else '📄' if content_type == 'document' else '🖼️' if content_type == 'photo' else '📝'
            btn_text = f"🗑️ {icon} {description[:20]}..." if description else f"🗑️ {icon} محتوى {content_id}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'stage_delete_content:confirm:{stage}:{content_id}'))
        
        markup.add(types.InlineKeyboardButton("العودة", callback_data=f'stage_chapter:{stage}:{subject_key}:{chapter_num}'))
        return markup

    @staticmethod
    def confirm_delete_menu(stage, content_id):
        """Confirmation keyboard for content deletion in specific stage"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f'stage_delete_content:execute:{stage}:{content_id}'),
            types.InlineKeyboardButton("❌ إلغاء", callback_data=f'stage_delete_content:cancel:{stage}:{content_id}')
        )
        return markup

    @staticmethod
    def admin_management_menu():
        """Keyboard for admin management"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        markup.add(types.InlineKeyboardButton("👥 قسم الأدمنية", callback_data='admin:admin_section'))
        
        row2_buttons = [
            types.InlineKeyboardButton("🚫 قسم الحظر", callback_data='admin:ban_section'),
            types.InlineKeyboardButton("📊 قسم الإحصائيات", callback_data='admin:stats_section')
        ]
        markup.row(*row2_buttons)
        
        row3_buttons = [
            types.InlineKeyboardButton("🔍 قنوات البحث", callback_data='admin:search_channels'),
            types.InlineKeyboardButton("📢 القناة الإجبارية", callback_data='admin:channel_manage')
        ]
        markup.row(*row3_buttons)
        
        other_buttons = [
            types.InlineKeyboardButton("💬 إدارة التعليقات", callback_data='admin:manage_comments'),
            types.InlineKeyboardButton("🤖 إدارة الذكاء الاصطناعي", callback_data='admin:ai_manage'),
            types.InlineKeyboardButton("📩 تذاكر الدعم", callback_data='admin:support_tickets'),
            types.InlineKeyboardButton("العودة", callback_data='main:home')
        ]
        
        for button in other_buttons:
            markup.add(button)
            
        return markup

    @staticmethod
    def admin_section_menu():
        """Sub-menu for admin management"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton("➕ رفع أدمن", callback_data='admin:add'),
            types.InlineKeyboardButton("➖ حذف أدمن", callback_data='admin:remove'),
            types.InlineKeyboardButton("📋 قائمة الأدمن", callback_data='admin:list'),
            types.InlineKeyboardButton("العودة", callback_data='admin:manage')
        ]
        markup.add(*buttons)
        return markup

    @staticmethod
    def ban_section_menu():
        """Sub-menu for ban management"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton("🚫 حظر مستخدم", callback_data='admin:ban_user'),
            types.InlineKeyboardButton("✅ إلغاء حظر مستخدم", callback_data='admin:unban_user'),
            types.InlineKeyboardButton("العودة", callback_data='admin:manage')
        ]
        markup.add(*buttons)
        return markup

    @staticmethod
    def stats_section_menu():
        """Sub-menu for statistics"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        buttons = [
            types.InlineKeyboardButton("👤 المستخدمين الجدد", callback_data='admin:new_users'),
            types.InlineKeyboardButton("👥 إحصائية المستخدمين", callback_data='admin:user_stats'),
            types.InlineKeyboardButton("📢 إرسال إذاعة", callback_data='admin:broadcast'),
            types.InlineKeyboardButton("العودة", callback_data='admin:manage')
        ]
        markup.add(*buttons)
        return markup

    @staticmethod
    def channel_management_menu():
        """Keyboard for channel management"""
        channel_info = db.get_required_channel()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if channel_info:
            buttons = [
                types.InlineKeyboardButton("➖ إزالة القناة الإجبارية", callback_data='admin:channel_remove'),
                types.InlineKeyboardButton("🔗 الانتقال للقناة", url=f"https://t.me/{channel_info[1]}"),
                types.InlineKeyboardButton("العودة", callback_data='admin:manage')
            ]
        else:
            buttons = [
                types.InlineKeyboardButton("➕ إضافة قناة إجبارية", callback_data='admin:channel_add'),
                types.InlineKeyboardButton("العودة", callback_data='admin:manage')
            ]
        
        markup.add(*buttons)
        return markup
        
    @staticmethod
    def search_channels_management():
        """Keyboard for search channels management"""
        channels = db.get_search_channels()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for channel in channels:
            btn_text = f"➖ {channel[2]}" if channel[2] else f"➖ @{channel[1]}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'admin:remove_search_channel:{channel[0]}'))
        
        markup.add(
            types.InlineKeyboardButton("➕ إضافة قناة بحث", callback_data='admin:add_search_channel'),
            types.InlineKeyboardButton("العودة", callback_data='admin:manage')
        )
        return markup

    @staticmethod
    def admin_comments_menu():
        """Keyboard for admin to view all comments"""
        comments = db.get_all_comments()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if not comments:
            markup.add(types.InlineKeyboardButton("لا توجد تعليقات", callback_data='none'))
        else:
            for comment in comments:
                user_info = f"{comment[3]}" if comment[3] else f"@{comment[4]}" if comment[4] else f"المستخدم {comment[0]}"
                btn_text = f"💬 {comment[5]} - {user_info} (المرحلة {comment[6]})"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'comment:admin_view:{comment[0]}'))
        
        markup.add(types.InlineKeyboardButton("العودة", callback_data='admin:manage'))
        return markup
        
    @staticmethod
    def ai_management_menu():
        """Keyboard for AI management"""
        settings = db.get_ai_settings()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        enabled_text = "✅ مفعل" if settings[0] else "❌ معطل"
        restricted_text = "✅ مقيد" if settings[1] else "❌ غير مقيد"
        
        buttons = [
            types.InlineKeyboardButton(f"تفعيل/تعطيل الخدمة: {enabled_text}", callback_data='admin:ai_toggle'),
            types.InlineKeyboardButton(f"تقييد/عدم تقييد الخدمة: {restricted_text}", callback_data='admin:ai_restrict_toggle'),
            types.InlineKeyboardButton("👤 إدارة المستخدمين المسموح لهم", callback_data='admin:ai_users'),
            types.InlineKeyboardButton("العودة", callback_data='admin:manage')
        ]
        markup.add(*buttons)
        return markup
        
    @staticmethod
    def ai_users_menu():
        """Keyboard for AI allowed users"""
        users = db.get_ai_users()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if not users:
            markup.add(types.InlineKeyboardButton("لا يوجد مستخدمين مسموح لهم", callback_data='none'))
        else:
            for user_id in users:
                try:
                    from config import bot
                    chat = bot.get_chat(user_id)
                    name = chat.first_name or chat.username or str(user_id)
                    markup.add(types.InlineKeyboardButton(f"➖ {name}", callback_data=f'admin:remove_ai_user:{user_id}'))
                except:
                    markup.add(types.InlineKeyboardButton(f"➖ {user_id}", callback_data=f'admin:remove_ai_user:{user_id}'))
        
        markup.add(
            types.InlineKeyboardButton("➕ إضافة مستخدم", callback_data='admin:add_ai_user'),
            types.InlineKeyboardButton("العودة", callback_data='admin:ai_manage')
        )
        return markup
        
        @staticmethod
        def support_tickets_menu():
            """Keyboard for support tickets"""
            tickets = db.get_support_tickets()
            markup = types.InlineKeyboardMarkup(row_width=1)
    
            if not tickets:
                markup.add(types.InlineKeyboardButton("لا توجد تذاكر مفتوحة", callback_data='none'))
            else:
                for ticket in tickets:
                	user_info = f"{ticket[3]}" if ticket[3] else f"@{ticket[4]}" if ticket[4] else f"المستخدم {ticket[0]}"
                	btn_text = f"📩 {user_info} - {ticket[1][:20]} (المرحلة {ticket[2]})"
                	markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'admin:view_ticket:{ticket[0]}'))
    
            markup.add(types.InlineKeyboardButton("العودة", callback_data='admin:manage'))
            return markup

    @staticmethod
    def stage_selection_menu(full_name):
        """Keyboard for stage selection during registration"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("المرحلة الأولى", callback_data=f'register_stage:1:{full_name}'),
            types.InlineKeyboardButton("المرحلة الثانية", callback_data=f'register_stage:2:{full_name}'),
            types.InlineKeyboardButton("المرحلة الثالثة", callback_data=f'register_stage:3:{full_name}'),
            types.InlineKeyboardButton("المرحلة الرابعة", callback_data=f'register_stage:4:{full_name}')
        ]
        markup.add(*buttons)
        return markup