@echo off
"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%~dp0..\.dart_tool\chrome-test-profile" --disable-crash-reporter %*
