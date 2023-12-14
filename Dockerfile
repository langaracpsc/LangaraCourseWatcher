FROM python:3-slim as build

# install requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir option 

# copy all files
COPY api.py api.py
COPY main.py main.py
COPY discord.py discord.py

# run code
CMD ["python3", "main.py"]