# bot/database.py
import sqlite3
from datetime import datetime
from config import DEVELOPER_ID

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('abbas.db', check_same_thread=False)
        self.create_tables()
        self.insert_default_data()

    def create_tables(self):
        with self.conn:
            # جدول المستخدمين الأساسي
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                is_new BOOLEAN DEFAULT 1,
                is_banned BOOLEAN DEFAULT 0
            )''')

            # جدول المستخدمين مع المرحلة
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users_stages (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                stage INTEGER NOT NULL CHECK (stage IN (1, 2, 3, 4)),
                date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )''')

            # جداول المواد لكل مرحلة
            for stage in [1, 2, 3, 4]:
                self.conn.execute(f'''
                CREATE TABLE IF NOT EXISTS stage_{stage}_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name_ar TEXT NOT NULL UNIQUE,
                    name_en TEXT NOT NULL UNIQUE,
                    key TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL DEFAULT 'subjects'
                )''')
                
                self.conn.execute(f'''
                CREATE TABLE IF NOT EXISTS stage_{stage}_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_key TEXT NOT NULL,
                    chapter_num INTEGER,
                    content_type TEXT NOT NULL,
                    file_id TEXT,
                    text_content TEXT,
                    description TEXT,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_by INTEGER,
                    content_number INTEGER,
                    FOREIGN KEY (subject_key) REFERENCES stage_{stage}_subjects(key)
                )''')

            # جدول الأدمنية
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER
            )''')

            # جدول القنوات الإجبارية
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS required_channels (
                channel_id TEXT PRIMARY KEY,
                channel_username TEXT,
                channel_title TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by INTEGER
            )''')
            
            # جدول التعليقات والاستفسارات
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                replied BOOLEAN DEFAULT 0,
                content_title TEXT,  
                stage INTEGER NOT NULL DEFAULT 4,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )''')
            
            # جدول قنوات البحث
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS search_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL UNIQUE,
                channel_username TEXT,
                channel_title TEXT,
                added_by INTEGER,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (added_by) REFERENCES admins(user_id)
            )''')
            
            # جدول التذاكر (التواصل مع الدعم) - مبسط بدون تخزين الردود
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stage INTEGER NOT NULL DEFAULT 4,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )''')
            
            # جدول إعدادات الذكاء الاصطناعي
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_settings (
                id INTEGER PRIMARY KEY DEFAULT 1,
                enabled BOOLEAN DEFAULT 0,
                restricted BOOLEAN DEFAULT 0
            )''')
            
            # جدول المستخدمين المسموح لهم باستخدام الذكاء الاصطناعي
            self.conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_allowed_users (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

    def insert_default_data(self):
        # بيانات المرحلة الأولى (11 مادة + 3 مختبرات + 11 شرح)
        stage_1_subjects = [
            # المواد الدراسية (11 مادة)
            ('رياضيات 1', 'math_1', 'math_1', 'subjects'),
            ('فيزياء 1', 'physics_1', 'physics_1', 'subjects'),
            ('كيمياء 1', 'chemistry_1', 'chemistry_1', 'subjects'),
            ('لغة عربية 1', 'arabic_1', 'arabic_1', 'subjects'),
            ('لغة انجليزية 1', 'english_1', 'english_1', 'subjects'),
            ('تاريخ 1', 'history_1', 'history_1', 'subjects'),
            ('جغرافيا 1', 'geography_1', 'geography_1', 'subjects'),
            ('علوم 1', 'science_1', 'science_1', 'subjects'),
            ('تربية اسلامية 1', 'islamic_1', 'islamic_1', 'subjects'),
            ('تربية وطنية 1', 'national_1', 'national_1', 'subjects'),
            ('كمبيوتر 1', 'computer_1', 'computer_1', 'subjects'),
            
            # الشروحات (11 شرح)
            ('شرح رياضيات 1', 'math_1_exp', 'math_1_exp', 'explanations'),
            ('شرح فيزياء 1', 'physics_1_exp', 'physics_1_exp', 'explanations'),
            ('شرح كيمياء 1', 'chemistry_1_exp', 'chemistry_1_exp', 'explanations'),
            ('شرح لغة عربية 1', 'arabic_1_exp', 'arabic_1_exp', 'explanations'),
            ('شرح لغة انجليزية 1', 'english_1_exp', 'english_1_exp', 'explanations'),
            ('شرح تاريخ 1', 'history_1_exp', 'history_1_exp', 'explanations'),
            ('شرح جغرافيا 1', 'geography_1_exp', 'geography_1_exp', 'explanations'),
            ('شرح علوم 1', 'science_1_exp', 'science_1_exp', 'explanations'),
            ('شرح تربية اسلامية 1', 'islamic_1_exp', 'islamic_1_exp', 'explanations'),
            ('شرح تربية وطنية 1', 'national_1_exp', 'national_1_exp', 'explanations'),
            ('شرح كمبيوتر 1', 'computer_1_exp', 'computer_1_exp', 'explanations'),
            
            # المختبرات (3 مختبرات)
            ('مختبر فيزياء 1', 'physics_lab_1', 'physics_lab_1', 'lab'),
            ('مختبر كيمياء 1', 'chemistry_lab_1', 'chemistry_lab_1', 'lab'),
            ('مختبر علوم 1', 'science_lab_1', 'science_lab_1', 'lab'),
            
            # الامتحانات (11 امتحان)
            ('امتحان رياضيات 1', 'math_1_exam', 'math_1_exam', 'exams'),
            ('امتحان فيزياء 1', 'physics_1_exam', 'physics_1_exam', 'exams'),
            ('امتحان كيمياء 1', 'chemistry_1_exam', 'chemistry_1_exam', 'exams'),
            ('امتحان لغة عربية 1', 'arabic_1_exam', 'arabic_1_exam', 'exams'),
            ('امتحان لغة انجليزية 1', 'english_1_exam', 'english_1_exam', 'exams'),
            ('امتحان تاريخ 1', 'history_1_exam', 'history_1_exam', 'exams'),
            ('امتحان جغرافيا 1', 'geography_1_exam', 'geography_1_exam', 'exams'),
            ('امتحان علوم 1', 'science_1_exam', 'science_1_exam', 'exams'),
            ('امتحان تربية اسلامية 1', 'islamic_1_exam', 'islamic_1_exam', 'exams'),
            ('امتحان تربية وطنية 1', 'national_1_exam', 'national_1_exam', 'exams'),
            ('امتحان كمبيوتر 1', 'computer_1_exam', 'computer_1_exam', 'exams'),
            
            # نماذج الامتحانات (11 نموذج)
            ('نموذج رياضيات 1', 'math_1_model', 'math_1_model', 'exam_models'),
            ('نموذج فيزياء 1', 'physics_1_model', 'physics_1_model', 'exam_models'),
            ('نموذج كيمياء 1', 'chemistry_1_model', 'chemistry_1_model', 'exam_models'),
            ('نموذج لغة عربية 1', 'arabic_1_model', 'arabic_1_model', 'exam_models'),
            ('نموذج لغة انجليزية 1', 'english_1_model', 'english_1_model', 'exam_models'),
            ('نموذج تاريخ 1', 'history_1_model', 'history_1_model', 'exam_models'),
            ('نموذج جغرافيا 1', 'geography_1_model', 'geography_1_model', 'exam_models'),
            ('نموذج علوم 1', 'science_1_model', 'science_1_model', 'exam_models'),
            ('نموذج تربية اسلامية 1', 'islamic_1_model', 'islamic_1_model', 'exam_models'),
            ('نموذج تربية وطنية 1', 'national_1_model', 'national_1_model', 'exam_models'),
            ('نموذج كمبيوتر 1', 'computer_1_model', 'computer_1_model', 'exam_models')
        ]

        # بيانات المرحلة الثانية (11 مادة + 3 مختبرات + 11 شرح)
        stage_2_subjects = [
            # المواد الدراسية (11 مادة)
            ('رياضيات 2', 'math_2', 'math_2', 'subjects'),
            ('فيزياء 2', 'physics_2', 'physics_2', 'subjects'),
            ('كيمياء 2', 'chemistry_2', 'chemistry_2', 'subjects'),
            ('لغة عربية 2', 'arabic_2', 'arabic_2', 'subjects'),
            ('لغة انجليزية 2', 'english_2', 'english_2', 'subjects'),
            ('تاريخ 2', 'history_2', 'history_2', 'subjects'),
            ('جغرافيا 2', 'geography_2', 'geography_2', 'subjects'),
            ('علوم 2', 'science_2', 'science_2', 'subjects'),
            ('تربية اسلامية 2', 'islamic_2', 'islamic_2', 'subjects'),
            ('تربية وطنية 2', 'national_2', 'national_2', 'subjects'),
            ('كمبيوتر 2', 'computer_2', 'computer_2', 'subjects'),
            
            # الشروحات (11 شرح)
            ('شرح رياضيات 2', 'math_2_exp', 'math_2_exp', 'explanations'),
            ('شرح فيزياء 2', 'physics_2_exp', 'physics_2_exp', 'explanations'),
            ('شرح كيمياء 2', 'chemistry_2_exp', 'chemistry_2_exp', 'explanations'),
            ('شرح لغة عربية 2', 'arabic_2_exp', 'arabic_2_exp', 'explanations'),
            ('شرح لغة انجليزية 2', 'english_2_exp', 'english_2_exp', 'explanations'),
            ('شرح تاريخ 2', 'history_2_exp', 'history_2_exp', 'explanations'),
            ('شرح جغرافيا 2', 'geography_2_exp', 'geography_2_exp', 'explanations'),
            ('شرح علوم 2', 'science_2_exp', 'science_2_exp', 'explanations'),
            ('شرح تربية اسلامية 2', 'islamic_2_exp', 'islamic_2_exp', 'explanations'),
            ('شرح تربية وطنية 2', 'national_2_exp', 'national_2_exp', 'explanations'),
            ('شرح كمبيوتر 2', 'computer_2_exp', 'computer_2_exp', 'explanations'),
            
            # المختبرات (3 مختبرات)
            ('مختبر فيزياء 2', 'physics_lab_2', 'physics_lab_2', 'lab'),
            ('مختبر كيمياء 2', 'chemistry_lab_2', 'chemistry_lab_2', 'lab'),
            ('مختبر علوم 2', 'science_lab_2', 'science_lab_2', 'lab'),
            
            # الامتحانات (11 امتحان)
            ('امتحان رياضيات 2', 'math_2_exam', 'math_2_exam', 'exams'),
            ('امتحان فيزياء 2', 'physics_2_exam', 'physics_2_exam', 'exams'),
            ('امتحان كيمياء 2', 'chemistry_2_exam', 'chemistry_2_exam', 'exams'),
            ('امتحان لغة عربية 2', 'arabic_2_exam', 'arabic_2_exam', 'exams'),
            ('امتحان لغة انجليزية 2', 'english_2_exam', 'english_2_exam', 'exams'),
            ('امتحان تاريخ 2', 'history_2_exam', 'history_2_exam', 'exams'),
            ('امتحان جغرافيا 2', 'geography_2_exam', 'geography_2_exam', 'exams'),
            ('امتحان علوم 2', 'science_2_exam', 'science_2_exam', 'exams'),
            ('امتحان تربية اسلامية 2', 'islamic_2_exam', 'islamic_2_exam', 'exams'),
            ('امتحان تربية وطنية 2', 'national_2_exam', 'national_2_exam', 'exams'),
            ('امتحان كمبيوتر 2', 'computer_2_exam', 'computer_2_exam', 'exams'),
            
            # نماذج الامتحانات (11 نموذج)
            ('نموذج رياضيات 2', 'math_2_model', 'math_2_model', 'exam_models'),
            ('نموذج فيزياء 2', 'physics_2_model', 'physics_2_model', 'exam_models'),
            ('نموذج كيمياء 2', 'chemistry_2_model', 'chemistry_2_model', 'exam_models'),
            ('نموذج لغة عربية 2', 'arabic_2_model', 'arabic_2_model', 'exam_models'),
            ('نموذج لغة انجليزية 2', 'english_2_model', 'english_2_model', 'exam_models'),
            ('نموذج تاريخ 2', 'history_2_model', 'history_2_model', 'exam_models'),
            ('نموذج جغرافيا 2', 'geography_2_model', 'geography_2_model', 'exam_models'),
            ('نموذج علوم 2', 'science_2_model', 'science_2_model', 'exam_models'),
            ('نموذج تربية اسلامية 2', 'islamic_2_model', 'islamic_2_model', 'exam_models'),
            ('نموذج تربية وطنية 2', 'national_2_model', 'national_2_model', 'exam_models'),
            ('نموذج كمبيوتر 2', 'computer_2_model', 'computer_2_model', 'exam_models')
        ]

        # بيانات المرحلة الثالثة (8 مواد + 2 مختبرات + 8 شرح)
        stage_3_subjects = [
            # المواد الدراسية (8 مواد)
            ('رياضيات 3', 'math_3', 'math_3', 'subjects'),
            ('فيزياء 3', 'physics_3', 'physics_3', 'subjects'),
            ('كيمياء 3', 'chemistry_3', 'chemistry_3', 'subjects'),
            ('لغة عربية 3', 'arabic_3', 'arabic_3', 'subjects'),
            ('لغة انجليزية 3', 'english_3', 'english_3', 'subjects'),
            ('تاريخ 3', 'history_3', 'history_3', 'subjects'),
            ('جغرافيا 3', 'geography_3', 'geography_3', 'subjects'),
            ('علوم 3', 'science_3', 'science_3', 'subjects'),
            
            # الشروحات (8 شرح)
            ('شرح رياضيات 3', 'math_3_exp', 'math_3_exp', 'explanations'),
            ('شرح فيزياء 3', 'physics_3_exp', 'physics_3_exp', 'explanations'),
            ('شرح كيمياء 3', 'chemistry_3_exp', 'chemistry_3_exp', 'explanations'),
            ('شرح لغة عربية 3', 'arabic_3_exp', 'arabic_3_exp', 'explanations'),
            ('شرح لغة انجليزية 3', 'english_3_exp', 'english_3_exp', 'explanations'),
            ('شرح تاريخ 3', 'history_3_exp', 'history_3_exp', 'explanations'),
            ('شرح جغرافيا 3', 'geography_3_exp', 'geography_3_exp', 'explanations'),
            ('شرح علوم 3', 'science_3_exp', 'science_3_exp', 'explanations'),
            
            # المختبرات (2 مختبرات)
            ('مختبر فيزياء 3', 'physics_lab_3', 'physics_lab_3', 'lab'),
            ('مختبر كيمياء 3', 'chemistry_lab_3', 'chemistry_lab_3', 'lab'),
            
            # الامتحانات (8 امتحان)
            ('امتحان رياضيات 3', 'math_3_exam', 'math_3_exam', 'exams'),
            ('امتحان فيزياء 3', 'physics_3_exam', 'physics_3_exam', 'exams'),
            ('امتحان كيمياء 3', 'chemistry_3_exam', 'chemistry_3_exam', 'exams'),
            ('امتحان لغة عربية 3', 'arabic_3_exam', 'arabic_3_exam', 'exams'),
            ('امتحان لغة انجليزية 3', 'english_3_exam', 'english_3_exam', 'exams'),
            ('امتحان تاريخ 3', 'history_3_exam', 'history_3_exam', 'exams'),
            ('امتحان جغرافيا 3', 'geography_3_exam', 'geography_3_exam', 'exams'),
            ('امتحان علوم 3', 'science_3_exam', 'science_3_exam', 'exams'),
            
            # نماذج الامتحانات (8 نموذج)
            ('نموذج رياضيات 3', 'math_3_model', 'math_3_model', 'exam_models'),
            ('نموذج فيزياء 3', 'physics_3_model', 'physics_3_model', 'exam_models'),
            ('نموذج كيمياء 3', 'chemistry_3_model', 'chemistry_3_model', 'exam_models'),
            ('نموذج لغة عربية 3', 'arabic_3_model', 'arabic_3_model', 'exam_models'),
            ('نموذج لغة انجليزية 3', 'english_3_model', 'english_3_model', 'exam_models'),
            ('نموذج تاريخ 3', 'history_3_model', 'history_3_model', 'exam_models'),
            ('نموذج جغرافيا 3', 'geography_3_model', 'geography_3_model', 'exam_models'),
            ('نموذج علوم 3', 'science_3_model', 'science_3_model', 'exam_models')
        ]

        # بيانات المرحلة الرابعة (نفس البيانات السابقة)
        stage_4_subjects = [
            ('الكهرومغناطيسية', 'electromagnetism', 'electromagnetism', 'subjects'),
            ('الفيزياء الصلبة', 'solid_physics', 'solid_physics', 'subjects'),
            ('الليزر', 'laser', 'laser', 'subjects'),
            ('القياس والتقويم', 'measurement', 'measurement', 'subjects'),
            ('النووية', 'nuclear', 'nuclear', 'subjects'),
            ('التربية العملية', 'practical_education', 'practical_education', 'subjects'),
            ('الكمي', 'quantum', 'quantum', 'subjects'),
            ('شرح الكهرومغناطيسية', 'electromagnetism_exp', 'electromagnetism_exp', 'explanations'),
            ('شرح الفيزياء الصلبة', 'solid_physics_exp', 'solid_physics_exp', 'explanations'),
            ('شرح الليزر', 'laser_exp', 'laser_exp', 'explanations'),
            ('شرح القياس والتقويم', 'measurement_exp', 'measurement_exp', 'explanations'),
            ('شرح النووية', 'nuclear_exp', 'nuclear_exp', 'explanations'),
            ('شرح التربية العملية', 'practical_education_exp', 'practical_education_exp', 'explanations'),
            ('شرح الكمي', 'quantum_exp', 'quantum_exp', 'explanations'),
            ('تجربة 1', 'lab_experiment_1', 'lab_experiment_1', 'lab'),
            ('تجربة 2', 'lab_experiment_2', 'lab_experiment_2', 'lab'),
            ('تجربة 3', 'lab_experiment_3', 'lab_experiment_3', 'lab'),
            ('تجربة 4', 'lab_experiment_4', 'lab_experiment_4', 'lab'),
            ('تجربة 5', 'lab_experiment_5', 'lab_experiment_5', 'lab'),
            ('تجربة 6', 'lab_experiment_6', 'lab_experiment_6', 'lab'),
            ('امتحان الكهرومغناطيسية', 'electromagnetism_exam', 'electromagnetism_exam', 'exams'),
            ('امتحان الفيزياء الصلبة', 'solid_physics_exam', 'solid_physics_exam', 'exams'),
            ('امتحان الليزر', 'laser_exam', 'laser_exam', 'exams'),
            ('امتحان القياس والتقويم', 'measurement_exam', 'measurement_exam', 'exams'),
            ('امتحان النووية', 'nuclear_exam', 'nuclear_exam', 'exams'),
            ('امتحان التربية العملية', 'practical_education_exam', 'practical_education_exam', 'exams'),
            ('امتحان الكمي', 'quantum_exam', 'quantum_exam', 'exams'),
            ('نموذج الكهرومغناطيسية', 'electromagnetism_model', 'electromagnetism_model', 'exam_models'),
            ('نموذج الفيزياء الصلبة', 'solid_physics_model', 'solid_physics_model', 'exam_models'),
            ('نموذج الليزر', 'laser_model', 'laser_model', 'exam_models'),
            ('نموذج القياس والتقويم', 'measurement_model', 'measurement_model', 'exam_models'),
            ('نموذج النووية', 'nuclear_model', 'nuclear_model', 'exam_models'),
            ('نموذج التربية العملية', 'practical_education_model', 'practical_education_model', 'exam_models'),
            ('نموذج الكمي', 'quantum_model', 'quantum_model', 'exam_models')
        ]

        stages_data = {
            1: stage_1_subjects,
            2: stage_2_subjects,
            3: stage_3_subjects,
            4: stage_4_subjects
        }

        with self.conn:
            # إضافة المواد لكل مرحلة
            for stage, subjects in stages_data.items():
                for subject in subjects:
                    self.conn.execute(f'''
                    INSERT OR IGNORE INTO stage_{stage}_subjects (name_ar, name_en, key, category)
                    VALUES (?, ?, ?, ?)
                    ''', subject)

            # إضافة المطور كأدمن
            self.conn.execute('''
            INSERT OR IGNORE INTO admins (user_id, added_by)
            VALUES (?, ?)
            ''', (DEVELOPER_ID, DEVELOPER_ID))
            
            # إعدادات الذكاء الاصطناعي الافتراضية
            self.conn.execute('''
            INSERT OR IGNORE INTO ai_settings (id, enabled, restricted)
            VALUES (1, 0, 0)
            ''')

    # ========== User Stage Methods ========== #
    def get_user_stage(self, user_id):
        """Get user's stage and full name"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT stage, full_name FROM users_stages WHERE user_id=?', (user_id,))
        return cursor.fetchone()

    def set_user_stage(self, user_id, full_name, stage):
        """Set user's stage and full name"""
        with self.conn:
            self.conn.execute('''
            INSERT OR REPLACE INTO users_stages (user_id, full_name, stage)
            VALUES (?, ?, ?)
            ''', (user_id, full_name, stage))
            return True

    # ========== Stage Subjects Methods ========== #
    def get_stage_subject(self, stage, identifier):
        """Get subject by key or name for specific stage"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
        SELECT name_ar, name_en, key, category FROM stage_{stage}_subjects 
        WHERE key=? OR name_ar=? OR name_en=?
        ''', (identifier, identifier, identifier))
        return cursor.fetchone()

    def get_stage_subjects_by_category(self, stage, category):
        """Get all subjects in a specific category for stage"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
        SELECT name_ar, key FROM stage_{stage}_subjects 
        WHERE category=? 
        ORDER BY name_en
        ''', (category,))
        return cursor.fetchall()

    # ========== Stage Content Methods ========== #
    def get_next_stage_content_number(self, stage, subject_key, chapter_num):
        """Get the next content number for a chapter in specific stage"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
        SELECT COUNT(*) FROM stage_{stage}_content 
        WHERE subject_key=? AND chapter_num=?
        ''', (subject_key, chapter_num))
        return cursor.fetchone()[0] + 1

    def add_stage_content(self, stage, subject_key, chapter_num, content_type, file_id=None, text=None, description=None, added_by=None):
        """Add content with automatic numbering for specific stage"""
        with self.conn:
            content_number = self.get_next_stage_content_number(stage, subject_key, chapter_num)
            
            if not description:
                content_type_names = {
                    'video': 'فيديو',
                    'document': 'ملف',
                    'photo': 'صورة',
                    'text': 'نص'
                }
                description = f"{content_type_names.get(content_type, 'محتوى')} {content_number}"
            
            self.conn.execute(f'''
            INSERT INTO stage_{stage}_content (subject_key, chapter_num, content_type, file_id, text_content, description, added_by, content_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (subject_key, chapter_num, content_type, file_id, text, description, added_by, content_number))
            
            return content_number

    def get_stage_chapter_content_list(self, stage, subject_key, chapter_num):
        """Get list of content for a chapter in specific stage with IDs"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
        SELECT id, content_type, description FROM stage_{stage}_content
        WHERE subject_key=? AND chapter_num=?
        ORDER BY content_number
        ''', (subject_key, chapter_num))
        return cursor.fetchall()

    def get_stage_content_by_id(self, stage, content_id):
        """Get specific content by ID for stage"""
        cursor = self.conn.cursor()
        cursor.execute(f'''
        SELECT content_type, file_id, text_content, description, added_by, subject_key, chapter_num 
        FROM stage_{stage}_content
        WHERE id=?
        ''', (content_id,))
        return cursor.fetchone()

    def delete_stage_content(self, stage, content_id):
        """Delete content by ID for stage"""
        with self.conn:
            self.conn.execute(f'DELETE FROM stage_{stage}_content WHERE id=?', (content_id,))
            return self.conn.total_changes > 0

    # ========== User Methods ========== #
    def add_user(self, user_id, username, first_name, last_name):
        """Add or update user"""
        is_new = 1
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id=?', (user_id,))
        if cursor.fetchone():
            is_new = 0
        
        with self.conn:
            self.conn.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_active, is_new)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (user_id, username, first_name, last_name, is_new))
            return is_new

    def get_all_users(self):
        """Get all users"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        return [row[0] for row in cursor.fetchall()]

    def count_users(self):
        """Count all users"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]
    
    def get_new_users(self):
        """Get new users since last check"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT user_id, first_name, last_name, username 
        FROM users 
        WHERE is_new = 1
        ''')
        users = cursor.fetchall()
        
        if users:
            self.conn.execute('UPDATE users SET is_new = 0 WHERE is_new = 1')
            
        return users

    def ban_user(self, user_id, reason=None):
        """Ban a user"""
        with self.conn:
            self.conn.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))
            return self.conn.total_changes > 0

    def unban_user(self, user_id):
        """Unban a user"""
        with self.conn:
            self.conn.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))
            return self.conn.total_changes > 0

    def is_banned(self, user_id):
        """Check if user is banned"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else False

    # ========== Admin Methods ========== #
    def add_admin(self, user_id, username, full_name, added_by):
        """Add new admin"""
        with self.conn:
            self.conn.execute('''
            INSERT OR REPLACE INTO admins (user_id, username, full_name, added_by)
            VALUES (?, ?, ?, ?)
            ''', (user_id, username, full_name, added_by))
            return True

    def remove_admin(self, user_id):
        """Remove admin (except developer)"""
        if user_id == DEVELOPER_ID:
            return False
            
        with self.conn:
            self.conn.execute('DELETE FROM admins WHERE user_id=?', (user_id,))
            return self.conn.total_changes > 0

    def get_admins(self):
        """Get list of all admins"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username, full_name FROM admins')
        return cursor.fetchall()

    def is_admin(self, user_id):
        """Check if user is admin"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM admins WHERE user_id=?', (user_id,))
        return cursor.fetchone() is not None

    # ========== Channel Methods ========== #
    def add_required_channel(self, channel_id, channel_username, channel_title, added_by):
        """Add a required channel"""
        with self.conn:
            self.conn.execute('DELETE FROM required_channels')
            
            self.conn.execute('''
            INSERT INTO required_channels (channel_id, channel_username, channel_title, added_by)
            VALUES (?, ?, ?, ?)
            ''', (channel_id, channel_username, channel_title, added_by))
            return True

    def get_required_channel(self):
        """Get the required channel info"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT channel_id, channel_username, channel_title FROM required_channels LIMIT 1')
        return cursor.fetchone()

    def remove_required_channel(self):
        """Remove the required channel"""
        with self.conn:
            self.conn.execute('DELETE FROM required_channels')
            return self.conn.total_changes > 0

    # ========== Comment Methods ========== #
    def add_comment(self, content_id, user_id, text, content_title, stage=4):
        """Add a new comment with content title and stage"""
        with self.conn:
            self.conn.execute('''
            INSERT INTO comments (content_id, user_id, text, content_title, stage)
            VALUES (?, ?, ?, ?, ?)
            ''', (content_id, user_id, text, content_title, stage))
            return True

    def get_comments(self, content_id, stage=4):
        """Get comments for specific content with content title"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT c.id, c.text, c.date, u.first_name, u.username, c.content_title 
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.content_id = ? AND c.stage = ?
        ORDER BY c.date DESC
        ''', (content_id, stage))
        return cursor.fetchall()
    
    def get_all_comments(self):
        """Get all comments for admin view"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT c.id, c.text, c.date, u.first_name, u.username, c.content_title, c.stage
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        ORDER BY c.date DESC
        LIMIT 50
        ''')
        return cursor.fetchall()

    # ========== Search Channel Methods ========== #
    def add_search_channel(self, channel_id, channel_username, channel_title, added_by):
        """Add a search channel"""
        with self.conn:
            self.conn.execute('''
            INSERT OR IGNORE INTO search_channels (channel_id, channel_username, channel_title, added_by)
            VALUES (?, ?, ?, ?)
            ''', (channel_id, channel_username, channel_title, added_by))
            return self.conn.total_changes > 0

    def get_search_channels(self):
        """Get all search channels"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT channel_id, channel_username, channel_title FROM search_channels')
        return cursor.fetchall()

    def remove_search_channel(self, channel_id):
        """Remove a search channel"""
        with self.conn:
            self.conn.execute('DELETE FROM search_channels WHERE channel_id = ?', (channel_id,))
            return self.conn.total_changes > 0

    # ========== Support Ticket Methods ========== #
    def add_support_ticket(self, user_id, message, stage=4):
        """Add a new support ticket"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO support_tickets (user_id, message, stage)
        VALUES (?, ?, ?)
        ''', (user_id, message, stage))
        self.conn.commit()
        return cursor.lastrowid

    def get_support_tickets(self):
        """Get all support tickets with user info"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT t.id, t.message, t.stage, u.first_name, u.username, t.date
        FROM support_tickets t
        JOIN users u ON t.user_id = u.user_id
        ORDER BY t.date DESC
        ''')
        return cursor.fetchall()

    def get_ticket_info(self, ticket_id):
        """Get ticket information with user details"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT t.user_id, t.message, t.stage, u.first_name, u.username, t.date
        FROM support_tickets t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.id = ?
        ''', (ticket_id,))
        return cursor.fetchone()

    def delete_support_ticket(self, ticket_id):
        """Delete support ticket after replying"""
        with self.conn:
            self.conn.execute('DELETE FROM support_tickets WHERE id = ?', (ticket_id,))
            return self.conn.total_changes > 0

    # ========== AI Methods ========== #
    def get_ai_settings(self):
        """Get AI settings"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT enabled, restricted FROM ai_settings WHERE id = 1')
        return cursor.fetchone()

    def update_ai_settings(self, enabled=None, restricted=None):
        """Update AI settings"""
        with self.conn:
            if enabled is not None and restricted is not None:
                self.conn.execute('UPDATE ai_settings SET enabled = ?, restricted = ? WHERE id = 1', (enabled, restricted))
            elif enabled is not None:
                self.conn.execute('UPDATE ai_settings SET enabled = ? WHERE id = 1', (enabled,))
            elif restricted is not None:
                self.conn.execute('UPDATE ai_settings SET restricted = ? WHERE id = 1', (restricted,))
            return True

    def add_ai_user(self, user_id, added_by):
        """Add user to AI allowed list"""
        with self.conn:
            self.conn.execute('''
            INSERT OR IGNORE INTO ai_allowed_users (user_id, added_by)
            VALUES (?, ?)
            ''', (user_id, added_by))
            return self.conn.total_changes > 0

    def remove_ai_user(self, user_id):
        """Remove user from AI allowed list"""
        with self.conn:
            self.conn.execute('DELETE FROM ai_allowed_users WHERE user_id = ?', (user_id,))
            return self.conn.total_changes > 0

    def get_ai_users(self):
        """Get all AI allowed users"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM ai_allowed_users')
        return [row[0] for row in cursor.fetchall()]

    def is_ai_allowed(self, user_id):
        """Check if user is allowed to use AI"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM ai_allowed_users WHERE user_id = ?', (user_id,))
        return cursor.fetchone() is not None

# Initialize database
db = Database()