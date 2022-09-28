FROM python:3.8-buster
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN chmod +x /app/entrypoint.sh
EXPOSE 8000
RUN mkdir static
RUN python manage.py collectstatic
ENTRYPOINT ["/app/entrypoint.sh"]
