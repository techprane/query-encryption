FROM python:3.9

#Comment

# Install necessary tools
RUN apt-get update && apt-get install -y wget

# Download and extract the .tgz file into /usr/local/lib
WORKDIR /tmp
RUN wget https://downloads.mongodb.com/linux/mongo_crypt_shared_v1-linux-x86_64-enterprise-debian12-8.0.4.tgz

RUN tar -zxvf mongo_crypt_shared_v1-linux-x86_64-enterprise-debian12-8.0.4.tgz

RUN mv /tmp/lib/mongo_crypt_v1.so /usr/local/lib/
# Update the library cache
RUN ldconfig /usr/local/lib

RUN rm -f mongo_crypt_shared_v1-linux-x86_64-enterprise-debian12-8.0.4.tgz

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

#Download the mongosh
#Install mongosh
# Install dependencies, add MongoDB repository, and install mongosh
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor && \
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] \
    https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-mongosh


CMD ["fastapi", "run", "app/main.py", "--port", "8090"]
