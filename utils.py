import re
import pandas as pd

CRITICAL_WORDS_AR = [
    "تسمم", "صراصير", "حشرات", "شعر", "عفن", "فاسد", "منتهي", "إسهال",
    "حساسية", "تلوث", "غش", "نصب", "سرقة", "ذباب", "فأر", "صرصور",
]

CRITICAL_WORDS_EN = [
    "food poisoning", "cockroach", "insects", "hair", "mold", "expired",
    "diarrhea", "allergy", "contamination", "fraud", "fly", "rat", "mouse",
    "vomit", "sick", "hospital", "health violation",
]

CRITICAL_WORDS = CRITICAL_WORDS_AR + CRITICAL_WORDS_EN

RESTAURANT_NEGATIVE_KEYWORDS = {
    "ar": [
        "بارد", "بطيء", "غالي", "قذر", "نيء", "مالح", "صغير", "زحمة",
        "سيء", "مقرف", "رديء", "ناشف", "محروق", "دهني", "قديم", "متأخر",
        "وسخ", "غير نظيف", "بايخ", "حار جداً", "بدون طعم", "مالح زيادة",
    ],
    "en": [
        "cold", "slow", "expensive", "dirty", "raw", "salty", "small", "crowded",
        "bad", "disgusting", "poor", "dry", "burnt", "greasy", "old", "late",
        "filthy", "tasteless", "overcooked", "undercooked", "overpriced", "rude",
        "wait", "waiting", "noisy", "stale", "bland", "unfriendly",
    ],
}

RESTAURANT_POSITIVE_KEYWORDS = {
    "ar": [
        "لذيذ", "طازج", "نظيف", "سريع", "ممتاز", "رائع", "كريم", "جميل",
        "أجواء", "مرتب", "لطيف", "مميز", "فاخر", "هادئ", "منظم", "دافئ",
        "طيب", "شهي", "حلو", "أنيق", "مبدع", "متنوع", "معقول", "قيمة",
    ],
    "en": [
        "delicious", "fresh", "clean", "fast", "excellent", "amazing", "generous",
        "beautiful", "ambiance", "organized", "nice", "outstanding", "luxury",
        "quiet", "warm", "friendly", "tasty", "yummy", "cozy", "creative",
        "diverse", "reasonable", "value", "great", "wonderful", "perfect",
        "attentive", "professional", "welcoming",
    ],
}

RESTAURANT_RECOMMENDATION_RULES = {
    "ar": {
        "بارد": "التأكد من تقديم الطعام ساخناً وطازجاً",
        "بطيء": "تحسين سرعة الخدمة وتقليل وقت الانتظار",
        "غالي": "مراجعة الأسعار لتتناسب مع جودة الطعام",
        "قذر": "تعزيز معايير النظافة والصيانة الدورية",
        "نيء": "ضبط مستوى طهي الطعام حسب المعايير",
        "مالح": "ضبط كمية الملح والبهارات في الأطباق",
        "زحمة": "تحسين إدارة الحجوزات والطاولات",
        "سيء": "مراجعة شاملة لجودة الطعام والخدمة",
        "محروق": "تدريب الطهاة على ضبط درجات الحرارة",
        "متأخر": "تحسين نظام الطلبات وسرعة التوصيل",
    },
    "en": {
        "cold": "Ensure food is served hot and fresh",
        "slow": "Improve service speed and reduce wait times",
        "expensive": "Review pricing to match food quality",
        "dirty": "Enhance cleanliness standards and regular maintenance",
        "raw": "Adjust food cooking levels to standards",
        "salty": "Adjust salt and seasoning levels in dishes",
        "crowded": "Improve reservation and table management",
        "bad": "Conduct a comprehensive review of food and service quality",
        "burnt": "Train chefs on proper temperature control",
        "rude": "Invest in customer service training for staff",
        "wait": "Optimize order processing and delivery speed",
        "overpriced": "Align menu pricing with portion sizes and quality",
    },
}

