const { sheets } = require('./sheets');
const SPREADSHEET_ID = process.env.SPREADSHEET_ID;
const COUNTRY_ORDER = ['US','UK','CAN','AUS','DE','UAE'];

const esc = s => String(s ?? '').replace(/"/g, '""');
const HYPER = (url, text) => url ? `=HYPERLINK("${esc(url)}","${esc(text || 'link')}")` : '';

// get meta for a tab by title
async function getSheetMeta(title) {
  const s = sheets();
  const meta = await s.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID });
  const found = meta.data.sheets.find(sh => sh.properties.title === title);
  if (!found) throw new Error(`Sheet/tab "${title}" not found`);
  const { sheetId, gridProperties } = found.properties;
  const columnCount = gridProperties?.columnCount || 26; // default ~A:Z
  return { sheetId, columnCount };
}

// insert one row below (0-based indices)
function insertRowBelowReq(sheetId, srcRow0) {
  return {
    insertDimension: {
      range: {
        sheetId,
        dimension: 'ROWS',
        startIndex: srcRow0 + 1,
        endIndex: srcRow0 + 2,
      },
      inheritFromBefore: false
    }
  };
}

// copy ONLY FORMATTING from srcRow -> destRow across 0..columnCount
function copyFormatReq(sheetId, srcRow0, destRow0, columnCount) {
  return {
    copyPaste: {
      source: {
        sheetId,
        startRowIndex: srcRow0,
        endRowIndex: srcRow0 + 1,
        startColumnIndex: 0,
        endColumnIndex: columnCount
      },
      destination: {
        sheetId,
        startRowIndex: destRow0,
        endRowIndex: destRow0 + 1,
        startColumnIndex: 0,
        endColumnIndex: columnCount
      },
      pasteType: 'PASTE_FORMAT',
      pasteOrientation: 'NORMAL'
    }
  };
}

// run a batchUpdate
async function batchUpdate(requests) {
  const s = sheets();
  return s.spreadsheets.batchUpdate({
    spreadsheetId: SPREADSHEET_ID,
    requestBody: { requests }
  });
}


async function getNextRowFromA(title) {
  const s = sheets();
  const r = await s.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: `${title}!A3:A`,
  });
  const used = (r.data.values || []).length; // how many Nos already present from row 3 down
  return 3 + used; // next row to write (1-based)
}

// Write rows starting exactly at A{startRow}:C{startRow+rows.length-1}
async function writeRowsAt(title, startRow, rows) {
  const s = sheets();
  const endRow = startRow + rows.length - 1;
  return s.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID,
    range: `${title}!A${startRow}:C${endRow}`,
    valueInputOption: 'USER_ENTERED',
    requestBody: { values: rows },
  });
}

module.exports = { COUNTRY_ORDER, HYPER, getNextRowFromA, writeRowsAt ,getSheetMeta, insertRowBelowReq, copyFormatReq, batchUpdate };
