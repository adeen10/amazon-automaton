const { google } = require('googleapis');

function getAuth() {
  return new google.auth.JWT({
    email: process.env.GOOGLE_CLIENT_EMAIL,
    key: (process.env.GOOGLE_PRIVATE_KEY || '').replace(/\\n/g, '\n'),
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
}
function sheets() { return google.sheets({ version: 'v4', auth: getAuth() }); }

module.exports = { sheets };