TRANSLATIONS = {
    "app_title": {"ar": "ReviewIQ Demo — محلل تقييمات المطاعم", "en": "ReviewIQ Demo — Restaurant Review Analyzer"},
    "page_collection": {"ar": "جمع التقييمات", "en": "Collect Reviews"},
    "page_analysis": {"ar": "التحليل", "en": "Analysis"},
    "language": {"ar": "اللغة", "en": "Language"},
    "select_source": {"ar": "اختر المصدر", "en": "Select Source"},
    "google_maps": {"ar": "Google Maps", "en": "Google Maps"},
    "custom_csv": {"ar": "ملف مخصص (CSV/Excel)", "en": "Custom File (CSV/Excel)"},
    "tripadvisor_csv": {"ar": "TripAdvisor CSV", "en": "TripAdvisor CSV"},
    "fetch_reviews": {"ar": "سحب التقييمات", "en": "Fetch Reviews"},
    "fetching": {"ar": "جارِ سحب التقييمات...", "en": "Fetching reviews..."},
    "reviews_fetched": {"ar": "تم سحب {count} تقييم بنجاح", "en": "Successfully fetched {count} reviews"},
    "no_reviews": {"ar": "لم يتم العثور على تقييمات", "en": "No reviews found"},
    "error_fetch": {"ar": "خطأ في سحب التقييمات: {error}", "en": "Error fetching reviews: {error}"},
    "preview": {"ar": "معاينة التقييمات", "en": "Reviews Preview"},
    "critical_alert": {"ar": "⚠️ {count} تقييمات تحتوي على كلمات حرجة", "en": "⚠️ {count} reviews contain critical keywords"},
    "google_api_key": {"ar": "مفتاح Google Places API", "en": "Google Places API Key"},
    "place_name": {"ar": "اسم المطعم أو الكافيه", "en": "Restaurant or Café Name"},
    "place_name_placeholder": {"ar": "مثال: كافيه كيان جدة", "en": "e.g., Kayan Café Jeddah"},
    "analyze": {"ar": "تحليل التقييمات", "en": "Analyze Reviews"},
    "analyzing": {"ar": "جارِ التحليل...", "en": "Analyzing..."},
    "analysis_complete": {"ar": "اكتمل التحليل بنجاح", "en": "Analysis completed successfully"},
    "sentiment_dist": {"ar": "توزيع المشاعر", "en": "Sentiment Distribution"},
    "positive": {"ar": "إيجابي", "en": "Positive"},
    "negative": {"ar": "سلبي", "en": "Negative"},
    "neutral": {"ar": "محايد", "en": "Neutral"},
    "top_complaints": {"ar": "أكثر الشكاوى تكراراً", "en": "Top Complaints"},
    "top_praises": {"ar": "أكثر الإشادات تكراراً", "en": "Top Praises"},
    "recommendations": {"ar": "توصيات التحسين", "en": "Recommendations"},
    "executive_summary": {"ar": "الملخص التنفيذي", "en": "Executive Summary"},
    "keyword_sentiment": {"ar": "خريطة مشاعر الكلمات", "en": "Keyword Sentiment Map"},
    "reputation_score": {"ar": "نقاط السمعة", "en": "Reputation Score"},
    "total_reviews": {"ar": "إجمالي التقييمات", "en": "Total Reviews"},
    "avg_rating": {"ar": "متوسط التقييم", "en": "Avg Rating"},
    "negative_pct": {"ar": "نسبة السلبي", "en": "Negative %"},
    "response_rate": {"ar": "معدل الرد", "en": "Response Rate"},
    "filters": {"ar": "فلترة ذكية", "en": "Smart Filters"},
    "filter_rating": {"ar": "فلتر بالنجوم", "en": "Filter by Rating"},
    "filter_date": {"ar": "فلتر بالتاريخ", "en": "Filter by Date"},
    "filter_keyword": {"ar": "بحث بكلمة", "en": "Search by Keyword"},
    "no_data": {"ar": "لا توجد بيانات — اجمع التقييمات أولاً", "en": "No data — collect reviews first"},
    "upload_csv": {"ar": "ارفع ملف CSV", "en": "Upload CSV File"},
    "upload_file": {"ar": "ارفع ملف CSV أو Excel", "en": "Upload CSV or Excel File"},
    "csv_instructions_gmaps": {
        "ar": "**كيف تنزّل تقييمات Google Maps:**\n1. افتح Google Maps وابحث عن المطعم\n2. اضغط على التقييمات\n3. استخدم إضافة متصفح لتصدير التقييمات كـ CSV",
        "en": "**How to download Google Maps reviews:**\n1. Open Google Maps and search for the restaurant\n2. Click on reviews\n3. Use a browser extension to export reviews as CSV"
    },
    "csv_instructions_tripadvisor": {
        "ar": "**كيف تنزّل تقييمات TripAdvisor:**\n1. افتح صفحة المطعم على TripAdvisor\n2. استخدم إضافة متصفح لتصدير التقييمات كـ CSV",
        "en": "**How to download TripAdvisor reviews:**\n1. Open the restaurant page on TripAdvisor\n2. Use a browser extension to export reviews as CSV"
    },
    "gmaps_option_api": {"ar": "عبر API", "en": "Via API"},
    "gmaps_option_csv": {"ar": "رفع CSV", "en": "Upload CSV"},
    "complaint": {"ar": "شكوى", "en": "Complaint"},
    "praise": {"ar": "إشادة", "en": "Praise"},
    "count": {"ar": "العدد", "en": "Count"},
    "error_analysis": {"ar": "خطأ في التحليل: {error}", "en": "Analysis error: {error}"},
    "full_version_only": {"ar": "هذه الميزة متوفرة في النسخة الكاملة", "en": "This feature is available in the full version"},
    "critical_reviews_urgent": {"ar": "تقييمات تحتاج رد فوري", "en": "Reviews Requiring Immediate Response"},
    "critical_reason": {"ar": "السبب: تم رصد كلمة «{word}»", "en": "Reason: detected keyword \"{word}\""},
}


