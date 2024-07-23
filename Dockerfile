FROM python:3.8

COPY revspotify /app
WORKDIR /app

RUN apt-get update -y
RUN pip3 install -U setuptools
RUN apt-get install -y libssl-dev libffi-dev 
RUN apt-get install -y libxml2-dev libxslt1-dev zlib1g-dev 
RUN apt-get install -y ffmpeg
RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]