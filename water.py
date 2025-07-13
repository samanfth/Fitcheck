import logging
import os
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display
from matplotlib import font_manager
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

logging.basicConfig(level=logging.INFO)

# مراحل گفتگو
(
    SELECTING,           # انتخاب نوع محاسبه
    WEIGHT, HEIGHT,      # برای BMI
    BMR_GENDER, BMR_AGE, BMR_WEIGHT, BMR_HEIGHT,    # برای BMR
    TDEE_GENDER, TDEE_AGE, TDEE_WEIGHT, TDEE_HEIGHT, TDEE_ACTIVITY,  # برای TDEE
    WATER_WEIGHT, WATER_AGE, WATER_GENDER, BODYFAT_GENDER, BODYFAT_AGE, BODYFAT_WEIGHT, BODYFAT_HEIGHT,
) = range(19)

DIETS = {
    'underweight': 'diet_images/underweight.jpg',
    'normal': 'diet_images/normal.jpg',
    'overweight': 'diet_images/overweight.jpg',
    'obese': 'diet_images/obese.jpg',
}

FONT_PATH = "C:/Windows/Fonts/tahoma.ttf"
font_prop = font_manager.FontProperties(fname=FONT_PATH)

def plot_bmi_chart(bmi):
    label1 = get_display(arabic_reshaper.reshape('BMI شما'))
    label2 = get_display(arabic_reshaper.reshape('حد نرمال (24.9)'))
    labels = [label1, label2]
    values = [bmi, 24.9]

    colors = ['#ff9999', '#99ff99']
    plt.figure(figsize=(6, 4))
    bars = plt.bar(labels, values, color=colors)
    plt.ylim(0, max(bmi, 30) + 5)

    title_text = get_display(arabic_reshaper.reshape('مقایسه BMI شما با حد نرمال'))
    ylabel_text = get_display(arabic_reshaper.reshape('BMI'))

    plt.title(title_text, fontproperties=font_prop)
    plt.ylabel(ylabel_text, fontproperties=font_prop)

    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval + 0.5,
            round(yval, 2),
            ha='center',
            fontsize=12,
            fontproperties=font_prop
        )

    chart_path = 'bmi_chart.png'
    plt.savefig(chart_path)
    plt.close()
    return chart_path

