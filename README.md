# syft-test

syft:
https://github.com/anchore/syft

## Install

### For Mac
```
$ brew install syft
```

check version after installed
```
$ syft --version
syft 0.85.0
```

## Command

### Scan ECR Image

#### Prerequisite

- ecr:GetAuthorizationToken
- ecr:BatchGetImage

1. Authorize

Run Dcoker Desktop in advance
```
$ aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 123456.dkr.ecr.ap-northeast-1.amazonaws.com
```

2. Pull
```
$ docker pull 123456.dkr.ecr.ap-northeast-1.amazonaws.com/sample-repository:latest
```

3. Scan by syft
```
$ syft packages <image> -o json
```