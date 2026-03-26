import streamlit as st
import requests
import smtplib
import os
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION — عدّل هذا القسم فقط
# ══════════════════════════════════════════════════════════════

GMAIL_ADDRESS   = "Wijdan.psyc@gmail.com"
GMAIL_PASSWORD  = "rias eeul lyuu stce"
THERAPIST_EMAIL = "Wijdan.psyc@gmail.com"
LOGO_FILE       = "logo.png"

# ══════════════════════════════════════════════════════════════
#  أسئلة اختبار الشخصية الخمسة الكبرى — 50 فقرة
# ══════════════════════════════════════════════════════════════

BFPT_QUESTIONS = [
    {"id": 1,  "text": "أكون روح الحفلة وعنصر الحيوية فيها.",
               "hint": "أشعر بالتدفق الطبيعي في المواقف الاجتماعية وأستمتع بكوني محور الاهتمام."},
    {"id": 2,  "text": "لا أشعر بقدر كبير من الاهتمام بالآخرين.",
               "hint": "لا أجد نفسي مشغولاً بما يمر به الآخرون من تجارب أو صعوبات."},
    {"id": 3,  "text": "أكون دائماً مستعداً ومهيأً.",
               "hint": "أحرص على التخطيط المسبق وتجهيز كل ما يلزم قبل الحاجة إليه."},
    {"id": 4,  "text": "أنفعل وأتوتر بسرعة.",
               "hint": "تؤثر الضغوط والمشكلات البسيطة على مزاجي وراحتي النفسية بشكل سريع."},
    {"id": 5,  "text": "أمتلك ثروة لغوية واسعة.",
               "hint": "أعبّر عن نفسي بيُسر وأستخدم مفردات متنوعة ودقيقة."},
    {"id": 6,  "text": "لا أتحدث كثيراً.",
               "hint": "أميل إلى الصمت وأفضّل الاستماع على الكلام في معظم المواقف."},
    {"id": 7,  "text": "أهتم بالناس وأنجذب نحوهم.",
               "hint": "أستمتع بالتعرف على حياة الآخرين وأفكارهم وتجاربهم."},
    {"id": 8,  "text": "أترك متعلقاتي مبعثرة.",
               "hint": "كثيراً ما أترك أغراضي دون ترتيب بدلاً من إعادتها إلى مكانها."},
    {"id": 9,  "text": "أكون مرتاحاً وهادئاً في معظم الأوقات.",
               "hint": "أشعر بالهدوء عموماً ولا أصاب بالقلق أو التوتر بسهولة."},
    {"id": 10, "text": "أجد صعوبة في فهم الأفكار المجردة.",
               "hint": "يصعب عليّ استيعاب المفاهيم النظرية أو الفلسفية."},
    {"id": 11, "text": "أشعر بالارتياح بين الناس.",
               "hint": "يبدو لي التواجد مع الآخرين أمراً طبيعياً وسهلاً."},
    {"id": 12, "text": "أُسيء إلى الآخرين أحياناً.",
               "hint": "قد أقول أشياء تؤذي مشاعر الآخرين أو تُسيء إليهم، سواء قصدت ذلك أم لا."},
    {"id": 13, "text": "أُولي الاهتمام للتفاصيل الدقيقة.",
               "hint": "أُلاحظ الأمور الصغيرة التي قد يغفل عنها غيري وأحرص على الدقة والشمولية."},
    {"id": 14, "text": "أنشغل بالتفكير والقلق كثيراً.",
               "hint": "كثيراً ما أجد نفسي أفكر فيما قد يسوء أو يحدث من مشكلات."},
    {"id": 15, "text": "أمتلك خيالاً واسعاً وخصباً.",
               "hint": "يصوّر ذهني بوضوح مشاهد ورؤى وأفكاراً تخيلية تلقائياً."},
    {"id": 16, "text": "أفضّل البقاء في الخلفية بعيداً عن الأضواء.",
               "hint": "أريح نفسي بعدم اللفت إليها بدلاً من أن أكون محور الاهتمام."},
    {"id": 17, "text": "أتعاطف مع مشاعر الآخرين.",
               "hint": "حين يمر شخص بحزن أو ضائقة، أشعر بألمه بصدق."},
    {"id": 18, "text": "أُحدث الفوضى في الأمور.",
               "hint": "أميل إلى ترك المهام أو الأماكن في حالة من الفوضى أو عدم الاكتمال."},
    {"id": 19, "text": "نادراً ما أشعر بالحزن أو الكآبة.",
               "hint": "لا أعاني من مشاعر الحزن أو الانكسار في الغالب."},
    {"id": 20, "text": "لا يستهويني التفكير في الأفكار المجردة.",
               "hint": "أفضّل الموضوعات العملية والملموسة على النقاشات النظرية."},
    {"id": 21, "text": "أبادر إلى بدء المحادثات.",
               "hint": "أكثر ما أبدأ الحديث مع الآخرين دون انتظار منهم."},
    {"id": 22, "text": "لا يستأثر اهتمامي مشاكل الآخرين.",
               "hint": "لا أشعر بدافع للانخراط في صعوبات الآخرين أو مشاغلهم."},
    {"id": 23, "text": "أُنجز واجباتي اليومية فور الشروع فيها.",
               "hint": "أتعامل مع المهام والمسؤوليات بسرعة دون تأجيل أو مماطلة."},
    {"id": 24, "text": "يسهل إزعاجي وإخراجي عن حالي.",
               "hint": "الضوضاء والمقاطعات والتغيرات المفاجئة تُخل براحتي بسهولة."},
    {"id": 25, "text": "أتوصل إلى أفكار متميزة وإبداعية.",
               "hint": "كثيراً ما أُفكر في حلول وأطروحات جديدة ومفيدة."},
    {"id": 26, "text": "لا يكون لديّ الكثير لأقوله.",
               "hint": "أجد في الغالب أن مساهمتي في الحوارات محدودة."},
    {"id": 27, "text": "أتسم برقة القلب والشعور بالآخرين.",
               "hint": "يتأثر قلبي بسرعة بآلام الآخرين وأميل إلى الرفق والرحمة."},
    {"id": 28, "text": "كثيراً ما أنسى إعادة الأشياء إلى مكانها.",
               "hint": "أُضيّع الأغراض كثيراً لأنني لا أعيدها حيث أخذتها."},
    {"id": 29, "text": "يسهل استفزازي وإثارة انفعالي.",
               "hint": "مشاعري تتقلب بسرعة حين لا تسير الأمور كما توقعت."},
    {"id": 30, "text": "لا أتمتع بخيال واسع.",
               "hint": "أجد صعوبة في تصوّر سيناريوهات أو ابتكار أفكار جديدة."},
    {"id": 31, "text": "أتحدث مع أشخاص كثيرين ومختلفين في التجمعات.",
               "hint": "في المناسبات الاجتماعية أنتقل بين المجموعات وأتحدث مع أناس متنوعين."},
    {"id": 32, "text": "لا يستأثر اهتمامي الآخرون في الغالب.",
               "hint": "لا أجد نفسي فضولياً تجاه حياة الآخرين أو مشاعرهم."},
    {"id": 33, "text": "أحب النظام والترتيب.",
               "hint": "أشعر براحة أكبر حين تكون الأمور منظمة ومرتبة وفق نسق واضح."},
    {"id": 34, "text": "يتبدل مزاجي كثيراً.",
               "hint": "حالتي المزاجية تتغير بتكرار خلال اليوم الواحد."},
    {"id": 35, "text": "أستوعب الأمور بسرعة.",
               "hint": "أستطيع فهم المعلومات والتعليمات والمفاهيم الجديدة بسرعة ويُسر."},
    {"id": 36, "text": "لا أحب أن أكون محط الأنظار.",
               "hint": "يُزعجني أن يُلاحظني الآخرون أو يُفردوني أمام الناس."},
    {"id": 37, "text": "أُخصص وقتاً لمساعدة الآخرين.",
               "hint": "أحرص على التواصل مع من حولي لدعمهم والاطمئنان عليهم."},
    {"id": 38, "text": "أتهاون في أداء مسؤولياتي.",
               "hint": "أتجنب أحياناً أو أؤجل الواجبات التي يُفترض بي القيام بها."},
    {"id": 39, "text": "أعاني من تقلبات مزاجية متكررة.",
               "hint": "مشاعري تتغير بشكل متقلب وغير متوقع بصفة منتظمة."},
    {"id": 40, "text": "أستخدم مفردات رفيعة ومتخصصة.",
               "hint": "أدمج بشكل طبيعي مصطلحات متقدمة ومركبة في حديثي أو كتابتي."},
    {"id": 41, "text": "لا يزعجني أن أكون محور الاهتمام.",
               "hint": "أشعر بالارتياح وربما بالبهجة حين تتجه إليّ الأنظار."},
    {"id": 42, "text": "أستشعر مشاعر الآخرين.",
               "hint": "أحس بما يشعر به الآخر حتى وإن لم يُصرّح بذلك."},
    {"id": 43, "text": "أسير وفق جدول زمني منظم.",
               "hint": "أُخطط ليومي وألتزم بالروتين عوضاً عن التصرف بشكل عفوي."},
    {"id": 44, "text": "سرعان ما أنزعج وأشعر بالتهيج.",
               "hint": "المصادر الصغيرة للإزعاج تُثير انفعالي أكثر مما ينبغي."},
    {"id": 45, "text": "أُمضي وقتاً في التأمل والتفكر العميق.",
               "hint": "أتوقف بانتظام للتفكر بعمق في تجاربي وأفكاري وقراراتي."},
    {"id": 46, "text": "أكون صامتاً في حضور الغرباء.",
               "hint": "أتحفظ وأقل الكلام حين أكون بين أشخاص لا أعرفهم."},
    {"id": 47, "text": "أجعل الآخرين يشعرون بالراحة والطمأنينة.",
               "hint": "يميل الآخرون إلى الشعور بالارتياح والانبساط في حضوري."},
    {"id": 48, "text": "أكون صارماً ودقيقاً في عملي.",
               "hint": "أضع لنفسي معايير عالية وأُولي الجودة والدقة اهتماماً بالغاً."},
    {"id": 49, "text": "كثيراً ما أشعر بالحزن والكآبة.",
               "hint": "أعاني بشكل متكرر من مشاعر الحزن والانكسار وتدني المزاج."},
    {"id": 50, "text": "ذهني مليء بالأفكار دائماً.",
               "hint": "تتدفق في ذهني باستمرار أفكار وإمكانيات ومفاهيم جديدة."},
]

