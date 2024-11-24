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
sudo docker pull datamasterr/fastapi-app:latest
sudo docker run -d -p 8000:8000 --env-file /home/ubuntu/.env datamasterr/fastapi-app:latest
``` 

## 실행
```bash
sudo docker images
sudo docker ps
sudo docker ps -a
```

## 디버깅
```bash
sudo docker logs <container-name>
```
