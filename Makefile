clean:		## delete pycache, build files
	@rm -rf deploy  
	@rm -rf layer 
	@rm -rf __pycache__

## create Docker image with requirements
docker-build:	
	cd bin; unzip -u ../chromium.zip 	
	docker-compose build
	rm -f bin/chromium

## run "src.lambda_function.lambda_handler" with docker-compose
## mapping "./tmp" and "./src" folders. 
## "event.json" file is loaded and provided to lambda function as event parameter  
lambda-run:	docker-build		
	docker-compose run lambda src.lambda_function.lambda_handler 

## prepares layer.zip archive for AWS Lambda Layer deploy 
lambda-layer-build: clean 
	rm -f layer.zip
	mkdir layer layer/python
	cp -r bin layer/.
	cd layer/bin; unzip -u ../../chromium.zip 
	pip3 install -r requirements.txt -t layer/python
	cd layer; zip -9qr layer.zip .
	cp layer/layer.zip .
	rm -rf layer

## prepares deploy.zip archive for AWS Lambda Function deploy 
lambda-function-build: clean 
	rm -f deploy.zip
	mkdir deploy 
	cp -r src deploy/.
	cd deploy; zip -9qr deploy.zip .
	cp deploy/deploy.zip .
	rm -rf deploy

lambda-function-build-update: clean
	rm -f deploy.zip
	mkdir deploy
	cp -r src deploy/.
	cd deploy; zip -9qr deploy.zip .
	cp deploy/deploy.zip .
	rm -rf deploy
	aws s3 cp deploy.zip s3://${BUCKET}/src/LeadManagementReport.zip
	aws_output=`aws lambda update-function-code  --function-name lead-management-report --s3-bucket ${BUCKET} --s3-key src/LeadManagementReport.zip`

## create CloudFormation stack with lambda function and role.
## usage:	make BUCKET=your_bucket_name create-stack 
create-stack-upload:
	aws s3 cp layer.zip s3://${BUCKET}/src/SeleniumChromiumLayer.zip
	aws s3 cp deploy.zip s3://${BUCKET}/src/LeadManagementReport.zip
	aws cloudformation create-stack --stack-name lead-management-report --template-body file://cloud.yaml --parameters ParameterKey=BucketName,ParameterValue=${BUCKET} --capabilities CAPABILITY_IAM

create-stack:
	aws s3 cp deploy.zip s3://${BUCKET}/src/LeadManagementReport.zip
	aws cloudformation create-stack --stack-name lead-management-report --template-body file://cloud.yaml --parameters ParameterKey=BucketName,ParameterValue=${BUCKET} --capabilities CAPABILITY_IAM

delete-stack:
	aws cloudformation delete-stack --stack-name lead-management-report