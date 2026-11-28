@echo off
REM Chay ca 3 crawler: lua gao, ho tieu, ca phe
REM File nay dung cho Windows Task Scheduler de tu dong crawl hang ngay

cd /d "%~dp0"

echo [%date% %time%] Bat dau crawl gia lua gao ...
python rice\crawl_rice.py

echo [%date% %time%] Bat dau crawl gia ho tieu ...
python pepper\crawl_pepper.py

echo [%date% %time%] Bat dau crawl gia ca phe ...
python coffee\crawl_coffee.py

echo [%date% %time%] Dang nap du lieu vao CSDL ...
cd /d "%~dp0..\db"
python load_crawler_data.py

echo [%date% %time%] Dang lay du lieu thoi tiet (NASA POWER) ...
python "%~dp0..\data_external\fetch_weather_data.py"

python "%~dp0..\..\ml\models\generate_forecast.py"
echo [%date% %time%] Hoan tat crawl du lieu ngay hom nay.