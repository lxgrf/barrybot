docker build -t lxbot:latest . 
docker tag lxbot:latest lxgrf/botbox:latest
docker push lxgrf/botbox:latest