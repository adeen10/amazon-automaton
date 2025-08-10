# 📦 Fullstack fillout page for Google Sheets Automation App

This repository is a **monorepo** containing both the frontend and backend for an application that writes structured product data into Google Sheets.  
The backend exposes a simple API that the frontend calls to submit data for storage.

---

## 📂 Project Structure

```
project-root/
  apps/
    frontend/       # React/Vite/Next.js frontend (replace with your stack)
    backend/        # Node.js + Express backend with Google Sheets API integration
```

---

## 🚀 Getting Started

### 1️⃣ Clone the repository
```bash
git clone https://github.com/adeen10/amazon-automaton.git
cd amazon-automaton
```

### 2️⃣ Install dependencies

**Frontend**
```bash
cd apps/frontend
npm install
```

**Backend**
```bash
cd apps/backend
npm install
```

---

## ⚙️ Environment Variables

You’ll need `.env` files in **both** the frontend and backend directories.  
The backend `.env` is required for Google Sheets API access.

---

### 📄 `apps/backend/.env.example`
```env
PORT=4000
SPREADSHEET_ID=your_google_sheet_id
GOOGLE_CLIENT_EMAIL=your_service_account_email
GOOGLE_PRIVATE_KEY=your_private_key
```

---

### 📄 `apps/frontend/.env.example`
```env
VITE_API_URL=http://localhost:4000/api
```

---

**❗ Never commit real `.env` files**.  
Copy the `.env.example` file to `.env` and fill in your actual values.

Example:
```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
```

---

## 🖥 Development

**Backend**
```bash
cd apps/backend
npm run dev
```
Runs Express API on `http://localhost:4000`.

**Frontend**
```bash
cd apps/frontend
npm run dev
```
Runs frontend dev server (usually `http://localhost:5173` or `http://localhost:3000` depending on your framework).

---

## 📦 Build for Production

**Frontend**
```bash
cd apps/frontend
npm run build
```

**Backend**
```bash
cd apps/backend
npm run build
```

---

## 🔌 API Documentation

### `GET /api/health`
Checks if backend is running.

**Response**
```json
{ "ok": true }
```

---

### `POST /api/submissions`
Writes product data to the Google Sheet.

**Request Body**
```json
{
  "brands": [
    {
      "brand": "Brand A",
      "countries": [
        {
          "name": "US",
          "products": [
            {
              "url": "https://example.com/product1",
              "productname": "Product 1",
              "keyword": "keyword1",
              "categoryUrl": "https://example.com/category"
            }
          ]
        }
      ]
    }
  ]
}
```

**Response**
```json
{
  "ok": true,
  "results": [
    {
      "country": "US",
      "added": 1,
      "fromNo": 1,
      "toNo": 1
    }
  ]
}
```

---

## 🛠 Tech Stack

**Frontend**
- React / Vite (or your chosen frontend framework)
- Fetch/Axios for API calls

**Backend**
- Node.js + Express
- Google Sheets API (via `googleapis` package)
- Modular routes & controllers

---

## 📜 License
This project is licensed under the MIT License.

---

## 📧 Contact
For questions or collaboration, reach out at **adeen2002@gmail.com**.
