FROM public.ecr.aws/lambda/python:3.6

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN yum install -y wget
RUN wget https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
RUN wget https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-53/stable-headless-chromium-amazonlinux-2017-03.zip

RUN yum install -y unzip
RUN unzip chromedriver_linux64.zip -d /bin
RUN unzip stable-headless-chromium-amazonlinux-2017-03.zip -d /bin
RUN rm stable-headless-chromium-amazonlinux-2017-03.zip chromedriver_linux64.zip

RUN chmod 755 /bin/chromedriver

COPY ~/Downloads/ec2_micro_avana.pem ${LAMBDA_TASK_ROOT}
COPY entrypoiny.sh ${LAMBDA_TASK_ROOT}

# Copy function code
COPY work.py ${LAMBDA_TASK_ROOT}


# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD ./entrypoiny.sh
