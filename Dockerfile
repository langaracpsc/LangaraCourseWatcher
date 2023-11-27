FROM python:3.11-slim as build

# install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy all files
COPY . .

# run code
CMD ["python3", "-u", "main.py"]