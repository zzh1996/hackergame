FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=conf.settings.docker
ENV TZ=Asia/Shanghai
RUN mkdir /var/log/django
WORKDIR /opt/hackergame
COPY requirements.txt /opt/hackergame/
RUN pip install -r requirements.txt && pip install uwsgi
COPY entrypoint.sh manage.py /opt/hackergame/
COPY conf /opt/hackergame/conf
COPY frontend /opt/hackergame/frontend
COPY server /opt/hackergame/server
CMD ["./entrypoint.sh"]
