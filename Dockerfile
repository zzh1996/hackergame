FROM python:3.7
COPY . /opt/hackergame
WORKDIR /opt/hackergame
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=conf.settings.docker
RUN pip install -r requirements.txt && pip install uwsgi
RUN mkdir /var/log/django
CMD ["./entrypoint.sh"]
