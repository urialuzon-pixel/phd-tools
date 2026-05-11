const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, ExternalHyperlink, HeadingLevel,
  BorderStyle, WidthType, ShadingType
} = require('docx');
const fs = require('fs');

const bullets = {
  config: [{
    reference: "bullets",
    levels: [{
      level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } }
    }]
  }]
};

function h1(text) {
  return new Paragraph({
    text, heading: HeadingLevel.HEADING_1,
    spacing: { before: 480, after: 200 },
    bidirectional: true
  });
}
function h2(text) {
  return new Paragraph({
    text, heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 120 },
    bidirectional: true
  });
}
function p(runs) {
  const children = typeof runs === 'string'
    ? [new TextRun({ text: runs, size: 24 })]
    : runs;
  return new Paragraph({
    children,
    spacing: { before: 100, after: 100 },
    alignment: AlignmentType.RIGHT,
    bidirectional: true
  });
}
function bullet(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 24 })],
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 },
    alignment: AlignmentType.RIGHT,
    bidirectional: true
  });
}
function run(text, opts = {}) {
  return new TextRun({ text, size: 24, ...opts });
}
function link(text, url) {
  return new ExternalHyperlink({
    link: url,
    children: [new TextRun({ text, style: "Hyperlink", size: 22 })]
  });
}
function bibEntry(authors, year, title, journal, url) {
  return new Paragraph({
    children: [
      new TextRun({ text: `${authors} (${year}). ${title}. `, size: 22 }),
      new TextRun({ text: journal + '. ', size: 22, italics: true }),
      new ExternalHyperlink({
        link: url,
        children: [new TextRun({ text: "קישור ל-Consensus", style: "Hyperlink", size: 22 })]
      })
    ],
    spacing: { before: 60, after: 60 },
    alignment: AlignmentType.RIGHT,
    bidirectional: true,
    indent: { left: 360, hanging: 360 }
  });
}
function tableRowHe(cells, isHeader) {
  return new TableRow({
    children: cells.map((c, i) => new TableCell({
      children: [new Paragraph({
        children: [new TextRun({ text: c, bold: isHeader, size: 20 })],
        spacing: { before: 60, after: 60 },
        alignment: AlignmentType.RIGHT,
        bidirectional: true
      })],
      shading: isHeader
        ? { type: ShadingType.CLEAR, fill: "1F4E79", color: "FFFFFF" }
        : undefined,
      width: i === 0
        ? { size: 18, type: WidthType.PERCENTAGE }
        : i === 1
          ? { size: 50, type: WidthType.PERCENTAGE }
          : { size: 32, type: WidthType.PERCENTAGE }
    }))
  });
}

