.PHONY: build prod_build clean dev_run run

TAG=$(shell git rev-parse HEAD)
COMMIT_TIME=$(shell echo \"`git show -s --format=%ci HEAD`\")
TODAY_DATE=$(shell date  +%Y%m%d)
DEV_REGISTRY='likeyiyy'

build:
	docker build -t $(DEV_REGISTRY)/mirrorweb:$(TAG) -f Dockerfile .
	docker tag $(DEV_REGISTRY)/mirrorweb:$(TAG) $(DEV_REGISTRY)/mirrorweb:latest

run:
	docker run -it --name mirrorweb \
	--net=host \
	-v /root/mirrorweb:/dist \
	-d mirrorweb \
	python3 /dist/manage.py runserver 0:8090

dev_postgres_1:
    docker run --name postgres \
    -e POSTGRES_PASSWORD=mirrors123 \
    --net=host \
    -v /opt/data/pgdata:/var/lib/postgresql/data-d \
    -d postgres

dev_run:
	docker run -it --rm --name mirrorweb \
	--net=host \
	-v .:/dist \
	--link dev_postgres_1:mysql \
	-d mirrorweb \
	python3 /dist/manage.py runserver 0:8090
