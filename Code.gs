// ==========================================
// ⚙️ Code.gs (Ver 5.7: [2026-02-07] 当日送信救済版)
// ==========================================
const DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1466771292807102657/7WBua-A8ptgLat_t-m-1qYEppmtej50KMP3aK3ZPx6HblqJ5JhUPjQeb3JEAHYKe1Iti';

const WARNING_FOOTER = `
━━━━━━━━━━━━━━
**※終演時間はあくまで予想ですので、最終的な判断はご自身で行ってください。**

**【⚠️ 禁無断転載・漏洩厳禁】**
本情報の著作権は当オンラインサロン『稼タク』に帰属します。
許可なく外部（SNS、ブログ、他媒体）へ転載・共有することは固く禁じます。
漏洩が発覚した際は、ログに基づき個人を特定し、法的措置を講じます。
━━━━━━━━━━━━━━`;

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡️タクシー機能') 
    .addItem('🚀 稼タク イベントエディター', 'showSidebar') 
    .addSeparator()
    .addItem('📨 [手動] 明日の分をDiscordに送信', 'sendDailyEvents') 
    // [2026-02-07] 🦁 付け足し：昨日のトリガー失敗時などの救済用
    .addItem('🚨 [緊急] 今日の分をDiscordに送信', 'sendTodayEvents') 
    .addToUi();
}

function showSidebar() {
  const html = HtmlService.createTemplateFromFile('Sidebar');
  html.venues = getUrlList(); 
  html.initialDate = Utilities.formatDate(new Date(), "JST", "yyyy-MM-dd");
  const display = html.evaluate().setTitle('巡回エディター Final改').setWidth(480);
  SpreadsheetApp.getUi().showSidebar(display);
}

// Sidebar初期化用データ取得
function getInitData() {
  return {
    list: getUrlList(),
    history: getRecentDetails(),
    today: Utilities.formatDate(new Date(), "JST", "yyyy-MM-dd")
  };
}

function registerEvent(payload) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('シート1');
  const year = new Date().getFullYear();
  const startDate = new Date(year + "/" + payload.startDate.split('(')[0]);
  const endDate = payload.endDate ? new Date(year + "/" + payload.endDate.split('(')[0]) : startDate;
  
  let finalVenue = payload.venue;
  if (payload.subVenue) finalVenue += "(" + payload.subVenue + ")";

  // 重複チェック用データ取得
  let existingData = [];
  if (sheet.getLastRow() > 1) {
    existingData = sheet.getRange(2, 1, sheet.getLastRow() - 1, 3).getValues();
  }

  let current = new Date(startDate);
  let duplicateCount = 0;

  while (current <= endDate) {
    const currentDateStr = Utilities.formatDate(current, "JST", "yyyy/MM/dd");
    const isDuplicate = existingData.some(row => {
      const rowDate = row[0] instanceof Date ? Utilities.formatDate(row[0], "JST", "yyyy/MM/dd") : row[0];
      let rowTime = row[1];
      if (rowTime instanceof Date) rowTime = Utilities.formatDate(rowTime, "JST", "HH:mm");
      rowTime = String(rowTime); 
      return rowDate === currentDateStr && rowTime === payload.endTime && row[2] === finalVenue;
    });

    if (!isDuplicate) {
      sheet.appendRow([
        new Date(current), 
        payload.endTime, 
        finalVenue, 
        payload.detail, 
        payload.price, 
        payload.isHot, 
        payload.isPickup, 
        payload.note || "", // 備考
        "" // チェックボックス用
      ]);
      sheet.getRange(sheet.getLastRow(), 6, 1, 2).insertCheckboxes();
    } else {
      duplicateCount++;
    }
    current.setDate(current.getDate() + 1);
  }
  if (duplicateCount > 0) return "DUPLICATE";
  return "OK";
}

function saveGlobalInfo(payload) {
  let ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('共通情報');
  if (!sheet) { sheet = ss.insertSheet('共通情報'); sheet.appendRow(['日付', '高速道路情報', 'ETC工事情報']); }
  
  const year = new Date().getFullYear();
  const startDate = new Date(year + "/" + payload.startDate.split('(')[0]);
  const endDate = payload.endDate ? new Date(year + "/" + payload.endDate.split('(')[0]) : startDate;
  
  let current = new Date(startDate);
  let count = 0;
  while (current <= endDate) {
    const dateKey = Utilities.formatDate(current, "JST", "yyyy/MM/dd");
    const data = sheet.getDataRange().getValues();
    let foundRow = -1;
    for (let i = 1; i < data.length; i++) {
      let d = data[i][0] instanceof Date ? Utilities.formatDate(data[i][0], "JST", "yyyy/MM/dd") : data[i][0];
      if (d === dateKey) { foundRow = i + 1; break; }
    }
    if (foundRow > 0) {
      sheet.getRange(foundRow, 2, 1, 2).setValues([[payload.highway, payload.etc]]);
    } else {
      sheet.appendRow([new Date(current), payload.highway, payload.etc]);
    }
    current.setDate(current.getDate() + 1);
    count++;
  }
  return `✅ 期間(${count}日分)に交通情報を保存`;
}