def get_text(key, lang="ar"):
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("en", key))


def detect_review_column(df):
    candidates = [
        "review_text", "body", "content", "text", "review", "comment",
        "reviews", "feedback", "description", "message",
        "تقييم", "نص التقييم", "التعليق", "المراجعة",
    ]
    for col in candidates:
        for df_col in df.columns:
            if df_col.strip().lower() == col.lower():
                return df_col
    for col in df.columns:
        if df[col].dtype == "object":
            avg_len = df[col].astype(str).str.len().mean()
            if avg_len > 20:
                return col
    return None


def detect_date_column(df):
    candidates = ["date", "at", "timestamp", "time", "created_at", "التاريخ", "تاريخ"]
    for col in candidates:
        for df_col in df.columns:
            if df_col.strip().lower() == col.lower():
                return df_col
    for col in df.columns:
        try:
            pd.to_datetime(df[col].head(10), errors="raise")
            return col
        except Exception:
            continue
    return None


def detect_rating_column(df):
    candidates = ["score", "rating", "stars", "rate", "التقييم", "النجوم"]
    for col in candidates:
        for df_col in df.columns:
            if df_col.strip().lower() == col.lower():
                return df_col
    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            if df[col].min() >= 0 and df[col].max() <= 5:
                return col
    return None


def detect_reply_column(df):
    candidates = ["replyContent", "reply", "response", "owner_reply", "الرد", "رد"]
    for col in candidates:
        for df_col in df.columns:
            if df_col.strip().lower() == col.lower():
                return df_col
    return None


def find_critical_words(text):
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    found = []
    for word in CRITICAL_WORDS:
        if word.lower() in text_lower:
            found.append(word)
    return found


def count_critical_reviews(df, review_col):
    if review_col is None:
        return 0, []
    critical_indices = []
    for idx, row in df.iterrows():
        if find_critical_words(str(row[review_col])):
            critical_indices.append(idx)
    return len(critical_indices), critical_indices


def calculate_reputation_score(df, analysis, review_col):
    rating_col = detect_rating_column(df)
    avg_rating = df[rating_col].mean() if rating_col else 3.0
    rating_component = (avg_rating / 5.0) * 40

    sentiments = analysis.get("sentiments", [])
    total_sents = len(sentiments)
    if total_sents > 0:
        pos_count = sum(1 for s in sentiments if s in ("Positive", "إيجابي"))
        positive_pct = pos_count / total_sents
    else:
        positive_pct = 0.5
    positive_component = positive_pct * 35

    reply_col = detect_reply_column(df)
    if reply_col is not None:
        has_reply = df[reply_col].astype(str).str.strip().replace("", None).replace("nan", None).replace("None", None)
        replied = has_reply.notna().sum()
        resp_rate = replied / len(df) if len(df) > 0 else 0
    else:
        resp_rate = 0
    response_component = resp_rate * 15

    critical_count, _ = count_critical_reviews(df, review_col)
    no_critical = 1.0 if critical_count == 0 else max(0, 1.0 - (critical_count / len(df)))
    critical_component = no_critical * 10

    score = rating_component + positive_component + response_component + critical_component
    return round(min(100, max(0, score)), 1)
