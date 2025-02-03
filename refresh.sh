# To be run on the host machine, to kill/refresh/restart the docker container
docker stop botbox
docker rm botbox
docker pull lxgrf/botbox:latest
docker run -d --name botbox -v $(pwd)/.env:/app/.env lxgrf/botbox:latest
