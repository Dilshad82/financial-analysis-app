import customtkinter as ctk
import os
from google import genai
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class MobileStyleAssistant(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("مساعد التحليل الذكي")
        self.geometry("400x650")

        # إعداد العميل الذكي من مكتبة google-genai الحديثة
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.ai_client = genai.Client(api_key=api_key)
        else:
            self.ai_client = None

        # واجهة المستخدم
        self.label = ctk.CTkLabel(self, text="📱 مساعد السوق الذكي", font=("Arial", 18, "bold"))
        self.label.pack(pady=15)

        self.input_entry = ctk.CTkEntry(self, placeholder_text="أدخل استفسارك هنا...", width=320, height=40)
        self.input_entry.pack(pady=10)

        self.analyze_button = ctk.CTkButton(self, text="تحليل الاستفسار 🚀", command=self.analyze_tasks)
        self.analyze_button.pack(pady=10)

        self.results_box = ctk.CTkTextbox(self, width=350, height=420, font=("Arial", 13))
        self.results_box.pack(pady=15)
        self.results_box.configure(state="disabled")

    def analyze_tasks(self):
        prompt = self.input_entry.get().strip()
        if not prompt:
            self.show_output("❌ الرجاء كتابة استفسار أولاً!")
            return

        if not self.ai_client:
            self.show_output("❌ لم يتم العثور على مفتاح GEMINI_API_KEY في ملف .env")
            return

        try:
            self.show_output("⏳ جاري التحليل...")

            # استخدام موديل gemini-2.5-flash الحديث
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )

            self.show_output(f"🤖 الترتيب الذكي:\n\n{response.text}")

        except Exception as e:
            self.show_output(f"❌ حدث خطأ: {e}")

    def show_output(self, message):
        self.results_box.configure(state="normal")
        self.results_box.delete("1.0", "end")
        self.results_box.insert("1.0", message)
        self.results_box.configure(state="disabled")


if __name__ == "__main__":
    app = MobileStyleAssistant()
    app.mainloop()