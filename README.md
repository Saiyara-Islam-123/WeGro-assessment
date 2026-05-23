To run:
->Install univcorn and fastapi using pip
->On one terminal run uvicorn main:app --reload, keep it open
->Open another terminal. If using a Windows machine run Remove-Item alias:curl
->Then run curl -X GET http://127.0.0.1:8000/{endpoint} in the second terminal
