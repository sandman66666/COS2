# Google OAuth Setup Guide

## Setting up Google OAuth for Strategic Intelligence System

To enable Google OAuth login and Gmail access, you need to configure OAuth credentials in Google Cloud Console.

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API and Google+ API

### Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type
3. Fill in the required information:
   - **App name**: Strategic Intelligence System
   - **User support email**: Your email
   - **Developer contact information**: Your email

### Step 3: Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application**
4. Configure the settings:

   **Name**: Strategic Intelligence System
   
   **Authorized JavaScript origins**:
   ```
   http://localhost:8080
   ```
   
   **Authorized redirect URIs**:
   ```
   http://localhost:8080/api/auth/callback
   http://localhost:8080/auth/callback
   ```

5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### Step 4: Set Environment Variables

Create a `.env` file in your project root with:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/api/auth/callback

# Other required variables
SECRET_KEY=your_secure_secret_key
API_PORT=8080
```

### Step 5: Enable Required APIs

In Google Cloud Console, enable these APIs:
1. **Gmail API** - For email access
2. **Google+ API** - For user profile information
3. **Calendar API** - For calendar access (Google adds this automatically)

### Step 6: Test the OAuth Flow

1. Start your application: `python3 app.py`
2. Go to: `http://localhost:8080/auth/google`
3. You should be redirected to Google's OAuth consent screen

### Important Notes

- **Port 8080**: Make sure both your app and Google Cloud Console are configured for port 8080
- **Localhost Only**: This setup is for development. For production, use your actual domain
- **Scopes**: The app requests access to Gmail and user profile information

### Troubleshooting

**Error: "redirect_uri_mismatch"**
- Make sure the redirect URI in Google Cloud Console exactly matches: `http://localhost:8080/api/auth/callback`

**Error: "invalid_client"**
- Check that your GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct

**Error: "access_denied"**
- The user denied access or the OAuth consent screen needs to be properly configured

### Current OAuth Endpoints

- **Login**: `http://localhost:8080/login`
- **Google OAuth Start**: `http://localhost:8080/auth/google`
- **OAuth Callback**: `http://localhost:8080/api/auth/callback`
- **Dashboard (No Auth)**: `http://localhost:8080/dashboard` 