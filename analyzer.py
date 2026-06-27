from collections import Counter
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from utils import RESTAURANT_NEGATIVE_KEYWORDS, RESTAURANT_POSITIVE_KEYWORDS, RESTAURANT_RECOMMENDATION_RULES


def analyze_basic(reviews_list):
    vader = SentimentIntensityAnalyzer()
    sentiments = []
    neg_keywords_found = Counter()
    pos_keywords_found = Counter()

    all_neg_words = RESTAURANT_NEGATIVE_KEYWORDS["ar"] + RESTAURANT_NEGATIVE_KEYWORDS["en"]
    all_pos_words = RESTAURANT_POSITIVE_KEYWORDS["ar"] + RESTAURANT_POSITIVE_KEYWORDS["en"]

    for rev in reviews_list:
        if not rev or not isinstance(rev, str):
            sentiments.append("Neutral")
            continue

        vader_scores = vader.polarity_scores(rev)
        compound = vader_scores["compound"]

        try:
            blob_polarity = TextBlob(rev).sentiment.polarity
        except Exception:
            blob_polarity = 0

        avg_score = (compound + blob_polarity) / 2

        if avg_score > 0.1:
            sentiments.append("Positive")
        elif avg_score < -0.1:
            sentiments.append("Negative")
        else:
            sentiments.append("Neutral")

        rev_lower = rev.lower()
        for word in all_neg_words:
            if word.lower() in rev_lower:
                neg_keywords_found[word] += 1
        for word in all_pos_words:
            if word.lower() in rev_lower:
                pos_keywords_found[word] += 1

    complaints = [{"text": w, "count": c} for w, c in neg_keywords_found.most_common(5)]
    praises = [{"text": w, "count": c} for w, c in pos_keywords_found.most_common(5)]

    recommendations = []
    all_rules = {**RESTAURANT_RECOMMENDATION_RULES.get("ar", {}), **RESTAURANT_RECOMMENDATION_RULES.get("en", {})}
    for word, _ in neg_keywords_found.most_common(5):
        word_lower = word.lower()
        if word_lower in all_rules:
            recommendations.append(all_rules[word_lower])

    if not recommendations:
        total = len(sentiments)
        neg_count = sentiments.count("Negative")
        if total > 0 and neg_count / total > 0.3:
            recommendations.append(
                "مراجعة شاملة لجودة الخدمة والطعام" if any(w in "".join(reviews_list) for w in RESTAURANT_NEGATIVE_KEYWORDS["ar"])
                else "Conduct a comprehensive review of service and food quality"
            )

    total = len(sentiments)
    pos = sentiments.count("Positive")
    neg = sentiments.count("Negative")
    neu = sentiments.count("Neutral")

    if total > 0:
        has_arabic = any(
            any("؀" <= c <= "ۿ" for c in rev)
            for rev in reviews_list[:5] if isinstance(rev, str)
        )
        if has_arabic:
            summary = (
                f"تم تحليل {total} تقييم. "
                f"النتائج: {pos} إيجابي ({round(pos/total*100, 1)}%)، "
                f"{neg} سلبي ({round(neg/total*100, 1)}%)، "
                f"{neu} محايد ({round(neu/total*100, 1)}%). "
            )
            if complaints:
                summary += f"أبرز الشكاوى: {', '.join(c['text'] for c in complaints[:3])}."
        else:
            summary = (
                f"Analyzed {total} reviews. "
                f"Results: {pos} positive ({round(pos/total*100, 1)}%), "
                f"{neg} negative ({round(neg/total*100, 1)}%), "
                f"{neu} neutral ({round(neu/total*100, 1)}%). "
            )
            if complaints:
                summary += f"Top complaints: {', '.join(c['text'] for c in complaints[:3])}."
    else:
        summary = ""

    return {
        "sentiments": sentiments,
        "complaints": complaints,
        "praises": praises,
        "recommendations": recommendations,
        "summary": summary,
    }


def calculate_response_rate(df):
    reply_cols = ["replyContent", "reply", "response", "owner_reply", "الرد", "رد"]
    reply_col = None
    for col in reply_cols:
        for df_col in df.columns:
            if df_col.strip().lower() == col.lower():
                reply_col = df_col
                break
        if reply_col:
            break

    if reply_col is None:
        return None

    has_reply = df[reply_col].astype(str).str.strip().replace("", None).replace("nan", None).replace("None", None)
    replied = has_reply.notna().sum()
    total = len(df)
    if total == 0:
        return 0.0
    return round((replied / total) * 100, 1)