SCALE_OPTIONS = {
    1: "١ — لا أوافق",
    2: "٢ — لا أوافق نسبياً",
    3: "٣ — محايد",
    4: "٤ — أوافق نسبياً",
    5: "٥ — أوافق",
}

# ══════════════════════════════════════════════════════════════
#  الحساب والتصنيف
# ══════════════════════════════════════════════════════════════

def calculate_scores(r: dict) -> dict:
    E = 20 + r[1]  - r[6]  + r[11] - r[16] + r[21] - r[26] + r[31] - r[36] + r[41] - r[46]
    A = 14 - r[2]  + r[7]  - r[12] + r[17]  - r[22] + r[27] - r[32] + r[37] + r[42] + r[47]
    C = 14 + r[3]  - r[8]  + r[13] - r[18]  + r[23] - r[28] + r[33] - r[38] + r[43] + r[48]
    N = 38 - r[4]  + r[9]  - r[14] + r[19]  - r[24] - r[29] - r[34] - r[39] - r[44] - r[49]
    O =  8 + r[5]  - r[10] + r[15] - r[20]  + r[25] - r[30] + r[35] + r[40] + r[45] + r[50]
    return {"E": E, "A": A, "C": C, "N": N, "O": O}

def get_level(score: int) -> str:
    if score <= 13:   return "منخفض"
    elif score <= 26: return "متوسط"
    else:             return "مرتفع"