# شروع بات و انتخاب گزینه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["BMI", "BMR", "TDEE"],
        ["آب بدن", "چربی بدن"],
        ["شروع", "پایان"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    text = (
        "سلام! 👋\n"
        "می‌تونی یکی از گزینه‌های زیر رو انتخاب کنی:\n"
        " (شاخص توده بدنی) میز ان تناسب وزن و قد BMI\n"
        " (نرخ متابولیسم پایه) - کالری مورد نیاز در حالت استراحت BMR\n"
        " (کل مصرف انرژی روزانه) - کالری مورد نیاز با توجه به فعالیت TDEE\n"
        "آب بدن - میزان آب مورد نیاز روزانه\n"
        "چربی بدن - درصد چربی بدن به روش تقریبی\n"
        "\nبرای شروع یکی رو انتخاب کن:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)
    return SELECTING

# دریافت انتخاب
async def selecting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip().upper()
    if choice == "BMI":
        await update.message.reply_text(
            "BMI:\n--------------------\n"
            "شاخص توده بدنی (Body Mass Index) معیاری برای اندازه‌گیری تناسب وزن نسبت به قد است.\n\n"
            "لطفاً وزن خودتو وارد کن (کیلوگرم):"
        )
        return WEIGHT
    elif choice == "BMR":
        await update.message.reply_text(
            "BMR:\n--------------------\n"
            "نرخ متابولیک پایه، کالری‌ای که بدنت در حالت استراحت می‌سوزونه.\n\n"
            "اول بگو جنسیتت چیه؟ (مرد / زن)"
        )
        return BMR_GENDER
    elif choice == "TDEE":
        await update.message.reply_text(
            "TDEE:\n--------------------\n"
            "کل کالری‌ای که در طول روز با توجه به فعالیت بدنی می‌سوزونی.\n\n"
            "اول بگو جنسیتت چیه؟ (مرد / زن)"
        )
        return TDEE_GENDER
    elif choice == "آب بدن":
        await update.message.reply_text(
            "محاسبه میزان آب مورد نیاز بدن:\n--------------------\n"
            "بر اساس وزن، سن و جنسیتت میزان آب روزانه رو حساب می‌کنیم.\n\n"
            "لطفاً وزن خودتو وارد کن (کیلوگرم):"
        )
        return WATER_WEIGHT
    elif choice == "چربی بدن":
        await update.message.reply_text(
            "محاسبه درصد چربی بدن (تقریبی):\n--------------------\n"
            "بر اساس جنسیت، سن، وزن و قد درصد چربی بدن تخمین زده می‌شود.\n\n"
            "لطفاً جنسیتت رو بگو (مرد / زن):"
        )
        return BODYFAT_GENDER
    elif choice == "شروع":
        return await start(update, context)
    elif choice == "پایان":
        await update.message.reply_text("بات متوقف شد. هر وقت خواستی دوباره /start رو بزن.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های بالا رو انتخاب کن.")
        return SELECTING

# -------------- BMI ----------------

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        context.user_data['weight'] = weight
        await update.message.reply_text("حالا قد خود را وارد کن (متر 📏 مثلاً 1.75):")
        return HEIGHT
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد وارد کن 😅. وزن (kg):")
        return WEIGHT

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        weight = context.user_data['weight']
        bmi = round(weight / (height ** 2), 2)

        if bmi < 18.5:
            category = 'underweight'
            status = "😕 شما کم‌وزن هستی."
            diet = (
                "✅ غذاهای مقوی‌تر بخور:\n"
                "🍚 برنج و نان کامل\n"
                "🥜 مغزها و خشکبار\n"
                "🥛 لبنیات پرچرب\n"
                "🍗 پروتئین بالا مصرف کن"
            )
        elif 18.5 <= bmi < 25:
            category = 'normal'
            status = "🎯 وزنت عالیه! 👏"
            diet = (
                "🥗 رژیم متعادل داشته باش:\n"
                "🍖 پروتئین کافی\n"
                "🥬 سبزیجات روزانه\n"
                "🍎 میوه متنوع\n"
                "💧 نوشیدن آب فراموش نشه"
            )
        elif 25 <= bmi < 30:
            category = 'overweight'
            extra = round((bmi - 24.9) * (height ** 2), 1)
            status = f"😬 شما اضافه‌وزن داری! حدوداً {extra} کیلوگرم بیشتر از نرمال 😅"
            diet = (
                "🍽️ رژیم سبک‌تری داشته باش:\n"
                "🥦 سبزیجات بیشتر بخور\n"
                "🍞 نان سبوس‌دار استفاده کن\n"
                "🚫 قند و چربی رو کم کن\n"
                "💦 آب زیاد بنوش"
            )
        else:
            category = 'obese'
            extra = round((bmi - 24.9) * (height ** 2), 1)
            status = f"🚨 شما در محدوده چاقی هستی! حدوداً {extra} کیلوگرم اضافه داری."
            diet = (
                "📉 رژیم کنترل‌شده ضروریه:\n"
                "🚫 حذف فست‌فود و نوشابه\n"
                "🍛 غذای خونگی و سالم بخور\n"
                "🥬 بشقابتو سبزتر کن\n"
                "🚶 روزانه پیاده‌روی کن"
            )

        await update.message.reply_text(f"📊 BMI شما: {bmi}\n{status}")
        await update.message.reply_text(f"🍽️ پیشنهاد تغذیه‌ای من برات:\n{diet}")

        image_path = DIETS[category]
        if os.path.exists(image_path):
            with open(image_path, 'rb') as img:
                await update.message.reply_photo(img)
        else:
            await update.message.reply_text("📷 تصویر گرافیکی مربوط به وضعیتت هنوز بارگذاری نشده.")

        chart_file = plot_bmi_chart(bmi)
        with open(chart_file, 'rb') as chart:
            await update.message.reply_photo(chart)

        await update.message.reply_text("برای شروع مجدد، هر وقت خواستی /start رو بزن.")
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("قدت رو به صورت عددی وارد کن (مثلاً 1.75):")
        return HEIGHT

# -------------- BMR ----------------

async def bmr_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.lower()
    if gender not in ['مرد', 'زن']:
        await update.message.reply_text("فقط بنویس مرد یا زن:")
        return BMR_GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("چند سالته؟")
    return BMR_AGE

async def bmr_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        context.user_data['age'] = age
        await update.message.reply_text("وزنت چند کیلوگرمه؟")
        return BMR_WEIGHT
    except ValueError:
        await update.message.reply_text("فقط عدد وارد کن. سنت چند ساله؟")
        return BMR_AGE

async def bmr_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        context.user_data['weight'] = weight
        await update.message.reply_text("قدت چنده؟ (به سانتی‌متر)")
        return BMR_HEIGHT
    except ValueError:
        await update.message.reply_text("عدد بفرست لطفاً. وزنت چند کیلوگرمه؟")
        return BMR_WEIGHT

async def bmr_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        gender = context.user_data['gender']
        age = context.user_data['age']
        weight = context.user_data['weight']

        if gender == 'مرد':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        await update.message.reply_text(
            "BMR\n------------------\n"
            f"سوخت پایه‌ی بدنت حدود {round(bmr)} کالری در روزه."
        )
        await update.message.reply_text("برای شروع مجدد، هر وقت خواستی /start رو بزن.")
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("قد رو عددی وارد کن (مثلاً 175):")
        return BMR_HEIGHT

# -------------- TDEE ----------------

async def tdee_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.lower()
    if gender not in ['مرد', 'زن']:
        await update.message.reply_text("فقط بنویس مرد یا زن:")
        return TDEE_GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("چند سالته؟")
    return TDEE_AGE

async def tdee_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        context.user_data['age'] = age
        await update.message.reply_text("وزنت چند کیلوگرمه؟")
        return TDEE_WEIGHT
    except ValueError:
        await update.message.reply_text("فقط عدد وارد کن. سنت چند ساله؟")
        return TDEE_AGE

async def tdee_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        context.user_data['weight'] = weight
        await update.message.reply_text("قدت چنده؟ (به سانتی‌متر)")
        return TDEE_HEIGHT
    except ValueError:
        await update.message.reply_text("عدد بفرست لطفاً. وزنت چند کیلوگرمه؟")
        return TDEE_WEIGHT

async def tdee_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        context.user_data['height'] = height
        await update.message.reply_text(
            "سطح فعالیت بدنی خودتو انتخاب کن:\n"
            "1. خیلی کم (بدون ورزش)\n"
            "2. کم (ورزش سبک 1-3 روز در هفته)\n"
            "3. متوسط (ورزش متوسط 3-5 روز در هفته)\n"
            "4. زیاد (ورزش زیاد 6-7 روز در هفته)\n"
            "5. خیلی زیاد (کار سخت فیزیکی یا ورزش شدید)"
        )
        return TDEE_ACTIVITY
    except ValueError:
        await update.message.reply_text("قد رو عددی وارد کن (مثلاً 175):")
        return TDEE_HEIGHT

async def tdee_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activity_level = update.message.text.strip()
    activity_multipliers = {
        '1': 1.2,
        '2': 1.375,
        '3': 1.55,
        '4': 1.725,
        '5': 1.9
    }
    if activity_level not in activity_multipliers:
        await update.message.reply_text("لطفاً عدد بین 1 تا 5 وارد کن:")
        return TDEE_ACTIVITY

    gender = context.user_data['gender']
    age = context.user_data['age']
    weight = context.user_data['weight']
    height = context.user_data['height']
    activity_factor = activity_multipliers[activity_level]

    if gender == 'مرد':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    tdee = round(bmr * activity_factor)

    await update.message.reply_text(
        "TDEE\n------------------\n"
        f"کل کالری که با توجه به فعالیت روزانه می‌سوزونی حدود {tdee} کالریه."
    )
    await update.message.reply_text("برای شروع مجدد، هر وقت خواستی /start رو بزن.")
    return ConversationHandler.END

# -------------- WATER NEED ----------------

async def water_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        context.user_data['weight'] = weight
        await update.message.reply_text("چند سالته؟")
        return WATER_AGE
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد وارد کن 😅. وزن (kg):")
        return WATER_WEIGHT

async def water_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        context.user_data['age'] = age
        await update.message.reply_text("جنسیت چیه؟ (مرد / زن)")
        return WATER_GENDER
    except ValueError:
        await update.message.reply_text("لطفاً فقط عدد وارد کن 😅. سن:")
        return WATER_AGE

async def water_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.lower()
    if gender not in ['مرد', 'زن']:
        await update.message.reply_text("فقط بنویس مرد یا زن:")
        return WATER_GENDER
    context.user_data['gender'] = gender

    weight = context.user_data['weight']
    age = context.user_data['age']

    # محاسبه مقدار آب مورد نیاز بر حسب لیتر
    base_water = weight * 0.035  # پایه بر حسب لیتر
    if age < 30:
        if gender == 'مرد':
            water = base_water + 0.5
        else:
            water = base_water + 0.3
    elif 30 <= age < 55:
        if gender == 'مرد':
            water = base_water + 0.3
        else:
            water = base_water + 0.2
    else:
        water = base_water  # برای افراد بالای 55 سال

    water = round(water, 2)

    await update.message.reply_text(
        "آب بدن\n------------------\n"
        f"میزان آب مورد نیاز روزانه شما تقریباً {water} لیتر است."
    )
    await update.message.reply_text("برای شروع مجدد، هر وقت خواستی /start رو بزن.")
    return ConversationHandler.END

# -------------- BODY FAT ----------------

async def bodyfat_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.lower()
    if gender not in ['مرد', 'زن']:
        await update.message.reply_text("فقط بنویس مرد یا زن:")
        return BODYFAT_GENDER
    context.user_data['gender'] = gender
    await update.message.reply_text("چند سالته؟")
    return BODYFAT_AGE

async def bodyfat_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        context.user_data['age'] = age
        await update.message.reply_text("وزنت چند کیلوگرمه؟")
        return BODYFAT_WEIGHT
    except ValueError:
        await update.message.reply_text("فقط عدد وارد کن. سنت چند ساله؟")
        return BODYFAT_AGE

async def bodyfat_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        context.user_data['weight'] = weight
        await update.message.reply_text("قدت چنده؟ (متر مثلاً 1.75)")
        return BODYFAT_HEIGHT
    except ValueError:
        await update.message.reply_text("عدد بفرست لطفاً. وزنت چند کیلوگرمه؟")
        return BODYFAT_WEIGHT

async def bodyfat_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        gender = context.user_data['gender']
        age = context.user_data['age']
        weight = context.user_data['weight']

        height_cm = height * 100  # متر به سانتی‌متر تبدیل می‌کنیم

        # فرمول نسبتا ساده تخمین درصد چربی بدن
        if gender == 'مرد':
            body_fat = 1.20 * (weight / (height ** 2)) + 0.23 * age - 16.2
        else:
            body_fat = 1.20 * (weight / (height ** 2)) + 0.23 * age - 5.4

        body_fat = round(body_fat, 2)
        await update.message.reply_text(
            "چربی بدن\n------------------\n"
            f"درصد تقریبی چربی بدن شما {body_fat}٪ است."
        )
        await update.message.reply_text("برای شروع مجدد، هر وقت خواستی /start رو بزن.")
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("قد رو عددی وارد کن (مثلاً 1.75):")
        return BODYFAT_HEIGHT

# لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد. هر وقت خواستی /start رو بزن.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    TOKEN = "7866812254:AAG7_KoXPJ2BPSjv3VWImThw7o1nuD9v06A"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^(BMI|BMR|TDEE|آب بدن|چربی بدن|شروع|پایان)$'), selecting)],
        states={
            SELECTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, selecting)],

            # BMI
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],

            # BMR
            BMR_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmr_gender)],
            BMR_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmr_age)],
            BMR_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmr_weight)],
            BMR_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmr_height)],

            # TDEE
            TDEE_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tdee_gender)],
            TDEE_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tdee_age)],
            TDEE_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tdee_weight)],
            TDEE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tdee_height)],
            TDEE_ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, tdee_activity)],

            # Water
            WATER_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, water_weight)],
            WATER_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, water_age)],
            WATER_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, water_gender)],

            # Body Fat
            BODYFAT_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bodyfat_gender)],
            BODYFAT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bodyfat_age)],
            BODYFAT_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bodyfat_weight)],
            BODYFAT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bodyfat_height)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    print("🤖 ربات در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
