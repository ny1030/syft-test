import boto3
import re
import subprocess
import json
import csv
from datetime import datetime

def list_matching_ecr_images(account_id, repository_pattern, tag_pattern, profile_name):
    # Create an ECR client by specifying a profile
    session = boto3.Session(profile_name=profile_name)
    ecr_client = session.client('ecr', region_name='ap-northeast-1')

    matching_images = []

    # Get a list of ECR repositories
    response = ecr_client.describe_repositories(registryId=account_id)
    #print(response)

    # Search for matching images by repository
    for repository in response['repositories']:
        repository_name = repository['repositoryName']

        # Check if the repository name matches the specified partial match pattern
        if re.search(repository_pattern, repository_name):
            # Get a list of images in the repository
            image_response = ecr_client.describe_images(repositoryName=repository_name, registryId=account_id)

            # Search for matching tags per image
            for image_detail in image_response['imageDetails']:
                image_tags = image_detail['imageTags'] if 'imageTags' in image_detail else []
                for tag in image_tags:
                    if re.match(tag_pattern, tag):
                        image_uri = f"{account_id}.dkr.ecr.ap-northeast-1.amazonaws.com/{repository_name}:{tag}"
                        matching_images.append(image_uri)

    return matching_images


def pull_docker_image(image_uri):
    # Pull Docker image
    cmd = f"docker pull {image_uri}"
    subprocess.run(cmd, shell=True)

def syft_analyze(image_uri, csv_writer):
    # Execute syft command
    cmd = f"syft packages {image_uri} -o json"
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    output_json = result.stdout.strip()
    if output_json:
        try:
            packages_data = json.loads(output_json)
            # Narrow down to matches where artifacts[].name is node or go or java
            filtered_packages = [{'name': pkg['name'], 'version': pkg['version']} for pkg in packages_data.get('artifacts', []) if 'name' in pkg and pkg['name'] in ['node', 'go', 'java'] and 'version' in pkg]
            for pkg in filtered_packages:
                csv_writer.writerow({'image_uri': image_uri.replace(f"{account_id}.dkr.ecr.ap-northeast-1.amazonaws.com/", ""), 'name': pkg['name'], 'version': pkg['version']})
        except json.JSONDecodeError as e:
            print("JSONデータのパースに失敗しました。")
            print(e)

# Get ECR image by specifying pattern
account_id = 'XXXXXXX'
repository_pattern = r'xxxxxxx'  # Specify a partial match pattern
tag_pattern = r'^latest$'
profile_name = 'xxxxxx'  # Specify the profile name configured in AWS CLI
matching_images = list_matching_ecr_images(account_id, repository_pattern, tag_pattern, profile_name)

# Output results to CSV file
today = datetime.today().strftime('%Y%m%d')
csv_file_name = f"{account_id}_{today}.csv"

with open(csv_file_name, 'w', newline='') as csvfile:
    fieldnames = ['image_uri', 'name', 'version']
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csv_writer.writeheader()

    # Pull Docker image and run syft command
    for image_uri in matching_images:
        print(f"Processing image: {image_uri}")
        pull_docker_image(image_uri)
        syft_analyze(image_uri, csv_writer)
