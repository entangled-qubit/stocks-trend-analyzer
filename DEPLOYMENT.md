# Deployment Guide: Indian Stock Screener

This guide will help you deploy your **Indian Stock Screener** to **Streamlit Community Cloud** for free.

## Prerequisites
1.  **GitHub Account**: You need a GitHub account to host your code.
2.  **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io/) using your GitHub account.

## Step 1: Prepare Your Code
We have already prepared the code for deployment:
-   **`requirements.txt`**: Lists all necessary libraries.
-   **`.gitignore`**: Ensures temporary files and large cache files are not uploaded.
-   **`pyperclip` fix**: Made clipboard functionality optional so it doesn't crash on the server.

## Step 2: Push to GitHub
You need to push your code to a new GitHub repository.

1.  **Create a New Repo**: Go to GitHub and create a new repository (e.g., `indian-stock-screener`).
2.  **Push Code**: Run these commands in your terminal:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin https://github.com/entangled-qubit/stocks-trend-analyzer.git
    git branch -M main
    git push -u origin main
    ```

## Step 3: Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your repository (`stocks-trend-analyzer`), branch (`main`), and main file (`app.py`).
4.  Click **"Deploy!"**.

## Step 4: Configure Secrets (API Key)
Your app needs the Gemini API key to work.

1.  Once deployed, go to your app's dashboard on Streamlit Cloud.
2.  Click the **"Settings"** (three dots) -> **"Settings"** -> **"Secrets"**.
3.  Paste your API key in the following format:
    ```toml
    GEMINI_API_KEY = "your-actual-api-key-here"
    ```
4.  Click **"Save"**.

## Step 5: First Run
1.  The app will start with an **empty cache**.
2.  Click **"🔄 Full Update"** in the sidebar.
3.  Wait for it to download data for all 2000+ stocks (this might take 2-3 minutes on the cloud).
4.  Once done, the **Instant Scanner** and **Rankings** will work perfectly!

## FAQ: Is there an APK?
Streamlit apps are **Web Applications**, so there is no standard APK file. However, you can use it like an app on your phone:

**On Android (Chrome):**
1.  Open the deployed link in Chrome.
2.  Tap the **three dots** (menu).
3.  Tap **"Add to Home screen"**.
4.  It will appear as an app icon on your phone and open in full-screen mode!

**On iOS (Safari):**
1.  Open the link in Safari.
2.  Tap the **Share** button.
3.  Tap **"Add to Home Screen"**.

## Troubleshooting
-   **"Clipboard copy failed"**: This is normal on the cloud. Use the "Copy" button if available or manually copy the text.
-   **Slow Update**: The first update is slow because it's downloading 5 years of data for 2000 stocks. Subsequent "Quick Updates" will be faster.
