@echo off
echo Installing LDR Telegram Bot Dependencies...
echo.

REM Create virtual environment (optional but recommended)
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python packages...
pip install -r requirements.txt

REM Create .env file from template if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo Please edit .env file and add your BOT_TOKEN!
    echo Get your token from @BotFather on Telegram
) else (
    echo .env file already exists
)

echo.
echo Setup complete! 
echo.
echo Next steps:
echo 1. Edit .env file and add your BOT_TOKEN
echo 2. Add images to the images/ folder
echo 3. Update bot_data.json with your personal data
echo 4. Run: python buttons.py
echo.
pause
