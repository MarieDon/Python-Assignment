#!/usr/bin/python
import boto3
from subprocess import *
import time
import datetime

ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')


def create_instance(url):

    userdata = """#!/bin/bash
        yum update -y
        yum install httpd -y
        systemctl enable httpd
        systemctl start httpd
        echo "<h2>Marie's test page</h2>Instance ID: " > /var/www/html/index.html
        curl --silent http://169.254.169.254/latest/meta-data/instance-id/ >> /var/www/html/index.html
        echo "<br>Availability zone: " >> /var/www/html/index.html
        curl --silent http://169.254.169.254/latest/meta-data/placement/availability-zone/ >> /var/www/html/index.html
        echo "<br>IP address: " >> /var/www/html/index.html
        curl --silent http://169.254.169.254/latest/meta-data/public-ipv4 >> /var/www/html/index.html
        echo "<hr>Here is an image that I have stored on S3: <br>" >> /var/www/html/index.html
        echo "<img src="%s">" >> /var/www/html/index.html""" %url



    instance = ec2.create_instances(
        ImageId = 'ami-0fad7378adf284ce0',
        KeyName="maries_key",
        SecurityGroups=['group'],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags':[
                    {
                        'Key': 'Name',
                        'Value': 'Assignment'
                    },
                ]
            }
        ],
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
        UserData=userdata
    )

    print("Loading...")
    instance[0].wait_until_running()
    time.sleep(20)
    instance[0].reload()
    dns_name = instance[0].public_dns_name
    print("DNS: "+dns_name)
    print("Instance ID: "+instance[0].id)
    return dns_name


def scp_file(dns_name):
    try:
        run('ssh -t -o StrictHostKeyChecking=no -i /home/marie/maries_key.pem ec2-user@'+dns_name+' sudo yum install python3 -y', check=True, shell=True)
        run('scp -i /home/marie/maries_key.pem check_webserver.py ec2-user@'+dns_name+':.', check=True, shell=True)
        run('ssh -i /home/marie/maries_key.pem ec2-user@'+dns_name+' python3 check_webserver.py', check=True, shell=True)

    except CalledProcessError:
        print("Something is broken")
        run('ssh -t -o StrictHostKeyChecking=no -i /home/marie/maries_key.pem ec2-user@'+dns_name+' sudo yum install python3 -y', shell=True)
        run('scp -i /home/marie/maries_key.pem check_webserver.py ec2-user@'+dns_name+':.', check=True, shell=True)
        run('ssh -i /home/marie/maries_key.pem ec2-user@'+dns_name+' python3 check_webserver.py', check=True, shell=True)


def creating_bucket(pybucket):
        now = datetime.datetime.now()
        random = str(now.microsecond)
        pybucket = pybucket+"-"+ random
        image = "image.jpeg"

        try:
            response1 = s3.create_bucket(Bucket=pybucket, CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'})
            print(response1)
            response2 = s3.Object(pybucket, image).put(ACL= 'public-read', ContentType='image/jpeg', Body=open(image, 'rb') )
            print (response2)
            return "https://s3-eu-west-1.amazonaws.com/"+pybucket+"/image.jpeg"
        except Exception as error:
            print(error)


def main():
     # Ask user to name their bucket
    name_input = input("Please name your bucket in lowercase letters:  ")
    # Makes sure bucket name is in lowecase letters
    bucketName = name_input.lower()
    # Creates bucket, bucket name is then being passed in and gives back a url
    url = creating_bucket(bucketName)
    dns_name = create_instance(url)
    scp_file(dns_name)


# This is the boilerplate that calls the main() function
if __name__ == '__main__':
    main()