TRAIT_META = {
    "E": {
        "name": "الانبساطية",
        "name_en": "Extroversion",
        "color": "#4A90D9",
        "low":      "يميل إلى الانطوائية والتأمل الداخلي، ويُفضّل العمل باستقلالية أو في بيئات أكثر هدوءاً وخصوصية.",
        "moderate": "يُظهر توازناً بين الانخراط الاجتماعي والميل نحو العزلة بحسب السياق والظروف.",
        "high":     "شخصية اجتماعية نشطة تستمد طاقتها من التفاعل مع المحيط الخارجي والآخرين.",
    },
    "A": {
        "name": "الطيبة والتوافقية",
        "name_en": "Agreeableness",
        "color": "#5CB85C",
        "low":      "يميل إلى المباشرة والتنافسية، وقد يُقدّم أهدافه الشخصية على حساب الانسجام الجماعي.",
        "moderate": "قادر على التعاون والمرونة مع الحفاظ على تأكيد احتياجاته الشخصية عند الاقتضاء.",
        "high":     "دافئ المشاعر، تعاوني بدرجة عالية، يُقدّم احتياجات الآخرين ويسعى إلى الوئام الاجتماعي.",
    },
    "C": {
        "name": "الضمير الحي والانضباط",
        "name_en": "Conscientiousness",
        "color": "#F0AD4E",
        "low":      "قد يتسم بالمرونة والعفوية، لكنه قد يعاني من صعوبة في التنظيم والمتابعة المنهجية.",
        "moderate": "موثوق ومنظم بشكل عام، مع بعض التفاوت في إنجاز المهام والالتزام الذاتي.",
        "high":     "منضبط، منظم، يسعى نحو الأهداف بجدية؛ يتسم بأخلاقيات عمل راسخة وانتباه دقيق للتفاصيل.",
    },
    "N": {
        "name": "العصابية",
        "name_en": "Neuroticism",
        "color": "#D9534F",
        "low":      "يتسم بالاستقرار الانفعالي والهدوء تحت الضغط، وأقل تأثراً بالضغوط والمثيرات.",
        "moderate": "يُبدي استجابة انفعالية معتدلة؛ قد يشعر بالضغط في المواقف الصعبة لكنه يتكيف في الغالب.",
        "high":     "عُرضة للضائقة الانفعالية وتقلبات المزاج وارتفاع حساسية التوتر؛ قد يعاني من القلق والتهيج أو انخفاض المزاج.",
    },
    "O": {
        "name": "الانفتاح على التجربة",
        "name_en": "Openness to Experience",
        "color": "#9B59B6",
        "low":      "يُفضّل الروتين والتفكير الواقعي الملموس والبيئات المألوفة؛ عملي وأرضي الطابع.",
        "moderate": "يُبدي فضولاً وإبداعاً في بعض المجالات مع تفضيله للبنية والقدرة على التنبؤ في مجالات أخرى.",
        "high":     "خيالي بدرجة عالية، فضولي فكرياً، منجذب نحو الأفكار المبتكرة والمساعي الإبداعية والتفكير المجرد.",
    },
}

