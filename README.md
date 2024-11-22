# Future Wise BE

## 개요
FastAPI를 활용하여 fund, customer API 만들기

## 기능
- http://<public-ip>:8000/docs 참고

## 종속성 설치
```bash
pipenv install -r requirements.txt
```

## 도커 명령어 (arm -> amd 아키텍처용)
```bash
docker buildx build --platform linux/amd64 -t datamasterr/fastapi-app:latest . --load
docker buildx build --platform linux/amd64 -t datamasterr/fastapi-app:latest . --push
```
```bash
docker buildx build --platform linux/amd64 -t datamasterr/fastapi-app:latest . --load
docker buildx build --platform linux/amd64 -t datamasterr/fastapi-app:latest . --push
``` 

## 실행
```bash
ollama serve
ollama pull qwen2.5:1.5b
streamlit run app.py
``` 