function getGlobalInfo(dateStr) {
  if (!dateStr) return {highway: "", etc: ""};
  let ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('共通情報');
  if (!sheet) return {highway: "", etc: ""};
  const year = new Date().getFullYear();
  const dateKey = Utilities.formatDate(new Date(year + "/" + dateStr.split('(')[0]), "JST", "yyyy/MM/dd");
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    let d = data[i][0] instanceof Date ? Utilities.formatDate(data[i][0], "JST", "yyyy/MM/dd") : data[i][0];
    if (d === dateKey) return {highway: data[i][1], etc: data[i][2]};
  }
  return {highway: "", etc: ""};
}

function getUrlList() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('URLリスト');
  const data = sheet.getDataRange().getValues();
  return data.slice(1).filter(r => r[0] && r[1]).map(r => ({ name: r[0], url: r[1], halls: r[2] ? String(r[2]).split(',') : [] }));
}

function undoLastAction() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('シート1');
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) { sheet.deleteRow(lastRow); return "🗑️ 1件削除しました"; }
  return "削除対象なし";
}

function sendDailyEvents() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('シート1'); 
  const data = sheet.getDataRange().getValues();
  
  const targetDate = new Date();
  targetDate.setDate(targetDate.getDate() + 1); // +1日（明日）
  targetDate.setHours(0, 0, 0, 0);

  let events = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (!row[0]) continue;
    const date = new Date(row[0]);
    date.setHours(0, 0, 0, 0);

    if (date.getTime() === targetDate.getTime()) {
      let tStr = row[1];
      if (tStr instanceof Date) tStr = Utilities.formatDate(tStr, "JST", "HH:mm");
      let note = (row.length > 7) ? row[7] : "";

      events.push({ 
        time: tStr, 
        venue: row[2], 
        detail: row[3], 
        price: row[4], 
        isHot: row[5], 
        isPickup: row[6],
        note: note
      });
    }
  }

  events.sort((a, b) => (a.time > b.time ? 1 : -1));

  let pickups = [];
  let timelines = [];
  events.forEach(e => {
    let line = `${e.time} ｜ ${e.venue}`;
    let infoParts = [];
    if (e.detail) infoParts.push(e.detail);
    if (e.price) infoParts.push('¥' + e.price);
    if (e.isHot) infoParts.push('❗️');
    
    if (infoParts.length > 0) line += ` (${infoParts.join(' ')})`;
    if (e.note && e.note !== "") {
      line += ` ｜ ${e.note}`;
    }

    if (e.isPickup) pickups.push(line); else timelines.push(line);
  });

  const dateStr = Utilities.formatDate(targetDate, "JST", "M/d(E)");
  const gInfo = getGlobalInfo(dateStr);
  const weatherText = getWeatherWithRetry(); 
  
  const dayStr = Utilities.formatDate(targetDate, 'Asia/Tokyo', 'M/d');
  const weekDays = ['日', '月', '火', '水', '木', '金', '土'];
  const weekStr = weekDays[targetDate.getDay()];
  
  let message = `**[明日] ${dayStr} ${weekStr}**\n${weatherText}\n\n`;
  if (pickups.length > 0) message += `**[ピックアップ]**\n` + pickups.join('\n') + `\n\n`;
  if (timelines.length > 0) message += `**[時刻表（終演順）]**\n` + timelines.join('\n');
  else message += `(明日の登録イベントはありません)`;
  
  if (gInfo.highway || gInfo.etc) {
    message += `\n\n**⚠️重要交通情報**`;
    if (gInfo.highway) {
      message += `\n【高速通行止・規制】\n` + formatToList(gInfo.highway);
    }
    if (gInfo.etc) {
      message += `\n【ETC工事・その他】\n` + formatToList(gInfo.etc);
    }
  }

  // ▼▼▼ 🦁 今回の修正: 指定URLに差し替え ▼▼▼
  message += `\n\n🌐 **高速道路・工事情報はこちら**\nhttps://www.shutoko-construction.jp/traffictime/`;
  // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

  message += `\n\n` + WARNING_FOOTER;
  sendToDiscord(message);
}

function formatToList(text) {
  if (!text) return "";
  let lines = text.split(/\r\n|\n|\r/);
  let result = "";
  lines.forEach(line => {
    let trimLine = line.trim();
    if (trimLine !== "") {
      result += "・" + trimLine + "\n";
    }
  });
  return result.trim();
}