# ══════════════════════════════════════════════════════════════
#  توليد التقرير عبر Groq
# ══════════════════════════════════════════════════════════════

def generate_report(client_name, scores, responses):
    trait_lines = "\n".join(
        f"  {TRAIT_META[t]['name']} ({TRAIT_META[t]['name_en']}) ({t}): {scores[t]}/40 — {get_level(scores[t])}"
        for t in ["E", "A", "C", "N", "O"]
    )

    prompt = f"""أنت طبيب نفسي إكلينيكي متخصص تكتب تقريراً تقييمياً مهنياً وسرياً للشخصية.

اكتب التقرير كاملاً باللغة العربية الفصحى ذات الطابع الإكلينيكي الرسمي.
تجنّب الأسلوب الحرفي وأسلوب الترجمة المباشرة. استخدم المصطلحات النفسية العربية المعتمدة.

المُقيَّم: {client_name}
الاختبار: اختبار الشخصية الخمسة الكبرى (BFPT) — 50 فقرة، مقياس من 1 إلى 5، الدرجة من 0 إلى 40 لكل سمة

درجات السمات:
{trait_lines}

مرجع التفسير:
- 0–13: مستوى منخفض  |  14–26: مستوى متوسط  |  27–40: مستوى مرتفع

وصف السمات:
- الانبساطية (E): مدى استمداد الفرد طاقته من المحيط الخارجي والتفاعل الاجتماعي. مرتفع = اجتماعي نشط؛ منخفض = انطوائي يُفضّل الاستقلالية.
- الطيبة والتوافقية (A): مدى تكيّف الفرد مع الآخرين. مرتفع = متعاون ودود؛ منخفض = مباشر صريح.
- الضمير الحي والانضباط (C): مدى التنظيم والمثابرة. مرتفع = منضبط ملتزم؛ منخفض = مرن عفوي.
- العصابية (N): مستوى الاستجابة الانفعالية. مرتفع = قابل للتأثر الانفعالي؛ منخفض = مستقر انفعالياً.
- الانفتاح على التجربة (O): الفضول الفكري والانجذاب للجديد. مرتفع = خيالي مبدع؛ منخفض = عملي واقعي.

اكتب تقريراً إكلينيكياً متكاملاً يشمل الأقسام التالية:

١. نظرة عامة على التقييم
   - الأداة المستخدمة، الغرض منها، سياق التطبيق.

٢. الملف الشخصي العام
   - سرد إكلينيكي متكامل للملف الشخصي للمُقيَّم وفق النموذج الخماسي. استحضر جميع الدرجات الخمس.
   - أبرز السمات الطاغية وأي أنماط إكلينيكية لافتة أو تناقضات بين السمات.

٣. تحليل السمات بشكل منفرد
   لكل سمة من السمات الخمس اكتب فقرة إكلينيكية تتضمن:
   - الدرجة ومستوى التصنيف (منخفض / متوسط / مرتفع)
   - التفسير الإكلينيكي الخاص بهذا المُقيَّم
   - الانعكاسات على السلوك والعلاقات والعمل والصحة النفسية

٤. تفاعل السمات والأنماط الإكلينيكية
   - ناقش كيف يُكوّن تضافر الدرجات صورة شخصية متماسكة.
   - أبرز التفاعلات الدالة (مثل: عصابية مرتفعة مع انبساطية منخفضة، ضمير مرتفع مع توافقية مرتفعة...).

٥. نقاط القوة ومحاور النمو
   - استناداً إلى الملف، حدّد نقاط القوة النفسية للمُقيَّم.
   - حدّد المحاور التي قد تستفيد من الدعم العلاجي أو التطوير الذاتي.

٦. التوجيهات العلاجية والعملية
   - اقتراحات مستندة إلى الأدلة تشمل: أسلوب التدخل العلاجي، نمط التواصل، توصيات عملية.
   - كيف يؤثر هذا الملف على العلاقة العلاجية.

٧. الخلاصة الإكلينيكية
   - فقرة موجزة صالحة للتوثيق في الملف الإكلينيكي وفق الصيغة المعتمدة:
     "وفقاً لاختبار الشخصية الخمسة الكبرى (BFPT)، يُفيد المُقيَّم ذاتياً بـ [وصف كل سمة مع درجتها]."

استخدم أسلوباً إكلينيكياً رصيناً. كن دقيقاً ومحدداً وفق الدرجات الفعلية. التقرير جاهز للإدراج في الملف الإكلينيكي."""

    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("مفتاح GROQ_API_KEY غير موجود في إعدادات التطبيق.")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2500,
            "temperature": 0.4,
        },
        timeout=60,
    )

    if not response.ok:
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise Exception(f"خطأ في Groq API {response.status_code}: {error_detail}")

    return response.json()["choices"][0]["message"]["content"].strip()

