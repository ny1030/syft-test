import boto3
import re
import subprocess
import json

def list_matching_ecr_images(account_id, repository_pattern, tag_pattern, profile_name):
    # プロファイルを指定してECRのクライアントを作成
    session = boto3.Session(profile_name=profile_name)
    ecr_client = session.client('ecr', region_name='ap-northeast-1')

    matching_images = []

    # ECRリポジトリの一覧を取得
    response = ecr_client.describe_repositories(registryId=account_id)
    #print(response)

    # リポジトリごとに一致するイメージを検索
    for repository in response['repositories']:
        repository_name = repository['repositoryName']

        # リポジトリ名が指定した部分一致のパターンに一致するかチェック
        if re.search(repository_pattern, repository_name):
            # リポジトリのイメージ一覧を取得
            image_response = ecr_client.describe_images(repositoryName=repository_name, registryId=account_id)

            # イメージごとに一致するタグを検索
            for image_detail in image_response['imageDetails']:
                image_tags = image_detail['imageTags'] if 'imageTags' in image_detail else []
                for tag in image_tags:
                    if re.match(tag_pattern, tag):
                        image_uri = f"{account_id}.dkr.ecr.ap-northeast-1.amazonaws.com/{repository_name}:{tag}"
                        matching_images.append(image_uri)

    return matching_images


def pull_docker_image(image_uri):
    # Dockerイメージをpull
    cmd = f"docker pull {image_uri}"
    subprocess.run(cmd, shell=True)

def syft_analyze(image_uri):
    # syftコマンドを実行
    cmd = f"syft packages {image_uri} -o json"
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

    # syftの結果をJSON形式にパース
    output_json = result.stdout.strip()
    if output_json:
        try:
            packages_data = json.loads(output_json)
            print("Syft analysis result:")
            # artifacts[].nameがnodeかgoで一致するものに絞り込み
            filtered_packages = [{'name': pkg['name'], 'version': pkg['version']} for pkg in packages_data.get('artifacts', []) if 'name' in pkg and pkg['name'] in ['java', 'go', 'node'] and 'version' in pkg]
            print(json.dumps({'artifacts': filtered_packages}, indent=2))
        except json.JSONDecodeError as e:
            print("JSONデータのパースに失敗しました。")
            print(e)

# パターンを指定してECRのイメージを取得
account_id = '599453524280'
repository_pattern = r'test'  # 部分一致のパターンを指定
tag_pattern = r'^latest$'
profile_name = 'frit'  # AWS CLIで設定したプロファイル名を指定
matching_images = list_matching_ecr_images(account_id, repository_pattern, tag_pattern, profile_name)

# Dockerイメージをpullしてsyftコマンドを実行
for image_uri in matching_images:
    print(f"Processing image: {image_uri}")
    pull_docker_image(image_uri)
    syft_analyze(image_uri)