function getWeatherWithRetry() {
  const maxRetries = 5; 
  const waitTime = 5000; 
  for (let i = 0; i < maxRetries; i++) {
    try {
      const res = UrlFetchApp.fetch("https://api.open-meteo.com/v1/forecast?latitude=35.6895&longitude=139.6917&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo", {muteHttpExceptions: true});
      if (res.getResponseCode() !== 200) throw new Error("Status: " + res.getResponseCode());
      const json = JSON.parse(res.getContentText());
      if (!json.daily) throw new Error("データ形式不正");

      const code = json.daily.weathercode[1]; 
      const maxT = json.daily.temperature_2m_max[1];
      const minT = json.daily.temperature_2m_min[1];

      let icon = (code <= 3) ? "☀️" : (code <= 67) ? "☔" : "☁️"; 
      if (code >= 95) icon = "⛈️";
      return `【天気】${icon} 最高:${maxT}℃ / 最低:${minT}℃`;
    } catch (e) {
      console.log(`天気取得失敗(トライ${i+1}/${maxRetries}): ${e.toString()}`);
      if (i < maxRetries - 1) Utilities.sleep(waitTime); 
    }
  }
  return "【天気】(取得できませんでした)";
}

function getRecentDetails() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('シート1');
  if (sheet.getLastRow() <= 1) return [];
  const data = sheet.getRange(2, 4, sheet.getLastRow() - 1, 1).getValues();
  const details = data.map(r => r[0]).filter(d => d && String(d).trim() !== "");
  const unique = [...new Set(details.reverse())];
  return unique.slice(0, 50);
}

function sendToDiscord(text) {
  UrlFetchApp.fetch(DISCORD_WEBHOOK_URL, { "method": "post", "contentType": "application/json", "payload": JSON.stringify({ "content": text }) });
}

// 念のため残している空関数（HTML側から呼ばれる可能性があるため）
function getExistingEvents(venue) {
  return [];
}

// ============================================================
// 🦁 [2026-02-07] 付け足し: 緊急用「今日の分」送信関数
// サニーさんの20年来の伝統（レガシー保持）に従い、既存関数を消さずに足しました。
// ============================================================
function sendTodayEvents() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('シート1'); 
  const data = sheet.getDataRange().getValues();
  
  const targetDate = new Date(); // 🦁 今日の日付（+1せず現在のまま）
  targetDate.setHours(0, 0, 0, 0);

  let events = [];
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (!row[0]) continue;
    const date = new Date(row[0]);
    date.setHours(0, 0, 0, 0);
    if (date.getTime() === targetDate.getTime()) {
      let tStr = row[1];
      if (tStr instanceof Date) tStr = Utilities.formatDate(tStr, "JST", "HH:mm");
      let note = (row.length > 7) ? row[7] : "";
      events.push({ time: tStr, venue: row[2], detail: row[3], price: row[4], isHot: row[5], isPickup: row[6], note: note });
    }
  }
  events.sort((a, b) => (a.time > b.time ? 1 : -1));

  let pickups = [], timelines = [];
  events.forEach(e => {
    let line = `${e.time} ｜ ${e.venue}`;
    let info = [];
    if (e.detail) info.push(e.detail);
    if (e.price) info.push('¥' + e.price);
    if (e.isHot) info.push('❗️');
    if (info.length > 0) line += ` (${info.join(' ')})`;
    if (e.note) line += ` ｜ ${e.note}`;
    if (e.isPickup) pickups.push(line); else timelines.push(line);
  });

  const weatherText = getTodayWeather(); // 🦁 今日専用の天気取得
  const dayStr = Utilities.formatDate(targetDate, 'Asia/Tokyo', 'M/d');
  const weekStr = ['日','月','火','水','木','金','土'][targetDate.getDay()];
  const gInfo = getGlobalInfo(Utilities.formatDate(targetDate, "JST", "M/d(E)"));
  
  let message = `**[本日] ${dayStr} ${weekStr}**\n${weatherText}\n\n`;
  if (pickups.length > 0) message += `**[ピックアップ]**\n` + pickups.join('\n') + `\n\n`;
  if (timelines.length > 0) message += `**[時刻表（終演順）]**\n` + timelines.join('\n');
  else message += `(本日の登録イベントはありません)`;

  if (gInfo.highway || gInfo.etc) {
    message += `\n\n**⚠️重要交通情報**`;
    if (gInfo.highway) message += `\n【高速通行止・規制】\n` + formatToList(gInfo.highway);
    if (gInfo.etc) message += `\n【ETC工事・その他】\n` + formatToList(gInfo.etc);
  }
  message += `\n\n🌐 **高速道路・工事情報はこちら**\nhttps://www.shutoko-construction.jp/traffictime/`;
  message += `\n\n` + WARNING_FOOTER;
  sendToDiscord(message);
}

// 🦁 今日用の天気取得（index [0] を参照）
function getTodayWeather() {
  try {
    const res = UrlFetchApp.fetch("https://api.open-meteo.com/v1/forecast?latitude=35.6895&longitude=139.6917&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo");
    const json = JSON.parse(res.getContentText());
    const code = json.daily.weathercode[0]; // 今日
    const maxT = json.daily.temperature_2m_max[0];
    const minT = json.daily.temperature_2m_min[0];
    let icon = (code <= 3) ? "☀️" : (code <= 67) ? "☔" : "☁️";
    if (code >= 95) icon = "⛈️";
    return `【天気】${icon} 最高:${maxT}℃ / 最低:${minT}℃`;
  } catch (e) { return "【天気】(取得できませんでした)"; }
}