# ══════════════════════════════════════════════════════════════
#  إنشاء تقرير PDF
# ══════════════════════════════════════════════════════════════

def create_pdf_report(path, client_name, scores, report_text, timestamp):
    DARK   = colors.HexColor("#1C1917")
    WARM   = colors.HexColor("#6B5B45")
    LIGHT  = colors.HexColor("#F7F4F0")
    BORDER = colors.HexColor("#DDD5C8")
    WHITE  = colors.white

    TRAIT_COLORS = {
        "E": colors.HexColor("#4A90D9"),
        "A": colors.HexColor("#5CB85C"),
        "C": colors.HexColor("#F0AD4E"),
        "N": colors.HexColor("#D9534F"),
        "O": colors.HexColor("#9B59B6"),
    }

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    title_s   = ParagraphStyle("T",  fontName="Helvetica-Bold",    fontSize=18, textColor=DARK,  alignment=TA_CENTER, spaceAfter=3)
    sub_s     = ParagraphStyle("S",  fontName="Helvetica",          fontSize=10, textColor=WARM,  alignment=TA_CENTER, spaceAfter=2)
    meta_s    = ParagraphStyle("M",  fontName="Helvetica",          fontSize=8,  textColor=WARM,  alignment=TA_CENTER, spaceAfter=12)
    section_s = ParagraphStyle("Se", fontName="Helvetica-Bold",     fontSize=10, textColor=WARM,  spaceBefore=12, spaceAfter=4)
    body_s    = ParagraphStyle("B",  fontName="Helvetica",          fontSize=9.5,textColor=DARK,  leading=16, spaceAfter=5)
    small_s   = ParagraphStyle("Sm", fontName="Helvetica",          fontSize=8.5,textColor=WARM,  leading=13)
    footer_s  = ParagraphStyle("Ft", fontName="Helvetica-Oblique",  fontSize=7.5,textColor=WARM,  leading=11, alignment=TA_CENTER)

    story = []
    date_str = datetime.datetime.now().strftime("%d / %m / %Y  —  %H:%M")

    if os.path.exists(LOGO_FILE):
        try:
            logo = RLImage(LOGO_FILE, width=4*cm, height=2*cm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 0.3*cm))
        except Exception:
            pass

    story.append(Paragraph("اختبار الشخصية الخمسة الكبرى", title_s))
    story.append(Paragraph("تقرير التقييم الإكلينيكي للشخصية", sub_s))
    story.append(Paragraph(f"سري وخاص  ·  {date_str}", meta_s))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.3*cm))

    info_data = [
        [Paragraph("<b>المُقيَّم</b>", small_s), Paragraph(client_name, body_s),
         Paragraph("<b>الاختبار</b>", small_s), Paragraph("BFPT — 50 فقرة", body_s)],
        [Paragraph("<b>التاريخ</b>", small_s), Paragraph(date_str, body_s),
         Paragraph("<b>نطاق الدرجات</b>", small_s), Paragraph("0 – 40 لكل سمة", body_s)],
    ]
    it = Table(info_data, colWidths=[3*cm, 6*cm, 3.5*cm, 4.5*cm])
    it.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), LIGHT),
        ("BOX",        (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ]))
    story.append(it)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("ملخص درجات السمات", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    score_header = [
        Paragraph("<b>السمة</b>", small_s),
        Paragraph("<b>الدرجة</b>", small_s),
        Paragraph("<b>المستوى</b>", small_s),
        Paragraph("<b>المؤشر البياني (0 ──────────────── 40)</b>", small_s),
    ]
    score_rows = [score_header]
    for t in ["E", "A", "C", "N", "O"]:
        sc   = scores[t]
        lvl  = get_level(sc)
        meta = TRAIT_META[t]
        tc   = TRAIT_COLORS[t]
        bar_filled = max(0, min(28, int((sc / 40) * 28)))
        bar_empty  = 28 - bar_filled
        hex_color  = meta["color"].lstrip("#")
        bar_para = Paragraph(
            f'<font color="#{hex_color}">{"█" * bar_filled}</font>'
            f'<font color="#CCCCCC">{"░" * bar_empty}</font>',
            ParagraphStyle("BR", fontName="Courier", fontSize=8, leading=12)
        )
        score_rows.append([
            Paragraph(f"<b>{meta['name']}</b>",
                      ParagraphStyle("TN", fontName="Helvetica-Bold", fontSize=9, textColor=tc)),
            Paragraph(f"<b>{sc}/40</b>",
                      ParagraphStyle("SC", fontName="Helvetica-Bold", fontSize=9, textColor=tc, alignment=TA_CENTER)),
            Paragraph(lvl,
                      ParagraphStyle("LV", fontName="Helvetica", fontSize=9, textColor=DARK, alignment=TA_CENTER)),
            bar_para,
        ])

    st_table = Table(score_rows, colWidths=[4.5*cm, 2*cm, 2.5*cm, 8*cm])
    st_styles = [
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#EDE9E3")),
        ("BOX",        (0,0),(-1,-1), 0.5, BORDER),
        ("INNERGRID",  (0,0),(-1,-1), 0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN", (1,0),(2,-1), "CENTER"),
    ]
    for row_i, t in enumerate(["E", "A", "C", "N", "O"], start=1):
        if row_i % 2 == 0:
            st_styles.append(("BACKGROUND", (0,row_i),(-1,row_i), LIGHT))
    st_table.setStyle(TableStyle(st_styles))
    story.append(st_table)
    story.append(Spacer(1, 0.5*cm))

    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("التقرير الإكلينيكي", section_s))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    for line in report_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.18*cm))
        elif line.endswith(":") and len(line) < 60:
            story.append(Paragraph(line, section_s))
        else:
            story.append(Paragraph(line, body_s))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "هذا التقرير سري للغاية ومُعدّ للاستخدام الحصري من قِبَل المعالج المختص. لا يجوز مشاركته مع المُقيَّم أو أي طرف ثالث دون إذن كتابي صريح.",
        footer_s
    ))
    doc.build(story)

