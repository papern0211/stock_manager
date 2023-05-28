# stock_manager
my private stock manager

This project is developed based on 'python'.
'kivy' and 'kivymd' are used to make cross-platform App.

- [kivy](https://kivy.org/doc/stable/gettingstarted/intro.html)
- [kibymd](https://kivymd.readthedocs.io/en/1.1.1/)

To build APK, we used 'buildozer'
- [buildozer](https://github.com/kivy/buildozer)

Unfortunately, I failed to build APK with WSL.
I keep facing the problem so I refer to the following [guide](https://brain-nim.tistory.com/9) 

Anyway, this app provides the following functions:
- Current Status
- Budget
- Transaction history
- Editing (test phase)

## Google Sheet 연동
Google sheet 와의 연동을 위해서는 다음의 사전 작업이 필요하다
  1. Google Cloud console 접속 후 프로젝트 setup
  2. Google Sheets API와 Google Drive API 을 enable
  3. Service Account 생성 (사용자 인증 정보 만들기 -> 서비스 계정)
    - 순서대로 만듬 (option들은 대부분 생략 가능)
    - 사용자 계정 '이메일' 정보를 복사
    - 사용하고자 하는 Google Sheet 의 공유 항목에 추가
    - 사용자 인증 정보의 서비스 계정에서 '키' 추가: Json으로 생성 및 다운로드
  4. 다음의 패키지 설치
  ```bash
  pip install google-api-python-client gspread oauth2client
  ```

키정보는 노출이 되지 않도록 유의하며, 다음의 코드에서도 credentials.json 으로 따로 저장 (repository에 미포함)
