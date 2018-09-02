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
	-p 8090:8090 \
	-v /root/mirrorweb:/dist \
	-v /opt/log/mirrors/:/opt/log/mirrors/ \
	-v /opt/web/:/opt/web/ \
	--link dev_postgres_1:postgres \
	-d likeyiyy/mirrorweb \
	python3 /dist/manage.py runserver 0:8090

dev_postgres_1:
	docker run --name dev_postgres_1 \
    -e POSTGRES_PASSWORD=mirrors123 \
	-p 5432:5432 \
    -v /opt/data/pgdata:/var/lib/postgresql/data-d \
    -d postgres

dev_run:
	docker run -it --rm --name dev_mirrorweb \
	-p 8090:8090 \
	-v /root/mirrorweb:/dist \
	-v /opt/log/mirrors/:/opt/log/mirrors/ \
	-v /opt/web/:/opt/web/ \
	--link dev_postgres_1:postgres \
	likeyiyy/mirrorweb \
	python3 /dist/manage.py runserver 0:8090