# ══════════════════════════════════════════════════════════════
#  إرسال التقرير بالبريد الإلكتروني
# ══════════════════════════════════════════════════════════════

def send_report_email(pdf_path, client_name, scores, filename):
    date_str = datetime.datetime.now().strftime("%d/%m/%Y — %H:%M")

    trait_rows = "".join(
        f"<tr><td style='padding:6px 0;color:#6B5B45;width:45%;'>{TRAIT_META[t]['name']}</td>"
        f"<td><strong style='color:{TRAIT_META[t]['color']};'>{scores[t]}/40 — {get_level(scores[t])}</strong></td></tr>"
        for t in ["E", "A", "C", "N", "O"]
    )

    msg = MIMEMultipart("mixed")
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = THERAPIST_EMAIL
    msg["Subject"] = f"[تقرير BFPT] {client_name} — {date_str}"

    body_html = f"""
    <html><body style="font-family:Georgia,serif;color:#1C1917;background:#F7F4F0;padding:24px;direction:rtl;">
      <div style="max-width:580px;margin:0 auto;background:white;border:1px solid #DDD5C8;border-radius:4px;padding:32px;">
        <h2 style="font-weight:300;font-size:22px;margin-bottom:2px;">اختبار الشخصية الخمسة الكبرى</h2>
        <p style="color:#6B5B45;font-size:12px;letter-spacing:0.05em;text-transform:uppercase;margin-top:0;">
          تقرير تقييم جديد
        </p>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <table style="width:100%;font-size:14px;border-collapse:collapse;direction:rtl;">
          <tr>
            <td style="padding:6px 0;color:#6B5B45;width:40%;">المُقيَّم</td>
            <td><strong>{client_name}</strong></td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B5B45;">التاريخ والوقت</td>
            <td>{date_str}</td>
          </tr>
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <p style="font-size:13px;color:#6B5B45;margin-bottom:8px;font-weight:bold;">درجات السمات</p>
        <table style="width:100%;font-size:13px;border-collapse:collapse;direction:rtl;">
          {trait_rows}
        </table>
        <hr style="border:none;border-top:1px solid #DDD5C8;margin:18px 0;">
        <p style="font-size:13px;line-height:1.7;">التقرير الإكلينيكي الكامل مرفق بصيغة PDF.</p>
        <p style="font-size:11px;color:#6B5B45;margin-top:20px;font-style:italic;">
          هذه الرسالة سرية ومُوجَّهة للمعالج المختص فقط.</p>
      </div>
    </body></html>"""

    msg.attach(MIMEText(body_html, "html"))
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, THERAPIST_EMAIL, msg.as_string())

