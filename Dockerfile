FROM python:3.6

MAINTAINER asi@localhost.com

ENV PYTHONUNBUFFERED 1
ENV SECRET_KEY=""
ENV DEBUG 0
ENV ALLOWED_HOSTS=""

RUN mkdir -p /opt/matter/src
WORKDIR /opt/matter/src

RUN apt-get update && \
    apt-get upgrade -y && \ 	
    apt-get install -y \
	python3 \
	python3-pip \
	supervisor \
	nginx && \
    rm -rf /var/lib/apt/lists/*

COPY . /opt/matter/src/

RUN pip3 install -r requirements.txt

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisor.conf /etc/supervisor/conf.d/

EXPOSE 80
CMD ["supervisord", "-n"]