const doc = new Document({
  numbering: bullets,
  styles: { default: { document: { run: { font: "David", size: 24 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1418, right: 1418, bottom: 1418, left: 1418 }
      }
    },
    children: [

      // כותרת
      new Paragraph({
        children: [new TextRun({ text: "הצעת מחקר לדוקטורט", bold: true, size: 28, color: "1F4E79" })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        bidirectional: true
      }),
      new Paragraph({
        children: [new TextRun({ text: "אל-עונשיות גיאופוליטית ופעילות כרייה:", bold: true, size: 34 })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
        bidirectional: true
      }),
      new Paragraph({
        children: [new TextRun({ text: "מסגרת היברידית של פיזיקה ולמידת מכונה לזיהוי חריגות כרייה בשטחים סכסוכיים", bold: true, size: 28 })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 60 },
        bidirectional: true
      }),
      new Paragraph({
        children: [new TextRun({ text: "טיוטה להגשה פנימית", size: 22, italics: true, color: "666666" })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 600 },
        bidirectional: true
      }),

      // פרק 1
      h1("1. רקע ומוטיבציה"),
      p([
        run("הצומת שבין ריבונות טריטוריאלית לבין כריית משאבי טבע מוכר מזמן כאחד הגורמים המרכזיים לסכסוכים. כאשר סמכות המדינה שנויה במחלוקת או נעדרת — כפי שקורה באזורי גבול במחלוקת, אזורי חלוקה עובדתיים, ואזורי שטח הפקר לאחר קונפליקט — מנגנוני הממשל הרגילים המגבילים פעילות כרייה קורסים. קונפליקטים נוטים לרוקן שטחים מאוכלוסייתם: תושבים נמלטים, כוחות אכיפה נסוגים, ומנגנוני הרישוי, הפיקוח והתביעה הפסיקו לתפקד. מה שנותר הוא שטח עשיר במשאבים ללא כל התנגדות לכניסה. "),
        run("למבין ומייפרואידט (Lambin & Meyfroidt, 2011)", { bold: true }),
        run(" הוכיחו, במאמר מכונן ב-PNAS עם 2,880 ציטוטים, שלחץ ממשלתי באזור אחד מעביר באופן שיטתי פעילות כרייה לאזורים בעלי ממשל חלש יותר — מנגנון עקירה הפועל בכריית יערות, כרייה ושינוי ייעוד קרקע ברחבי העולם. שטחים סכסוכיים ממוקמים בקצה הקיצוני של מדרגת הממשל הזו.")
      ]),
      p([
        run("ספרות תעשיות הכרייה מאשרת את הדינמיקה הזו. "),
        run("בבינגטון ועמיתים (Bebbington et al., 2011)", { bold: true }),
        run(", שניתחו שטחים אנדיים-אמזוניים, תיעדו את ההתכנסות של משטרים שונים לכיוון הרחבה אגרסיבית של כרייה — מונעת על ידי דינמיקת \"קללת המשאבים\", לחץ פיסקלי, והעדר עירור מקומי אפקטיבי. "),
        run("פרם ועמיתים (Prem et al., 2020)", { bold: true }),
        run(", תוך שימוש בנתוני לוויין על כריית יערות ואסטרטגיית זיהוי הפרשי-בהפרשים (DiD), הראו שסיום הקונפליקט עם FARC בקולומביה גרם לעלייה ניתנת למדידה בכריית יערות באזורים שבהם קיבולת המדינה הייתה חלשה. מחקרים אלה מבססים את הסדירות האמפירית: ואקום ממשלי מנבא כרייה, וקונפליקט יוצר ואקום ממשלי.")
      ]),
      p([
        run("חישת-מרחק שינתה את הניטור של הפרעות קרקע. "),
        run("גאלווי ועמיתים (Gallwey et al., 2020)", { bold: true }),
        run(", שיישמו רשת נוירונים קונבולוציונית על תצלומי לוויין Sentinel-2 בגאנה, השיגו זיהוי כרייה זעירה-ואומנותית (ASM) עם פחות מ-8% שגיאה על פני שישה מיליון הקטר — וכן הדגימו תגובה מדידה להתערבות ממשל מ-2017. "),
        run("בלניוק ועמיתים (Balaniuk et al., 2020)", { bold: true }),
        run(" זיהו 263 מכרות לא-רשומים בברזיל באמצעות אותה פלטפורמת לוויין ואלגוריתמי למידה עמוקה. שני המחקרים מאשרים שכרייה הבלתי נראית לאכיפה המשפטית נראית מהחלל. הפער הקריטי בספרות זו הוא כפול: ראשית, שיטות הזיהוי הקיימות מתייחסות לכרייה כבעיית סיווג — לא כחריגה ביחס לקו בסיס סביבתי-פיזיקלי מכויל; שנית, אף מחקר אינו כולל הקשר גיאופוליטי — מצב סכסוך, איכות ממשל, עצימות קונפליקט — כמשתנים מנבאים.")
      ]),
      p([
        run("למידת מכונה מונחית-פיזיקה (Physics-Guided ML) התבססה כפרדיגמה לניטור סביבתי. "),
        run("וילארד ועמיתים (Willard et al., 2020)", { bold: true }),
        run(", ב-ACM Computing Surveys עם 490 ציטוטים, מיפו את מרחב העיצוב של שיטות לשילוב מודלים פיזיקליים עם ML — כולל תיקון שגיאות שיוריות (delta learning), הארכיטקטורה הרלוונטית ביותר למחקר זה. "),
        run("שן ועמיתים (Shen et al., 2023)", { bold: true }),
        run(", ב-Nature Reviews, הוכיחו שמידול דיפרנציאלי — חיבור מודלי פיזיקה למבני רשתות נוירונים — מניב הכללה טובה יותר ממידת מכונה טהורה בתנאי מחסור נתונים. זה קריטי לאגנים סכסוכיים, שבהם נתוני מד-מים עשויים להיות בלתי-נגישים, מזויפים, או מנוע כחלק מהתחרות הגיאופוליטית עצמה. "),
        run("לו ועמיתים (Lu et al., 2021)", { bold: true }),
        run(" אימתו LSTM בייסיאני מונחה-פיזיקה לחיזוי ספיקה באגנים ממועטי-נתונים, עם יעילות Nash-Sutcliffe מעל 0.8 — הזמינות הריאלית של נתונים באזורי סכסוך רבים.")
      ]),
      p([
        run("מחקר זה עוסק בהתכנסות שלוש ספרויות אלה. "),
        run("התצפית הליבית היא שדיפופולציה הנגרמת מסכסוך יוצרת חתימה סביבתית ייחודית:"),
        run(" היא מדכאת את רעש הרקע האנתרופוגני (חקלאות, בנייה, ישובים) תוך שהיא משאירה את השטח נגיש לשחקנים הפועלים מחוץ לכל מסגרת ממשל. זה יוצר סביבה נוחה לזיהוי — המודל הפיזיקלי מצפה לעכירות נמוכה בשל פעילות אנושית מדוכאת; כל עודף נצפה ניתן לייחוס להפרעה פעילה, ככל הנראה כרייה. המחקר מציע לאופרציונלז את ההיגיון הזה דרך צינור בן שישה שלבים.")
      ]),

      // פרק 2
      h1("2. שאלות מחקר"),
      p("המחקר מובנה סביב שאלה ראשית אחת ושלוש שאלות משנה הנגזרות מהפערים שזוהו בספרות:"),
      new Paragraph({ spacing: { before: 160, after: 80 }, bidirectional: true }),
      p([run("שאלת המחקר הראשית:", { bold: true })]),
      p([
        run("RQ0: ", { bold: true }),
        run("האם תנאי אל-עונשיות גיאופוליטית — המוגדרים כקרבה לסכסוכי ריבונות, גירעוני ממשל, ועצימות קונפליקט — מנבאים שיורי עכירות חריגים (ריכוז חלקיקים מרחביים שנצפה דרך לוויין פחות הצפוי מהמודל הפיזיקלי) באגני מים סכסוכיים, ואם הסלמת סכסוך מגבירה שיורים אלה מעל מה שמשתנים סביבתיים בלבד יכולים להסביר?")
      ]),
      new Paragraph({ spacing: { before: 120, after: 60 }, bidirectional: true }),
      p([run("שאלות משנה:", { bold: true })]),
      p([
        run("RQ1: ", { bold: true }),
        run("האם מסגרת היברידית של פיזיקה-ML — קו בסיס SWAT בשילוב עם מנבא שיורים XGBoost/LSTM עם משתנים גיאופוליטיים — יכולה לזהות בצורה אמינה חריגות עכירות הנגרמות מכרייה באגנים סכסוכיים ממועטי-נתונים, תוך שליטה בשונות הידרולוגית טבעית?")
      ]),
      p([
        run("RQ2: ", { bold: true }),
        run("האם משתנים גיאופוליטיים — מצב סכסוך מ-MID/ICOW, מדדי איכות ממשל, ספירת אירועי קונפליקט מ-ACLED — מספקים כוח ניבוי גדל-משמעותי לשיורי עכירות מעבר למשתנים סביבתיים — משקעים, שיפוע, כיסוי קרקע, עונתיות — בלבד?")
      ]),
      p([
        run("RQ3: ", { bold: true }),
        run("האם מודל תיאורטי-משחקים רב-סוכנים, מכויל מהיחס שיורים-הסלמה שנצפה, משחזר את עיתוי וגודל חריגות הכרייה לאורך מחזורי סכסוך היסטוריים — ובכך מספק מודל מנגנוני שיכול, לאחר אימות, לתמוך בתרחישי סיכון כרייה עתידיים?")
      ]),

      // פרק 3
      h1("3. מיצוב בספרות"),
      p([
        run("שלוש קהילות מחקריות נפרדות פיתחו את הכלים שהצעה זו משלבת, אך הן לא תקשרו ביניהן. קהילת "),
        run("חישת-מרחק וזיהוי כרייה", { bold: true }),
        run(" (Gallwey et al. 2020; Balaniuk et al. 2020; Usmanov et al. 2021) הפיקה צינורות מאומתים לזיהוי כרייה מהלוויין. מחקרים אלה מתייחסים לכרייה כבעיית סיווג כיסוי-קרקע; הם אינם מנסים להסביר מדוע כרייה מתרחשת היכן שהיא מתרחשת, ואף אחד אינו כולל משתנים גיאופוליטיים.")
      ]),
      p([
        run("קהילת "),
        run("למידת מכונה מונחית-פיזיקה לידרולוגיה", { bold: true }),
        run(" (Willard et al. 2020; Shen et al. 2023; Lu et al. 2021; Shuai et al. 2024) ביססה ארכיטקטורות חזקות לתיקון שיורי מודלי פיזיקה באמצעות ML. שואי ועמיתים (2024) הדגימו את הגישה הזו — שימוש ב-XGBoost וב-LSTM לתיקון שיורי MODFLOW — עם הממצא הקריטי שמשתנים עזר משפרים ביצועים. עם זאת, כל מחקרי מנבא-השיורים הקיימים משתמשים אך ורק במשתנים סביבתיים. אף מחקר לא הכניס משתני ממשל, מצב סכסוך, או נתוני אירועי קונפליקט למודל שיורים פיזיקה-ML.")
      ]),
      p([
        run("קהילת "),
        run("הכלכלה הפוליטית של כרייה", { bold: true }),
        run(" (Lambin & Meyfroidt 2011; Bebbington et al. 2011; Prem et al. 2020) ביססה קשרים סיבתיים בין תנאי ממשל לעצימות כרייה. פרם ועמיתים (2020) מייצגים את הגבול: DiD עם נתוני לוויין, זיהוי סיבתי של כרייה הנגרמת משינוי ממשל. אך ספרות זו אינה משתמשת בקווי בסיס מכויילים-פיזיקלית — היא משתמשת בזיהוי שינוי לוויין גולמי — ואינה מנסה מידול מנגנוני דרך תיאוריית משחקים.")
      ]),
      p([
        run("מידול "),
        run("תיאורטי-משחקים של קונפליקט משאבים", { bold: true }),
        run(" קיים ביחסים בינלאומיים (Bueno de Mesquita et al. 1985) ובהקצאת מים (Khorshidi et al. 2024). כל מודל תיאורטי-משחקים קיים משתמש במטריצות תשלום מנחות. אף אחד אינו משתמש באות פיזיקלי מלוויין כקלט אמפירי למפרט התשלום. זהו הפער הקשה ביותר לגישור והתרומה התיאורטית המשמעותית ביותר של מחקר זה.")
      ]),
      p([
        run("מחקר זה הוא הראשון ל: (1) שימוש בשיור מכויל-פיזיקלית — ולא בשינוי לוויין גולמי — כאות הזיהוי לכרייה; (2) הוספת משתנים גיאופוליטיים למנבא שיורים פיזיקה-ML; (3) יישום DiD מדורג על הסלמת סכסוך כטיפול המשפיע על תוצאה רציפה מתוקנת-פיזיקלית; ו-(4) כיול מודל תיאורטי-משחקים מדפוסי שיורים-הסלמה שנצפו.")
      ]),

      // פרק 4
      h1("4. מתודולוגיה"),
      h2("4.1 עיצוב המחקר"),
      p("המחקר משתמש בעיצוב חישובי-אמפירי מעורב המובנה כצינור בן שישה שלבים. שלבים 1–3 מייצרים את אות הזיהוי; שלבים 4–5 בוחנים את מבנהו ההסברי והסיבתי; שלב 6 מדגם את המנגנון האסטרטגי הבסיסי. הצינור מתוכנן להיות מיושם על מספר שטחי מקרה — ספציפית אגני נהרות בשטחים סכסוכיים או בסמוך להם — תוך שימוש בנתוני לוויין פתוחים, תשתית מודל הידרולוגי פתוח, ומסדי נתוני אירועי קונפליקט."),

      h2("4.2 מקורות נתונים"),
      bullet("תצלומי לוויין Sentinel-2 (ESA, רזולוציה 10 מטר, ביקור חוזר כל 5 ימים): סדרות-זמן NDTI דרך Google Earth Engine לתצפית עכירות (שלב 2)"),
      bullet("קלטי מודל SWAT: SRTM DEM, נתוני קרקע FAO, כיסוי קרקע Copernicus, שחזור אקלים ERA5. ללא תלות במד-מים חי לבניית קו הבסיס (שלב 1)"),
      bullet("משתנים גיאופוליטיים: מסד נתוני MID (Militarized Interstate Dispute), מסד ICOW לטענות טריטוריאליות, מסד אירועי קונפליקט ACLED (גיאו-מקודד, רזולוציה יומית), World Governance Indicators (שלב 4)"),
      bullet("תאריכי הסלמת סכסוך כגירוי (treatment): אירועי הסלמה מ-ACLED כזעזועי טיפול לסטודיית האירוע (שלב 5)"),
      bullet("בקרה גיאולוגית: מפות סיכוי מינרלים מלפני הסכסוכים לכלי אינסטרומנטציה לאנדוגניות (שלב 4)"),

      h2("4.3 צינור הניתוח"),
      p([run("שלב 1 — קו הבסיס הפיזיקלי (SWAT):", { bold: true }), run(" פריסת SWAT עם אזוריוּת-פרמטרים מבוססת-ML (בעקבות Bawa et al. 2025) לייצור ריכוז חלקיקים מרחביים יומי צפוי בנקודות ניטור בכל אגן מטרה. במקומות שבהם נתוני כיול אינם זמינים, יישום LSTM בייסיאני מונחה-פיזיקה חלופי (Lu et al. 2021). המודל קובע איזו עכירות תיצפה בהידרולוגיה טבעית ללא כרייה.")]),
      p([run("שלב 2 — תצפית לוויין (Sentinel-2 NDTI):", { bold: true }), run(" חישוב סדרות-זמן NDTI לכל אגן באמצעות Google Earth Engine. יישום מסיכת עננים וקומפוזיטינג זמני. פלט: אות עכירות נצפה ברזולוציה 10 מטר / 5 ימים, ממוקם לנקודות ניטור SWAT.")]),
      p([run("שלב 3 — חישוב השיור:", { bold: true }), run(" חישוב השיור החתום: NDTI נצפה פחות עכירות צפויה מ-SWAT, מנורמל לפי שונות קו הבסיס העונתי. שיורים חיוביים מציינים חלקיקים מרחביים חריגים מעל הרמה הפיזיקלית הצפויה. זהו אות הזיהוי העיקרי.")]),
      p([run("שלב 4 — מנבא שיורים ML:", { bold: true }), run(" אימון מודלי XGBoost ו-LSTM מרחבי-זמני לחיזוי השיור משתי קבוצות משתנים: (א) סביבתיים בלבד; (ב) סביבתיים + גיאופוליטיים. השוואת ביצועי המודל לבידוד התרומה השולית של המשתנים הגיאופוליטיים (RQ2). יישום ערכי SHAP לפירוק חשיבות המאפיינים.")]),
      p([run("שלב 5 — אימות סיבתי (DiD מדורג):", { bold: true }), run(" טיפול באירועי הסלמת סכסוך כזעזועי טיפול מדורגים. יישום מסגרת המגמות המקבילות (Marcus et al. 2020) לאמידת ההשפעה הסיבתית של הסלמה על שיורי עכירות, תוך שימוש באגנים סמוכים לא-סכסוכיים כקבוצת השוואה. זה מטפל ב-RQ0 וב-RQ2.")]),
      p([run("שלב 6 — מודל מנגנוני תיאורטי-משחקים:", { bold: true }), run(" הגדרת משחק רב-שחקנים שבו גורמי הכרייה בוחרים עיתוי כניסה ועצימות בהינתן מבנה תשלום המכויל מהיחס שיורים-הסלמה שנצפה (שלבים 3–5). פתרון שיווי-משקל Nash ובחינה האם עיתוי ועצימות הכרייה בשיווי-משקל משחזרים דפוסי שיורים היסטוריים (RQ3). המנגנון המאומת מאפשר בשלב הבא, לאחר אימות רטרוספקטיבי, גזירת תרחישי סיכון עתידיים.")]),

      h2("4.4 בחירת מקרי-בוחן"),
      p("אגני המטרה ייבחרו למקסום שונות בסוג הסכסוך, משטר הממשל, וסיכוי גיאולוגי, תוך עמידה בתצפיתיות Sentinel-2 (כיסוי עננים מתחת ל-40% מהחודשים). אזורי מועמדות כוללים אזורי גבול סכסוכיים בגב האמזון, מסדרון הסאהל, ודרום-מזרח אסיה. הבחירה הסופית כפופה לסקר זמינות נתונים בשנה 1."),

      // פרק 5
      h1("5. תרומות צפויות"),
      h2("5.1 תרומה תיאורטית"),
      p([
        run("מחקר זה מציג "),
        run("זיהוי חריגות שיוריות מכויל-פיזיקלית", { bold: true }),
        run(" כפרדיגמה חדשה לניטור כרייה מלוויין. גישות זיהוי קיימות מסווגות כיסוי קרקע או מודדות שינוי מקו בסיס שרירותי; מסגרת זו משתמשת במודל פיזיקלי מכויל כנגד-עובדה, ומפיקה חריגות הניתנות לפרשנות ביחידות פיזיקליות ועמידות לנוגדני-סביבה.")
      ]),
      p([
        run("שילוב "),
        run("משתנים גיאופוליטיים במנבא שיורים פיזיקה-ML", { bold: true }),
        run(" — ככל הידוע לנו, היישום הראשון מסוגו — מבסס שמשתני ממשל וקונפליקט מכילים מידע שמשתנים סביבתיים אינם לוכדים. אם מאושר, זה ממסגר מחדש את שאלת עיצוב המשתנים לניטור סביבתי: משתנים פוליטיים שייכים לצד פיזיקליים.")
      ]),
      p([
        run("מודל המנגנון "),
        run("התיאורטי-משחקים המכויל אמפירית", { bold: true }),
        run(" (שלב 6) מייצג את היישום הראשון של אותות פיזיקליים מלוויין כקלטים למידול התנהגות אסטרטגית. זה מגשר בין חישת-מרחק וספרות יחב\"ל/כלכלה פוליטית בדרך שאף אחת מהן לא ניסתה בעבר, ופותח תוכנית מחקר לתרחישי סיכון כרייה פרואקטיביים ברגע שהמנגנון הרטרוספקטיבי מאומת.")
      ]),

      h2("5.2 תרומה יישומית"),
      p("הצינור מייצר מערכת ניטור שניתנת לשכפול, בקוד פתוח, הניתנת ליישום בכל אגן עם כיסוי Sentinel-2 ומסד נתוני אירועי קונפליקט תואם. הפלטות — מפות חריגות, סדרות-זמן שיוריות, ייחוס SHAP — ניתנות לפרשנות ישירה על ידי סוכנויות אכיפה סביבתיות, עיתונאים חוקרים המכסים כרייה בשטחי קונפליקט, וגופים בינלאומיים (UNEP, יחידת פשעי סביבה של האינטרפול) המנטרים כרייה בלתי-חוקית."),

      h2("5.3 תרומה מדינית"),
      p("הזיהוי הסיבתי של הסלמת סכסוך כמניע חריגות כרייה מספק בסיס ראיות להתערבויות ממשל אנטיציפטוריות: פריסת משאבי ניטור ולחץ דיפלומטי לפני שהכרייה מתבססת. מודל המנגנון התיאורטי-משחקים, לאחר אימות, יכול לייצר מפות סיכון כרייה הסתברותיות המותנות בקלטי תרחישי קונפליקט — קלט ישיר למערכות התרעה-מוקדמת לפשע סביבתי בשטחים סכסוכיים."),

      // פרק 6
      h1("6. לוח זמנים"),
      new Table({
        width: { size: 100, type: WidthType.PERCENTAGE },
        rows: [
          tableRowHe(["תקופה", "פעילות ראשית", "אבן-דרך / תוצר"], true),
          tableRowHe(["שנה 1 — ס' א'", "בחירת מקרי-בוחן וסקר נתונים; הקמת SWAT ל-2–3 אגני פיילוט; צינור GEE ל-NDTI", "דוח בחירת אגן פיילוט; SWAT רץ לאתרי פיילוט"]),
          tableRowHe(["שנה 1 — ס' ב'", "חישוב סדרות-זמן NDTI; חישוב שיורים (שלבים 2–3); מפות חריגות ראשוניות", "מסד נתוני שיורים לאגני פיילוט; טיוטת פרק 1"]),
          tableRowHe(["שנה 2 — ס' א'", "מנבא שיורים ML (שלב 4): אימון XGBoost + LSTM; אינטגרציה משתנים גיאופוליטיים; ניתוח SHAP", "תוצאות מודל ML; מאמר כנס על שלבים 1–4"]),
          tableRowHe(["שנה 2 — ס' ב'", "אימות סיבתי (שלב 5): עיצוב DiD מדורג; בדיקות מגמות מקבילות; הרחבה לאגן מלא", "טיוטת פרק 2 (שלבים 1–5); הגשת מאמר לכתב-עת"]),
          tableRowHe(["שנה 3 — ס' א'", "מידול תיאורטי-משחקים (שלב 6): מפרט וכיול; ניתוח שיווי-משקל; בחינה-לאחור", "טיוטת פרק 3 (שלב 6); הגשת מאמר שני"]),
          tableRowHe(["שנה 3 — ס' ב'", "אינטגרציה עבודת דוקטורט; עריכה; brief מדיניות; פרסום מאגר קוד-פתוח", "הגשת עבודת דוקטורט; פרסום צינור בקוד פתוח"])
        ]
      }),

      // פרק 7
      h1("7. ביבליוגרפיה"),
      p("כל ההפניות הבאות התקבלו מ-Consensus במהלך סשן סקירת הספרות. הקישורים מובילים ישירות לדף הנייר ב-Consensus."),
      new Paragraph({ spacing: { before: 160 }, bidirectional: true }),

      bibEntry("Balaniuk, R. et al.", "2020", "Mining and Tailings Dam Detection in Satellite Imagery Using Deep Learning", "Sensors", "https://consensus.app/papers/details/4f61b0018db159b0b7dcbd924712a018/?utm_source=claude_code"),
      bibEntry("Bawa, A. et al.", "2025", "Enhancing hydrological modeling of ungauged watersheds through machine learning and physical similarity-based regionalization", "Environmental Modelling & Software", "https://consensus.app/papers/details/be29f0c59d0b5649a8fdbb8315521b97/?utm_source=claude_code"),
      bibEntry("Bebbington, A. et al.", "2011", "An Andean Avatar: Post-Neoliberal and Neoliberal Strategies for Securing the Unobtainable", "New Political Economy", "https://consensus.app/papers/details/75ec7fcb43c25ec0bbf0523458212779/?utm_source=claude_code"),
      bibEntry("Bueno de Mesquita, B. et al.", "1985", "Forecasting Political Events: The Future of Hong Kong", "Yale University Press", "https://consensus.app/papers/details/c9d678c0db1052ce820b886cf6c17819/?utm_source=claude_code"),
      bibEntry("Furlong, K. & Gleditsch, N.P. et al.", "2006", "Geographic Opportunity and Neomalthusian Willingness: Boundaries, Shared Rivers, and Conflict", "International Interactions", "https://consensus.app/papers/details/67c6fc8770525c11baabdd41cacc2383/?utm_source=claude_code"),
      bibEntry("Gallwey, J. et al.", "2020", "A Sentinel-2 based multispectral convolutional neural network for detecting artisanal small-scale mining in Ghana", "Remote Sensing of Environment", "https://consensus.app/papers/details/6fda6793d62e56a3987335d6b8ad752a/?utm_source=claude_code"),
      bibEntry("Godar, J. et al.", "2014", "Actor-specific contributions to the deforestation slowdown in the Brazilian Amazon", "PNAS", "https://consensus.app/papers/details/152b68c80f825ec9b3a40dad3968e94d/?utm_source=claude_code"),
      bibEntry("Khorshidi, M.S. et al.", "2024", "Integrating Agent-Based Modeling and Game Theory for Optimal Water Resource Allocation", "Journal of Cleaner Production", "https://consensus.app/papers/details/d944dd5ce3ab5b2a984b4a11d4adcd67/?utm_source=claude_code"),
      bibEntry("Lambin, E. & Meyfroidt, P. et al.", "2011", "Global land use change, economic globalization, and the looming land scarcity", "PNAS", "https://consensus.app/papers/details/57f9d89a6be45b95b67b7bf8e43299cc/?utm_source=claude_code"),
      bibEntry("Lu, D. et al.", "2021", "Streamflow simulation in data-scarce basins using Bayesian and physics-informed machine learning models", "Journal of Hydrometeorology", "https://consensus.app/papers/details/b5e9946283165374bb9e3b19f65cc8f6/?utm_source=claude_code"),
      bibEntry("Marcus, M. et al.", "2020", "The Role of Parallel Trends in Event Study Settings: An Application to Environmental Economics", "Journal of the Association of Environmental and Resource Economists", "https://consensus.app/papers/details/e6da3e18eecf5d9c98c76bd129983c2a/?utm_source=claude_code"),
      bibEntry("Meyfroidt, P.", "2017", "Trade-offs between environment and livelihoods: Bridging the global land use and food security discussions", "AARN: Politics & Land Use", "https://consensus.app/papers/details/ddaa703846a65edabfde8ae0c1599f3e/?utm_source=claude_code"),
      bibEntry("Prem, M. et al.", "2020", "End-of-conflict deforestation: Evidence from Colombia's peace agreement", "World Development", "https://consensus.app/papers/details/e8cefa4bf39150549f0e3fe2b101d076/?utm_source=claude_code"),
      bibEntry("Qi, J. et al.", "2020", "SWAT ungauged: Water quality modeling in the Upper Mississippi River Basin", "Journal of Hydrology", "https://consensus.app/papers/details/2756fe3ff0105abfa61fe7ef54d6d132/?utm_source=claude_code"),
      bibEntry("Shen, C. et al.", "2023", "Differentiable modelling to unify machine learning and physical models for geosciences", "Nature Reviews Earth & Environment", "https://consensus.app/papers/details/47e78cfecf5257a58908d7d599aa56a0/?utm_source=claude_code"),
      bibEntry("Shuai, G. et al.", "2024", "Comparison of Multiple Machine Learning Methods for Correcting Groundwater Levels Predicted by Physics-Based Models", "Sustainability", "https://consensus.app/papers/details/ad8ddc25de0d5ef2b6c6c67d3e95da5f/?utm_source=claude_code"),
      bibEntry("Vithya, N. et al.", "2025", "Dominance Rule in Game Theory: Resolving the Cauvery River Basin Conflict", "IJRASET", "https://consensus.app/papers/details/a57c3813392a5d12af56fc85c56bda33/?utm_source=claude_code"),
      bibEntry("Wang, C. et al.", "2024", "Distributed Hydrological Modeling With Physics-Encoded Deep Learning in the Amazon", "Water Resources Research", "https://consensus.app/papers/details/00c6128bc1ac5254beaccf21dd0ebd58/?utm_source=claude_code"),
      bibEntry("Willard, J. et al.", "2020", "Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems", "ACM Computing Surveys", "https://consensus.app/papers/details/81a68be9a0c15a76b63b76910daf89d9/?utm_source=claude_code"),

    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('doctoral_proposal_geopolitical_hebrew.docx', buffer);
  console.log('נשמר: doctoral_proposal_geopolitical_hebrew.docx');
});