# ══════════════════════════════════════════════════════════════
#  واجهة Streamlit
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="اختبار الشخصية الخمسة الكبرى",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg: #F7F4F0;
    --white: #FFFFFF;
    --deep: #1C1917;
    --warm: #6B5B45;
    --accent: #8B6F47;
    --border: #DDD5C8;
    --selected: #2D2926;
}

/* ── إخفاء عناصر Streamlit ── */
#MainMenu { visibility: hidden !important; display: none !important; }
header[data-testid="stHeader"] { visibility: hidden !important; display: none !important; }
footer { visibility: hidden !important; display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stActionButton"] { display: none !important; }
a[href*="streamlit.io"] { display: none !important; }
a[href*="share.streamlit.io"] { display: none !important; }
.viewerBadge_container__r5tak { display: none !important; }
.viewerBadge_link__qRIco { display: none !important; }
.styles_viewerBadge__CvC9N { display: none !important; }
[class*="viewerBadge"] { display: none !important; }
[class*="ProfileBadge"] { display: none !important; }
iframe[src*="streamlit.io"] { display: none !important; }
#stDecoration { display: none !important; }

/* ── وضع فاتح دائماً ── */
html, body, [data-theme="dark"], [data-theme="light"] {
    color-scheme: light only !important;
}
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg);
    color: var(--deep);
    direction: rtl;
}
.stApp { background-color: var(--bg); }
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
.stApp {
    background-color: var(--bg) !important;
    color: var(--deep) !important;
}

.page-header {
    text-align: center;
    padding: 2.5rem 0 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
    direction: rtl;
}
.page-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 400;
    letter-spacing: 0.01em;
    margin-bottom: 0.3rem;
    color: var(--deep);
}
.page-header p {
    color: var(--warm);
    font-size: 0.82rem;
    letter-spacing: 0.06em;
    font-weight: 400;
}

.question-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.5rem 1.8rem 0.5rem 1.8rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
    direction: rtl;
    text-align: right;
}
.question-card:hover { border-color: var(--accent); }

.q-number {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: var(--accent);
    margin-bottom: 0.3rem;
    font-weight: 500;
}
.q-stem {
    font-size: 0.8rem;
    color: var(--warm);
    font-style: italic;
    margin-bottom: 0.5rem;
}
.q-text {
    font-family: 'Playfair Display', serif;
    font-size: 1.08rem;
    color: var(--deep);
    margin-bottom: 0.6rem;
    line-height: 1.6;
}
.q-hint {
    font-size: 0.8rem;
    color: var(--warm);
    font-style: italic;
    background: #F7F4F0;
    border-right: 2px solid var(--accent);
    border-left: none;
    padding: 0.35rem 0.7rem;
    border-radius: 3px 0 0 3px;
    margin-bottom: 0.8rem;
    line-height: 1.6;
}

div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] > div {
    gap: 0.4rem !important;
    flex-direction: row-reverse !important;
    flex-wrap: wrap !important;
    justify-content: flex-start !important;
}
div[data-testid="stRadio"] > div > label {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 0.38rem 0.9rem !important;
    cursor: pointer !important;
    font-size: 0.82rem !important;
    color: var(--deep) !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
}
div[data-testid="stRadio"] > div > label:hover {
    border-color: var(--accent) !important;
    background: #F0EBE3 !important;
}

.progress-wrap { background: var(--border); border-radius: 2px; height: 3px; margin: 1.5rem 0 0.5rem 0; }
.progress-fill { height: 3px; border-radius: 2px; background: linear-gradient(90deg, var(--warm), var(--accent)); }

.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    border-radius: 2px !important;
    padding: 0.8rem 2.8rem !important;
    transition: background 0.2s ease !important;
}
.stButton > button[kind="primary"],
.stButton > button {
    background: var(--selected) !important;
    color: var(--bg) !important;
    border: none !important;
}
.stButton > button:hover { background: var(--warm) !important; }

.thank-you {
    text-align: center;
    padding: 5rem 2rem;
    direction: rtl;
}
.thank-you h2 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 400;
    margin-bottom: 1rem;
}
.thank-you p {
    color: var(--warm);
    font-size: 0.95rem;
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.9;
}

