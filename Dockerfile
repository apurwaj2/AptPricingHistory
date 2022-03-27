FROM public.ecr.aws/lambda/python:3.6

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir bin
ADD bin /bin/

RUN chmod 755 /bin/chromedriver
# Copy function code
COPY work.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "work.entry_main" ]
