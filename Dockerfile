FROM python:3-slim as build

# install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir option 

RUN ["playwright", "install"]

# copy all files
COPY /sdk /sdk
COPY Controller.py Controller.py
COPY main.py main.py
COPY api.py api.py

# run code
CMD ["python3", "-u", "main.py"]