div[data-testid="stTextInput"] input {
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--deep) !important;
    text-align: right !important;
    direction: rtl !important;
}
</style>
""", unsafe_allow_html=True)

# ── التوجيه: إدارة أم عميل ──────────────────────────────────────
page = st.query_params.get("page", "client")

if page == "admin":
    st.markdown("""
    <div class="page-header">
        <p>بوابة المعالج</p>
        <h1>التقارير المحفوظة</h1>
    </div>""", unsafe_allow_html=True)

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pwd = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
        if st.button("دخول"):
            if pwd == st.secrets.get("ADMIN_PASSWORD", ""):
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة.")
    else:
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        files = sorted([f for f in os.listdir(reports_dir) if f.endswith(".pdf")], reverse=True)

        if not files:
            st.info("لا توجد تقارير مسجّلة حتى الآن.")
        else:
            st.markdown(f"**{len(files)} تقرير محفوظ**")
            for fname in files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📄 `{fname}`")
                with col2:
                    with open(os.path.join(reports_dir, fname), "rb") as f:
                        st.download_button("تحميل", data=f, file_name=fname,
                                           mime="application/pdf", key=fname)
        if st.button("تسجيل الخروج"):
            st.session_state.admin_auth = False
            st.rerun()

else:
    # ── واجهة المريض ──────────────────────────────────────────────
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if st.session_state.submitted:
        st.markdown("""
        <div class="thank-you">
            <h2>شكراً لك</h2>
            <p>تم تسليم إجاباتك بنجاح.<br>
            سيتواصل معك المعالج في أقرب وقت.</p>
        </div>""", unsafe_allow_html=True)
    else:
        if os.path.exists(LOGO_FILE):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(LOGO_FILE, use_container_width=True)

        st.markdown("""
        <div class="page-header">
            <p>تقييم نفسي سري</p>
            <h1>اختبار الشخصية الخمسة الكبرى</h1>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <p style="font-size:0.88rem;color:#6B5B45;text-align:center;margin-bottom:0.5rem;
                  line-height:1.9;direction:rtl;">
        اقرأ كل عبارة بعناية وحدد مدى انطباقها عليك.<br>
        ابدأ كل عبارة بـ <strong>"أنا..."</strong> وأجب بناءً على ما تشعر به في العادة.
        </p>""", unsafe_allow_html=True)

        client_name = st.text_input("اسمك (اختياري)", placeholder="الاسم أو الأحرف الأولى")
        st.markdown("<br>", unsafe_allow_html=True)

        responses = {}
        all_answered = True

        for q in BFPT_QUESTIONS:
            qid = q["id"]
            hint_html = f'<div class="q-hint">{q["hint"]}</div>' if q.get("hint") else ""
            st.markdown(f"""
            <div class="question-card">
                <div class="q-number">السؤال {qid} من 50</div>
                <div class="q-stem">أنا…</div>
                <div class="q-text">{q['text']}</div>
                {hint_html}
            </div>""", unsafe_allow_html=True)

            choice = st.radio(
                label=f"q_{qid}",
                options=list(SCALE_OPTIONS.values()),
                index=None,
                key=f"q_{qid}",
                label_visibility="collapsed",
                horizontal=True,
            )

            if choice is None:
                all_answered = False
            else:
                score_val = next(k for k, v in SCALE_OPTIONS.items() if v == choice)
                responses[qid] = score_val

        answered_count = len(responses)
        pct = int((answered_count / 50) * 100)
        st.markdown(f"""
        <div style="text-align:center;font-size:0.78rem;color:#6B5B45;
                    letter-spacing:0.05em;margin-top:1.5rem;direction:rtl;">
            {answered_count} من 50 سؤالاً تمت الإجابة عنه
        </div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{pct}%"></div>
        </div>""", unsafe_allow_html=True)

        if not all_answered and answered_count > 0:
            st.markdown("""
            <div style="background:#FFF8F0;border-right:3px solid #E07B39;border-left:none;
                        padding:1rem 1.2rem;border-radius:4px 0 0 4px;
                        font-size:0.88rem;color:#7A3D1A;margin:1rem 0;direction:rtl;text-align:right;">
                ⚠ يرجى الإجابة على جميع الأسئلة الخمسين قبل التسليم.
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="text-align:center;padding:2rem 0 3rem 0;">', unsafe_allow_html=True)
        submit = st.button("تسليم الاختبار", disabled=not all_answered)
        st.markdown('</div>', unsafe_allow_html=True)

        if submit and all_answered:
            with st.spinner("جاري تسليم إجاباتك..."):
                scores = calculate_scores(responses)
                report_text = generate_report(client_name or "غير محدد", scores, responses)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = (client_name or "مجهول").replace(" ", "_")
                filename  = f"BFPT_AR_{safe_name}_{timestamp}.pdf"
                os.makedirs("reports", exist_ok=True)
                pdf_path  = os.path.join("reports", filename)

                create_pdf_report(pdf_path, client_name or "غير محدد", scores, report_text, timestamp)

                try:
                    send_report_email(pdf_path, client_name or "غير محدد", scores, filename)
                except Exception as e:
                    st.warning(f"تم حفظ التقرير لكن فشل الإرسال بالبريد: {e}")

                st.session_state.submitted = True
                st.rerun()
