# Docker Images Pusher

使用Github Action将国外的Docker镜像转存到阿里云私有仓库，供国内服务器使用，免费易用<br>

- 支持DockerHub, gcr.io, k8s.io, ghcr.io等任意仓库<br>
- 支持最大40GB的大型镜像<br>
- 使用阿里云的官方线路，速度快<br>

---

## leo03w 20240830

新增 `api_hook.yaml` 带参workflow, 支持api方式启动github action, 可传 `原始镜像地址` 和 `目的镜像地址` 两个参数

- 支持 `streamlit` 形式提供web界面
- 支持 `cli.py` 命令行工具调用

## 使用方式

```bash
pip install .
```

```bash
export github_token=your_token
```

```bash
docker-image-forker --help
```

### 配置文件

在项目根目录下创建 `.env` 配置文件, 参考 `config.py` 中定义的配置项进行设置

token为必须配置, 参考
[workflow rest api doc](https://docs.github.com/zh/rest/actions/workflows?apiVersion=2022-11-28)
生成你的访问令牌, 建议 `细粒度的个人访问令牌`

配置 owner为你的github用户名, repo为你克隆此项目后的项目命名

[workflow 触发及参数文档](https://docs.github.com/zh/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#workflow_dispatch)

### todo

- [x] `cli.py` 支持单位置参数
- [ ] 外部调用 `cli.py` 配置文件读取不到问题
- [x] 镜像目标位置 名称中 `/` 替换为 `-`
- [ ] 客户端工具, 输入镜像名称, 自动从阿里云仓库克隆, 并重命名
- [ ] 封装可执行文件

---


视频教程：https://www.bilibili.com/video/BV1Zn4y19743/

作者：**[技术爬爬虾](https://github.com/tech-shrimp/me)**<br>
B站，抖音，Youtube全网同名，转载请注明作者<br>

## 使用方式

### 配置阿里云

登录阿里云容器镜像服务<br>
https://cr.console.aliyun.com/<br>
启用个人实例，创建一个命名空间（**ALIYUN_NAME_SPACE**）
![](/doc/命名空间.png)

访问凭证–>获取环境变量<br>
用户名（**ALIYUN_REGISTRY_USER**)<br>
密码（**ALIYUN_REGISTRY_PASSWORD**)<br>
仓库地址（**ALIYUN_REGISTRY**）<br>

![](/doc/用户名密码.png)

### Fork本项目

Fork本项目<br>

#### 启动Action

进入您自己的项目，点击Action，启用Github Action功能<br>

#### 配置环境变量

进入Settings->Secret and variables->Actions->New Repository secret
![](doc/配置环境变量.png)
将上一步的**四个值**<br>
ALIYUN_NAME_SPACE,ALIYUN_REGISTRY_USER，ALIYUN_REGISTRY_PASSWORD，ALIYUN_REGISTRY<br>
配置成环境变量

### 添加镜像

打开images.txt文件，添加你想要的镜像
可以加tag，也可以不用(默认latest)<br>
可添加 --platform=xxxxx 的参数指定镜像架构<br>
可使用 k8s.gcr.io/kube-state-metrics/kube-state-metrics 格式指定私库<br>
可使用 #开头作为注释<br>
![](doc/images.png)
文件提交后，自动进入Github Action构建

### 使用镜像

回到阿里云，镜像仓库，点击任意镜像，可查看镜像状态。(可以改成公开，拉取镜像免登录)
![](doc/开始使用.png)

在国内服务器pull镜像, 例如：<br>

```
docker pull registry.cn-hangzhou.aliyuncs.com/shrimp-images/alpine
```

registry.cn-hangzhou.aliyuncs.com 即 ALIYUN_REGISTRY(阿里云仓库地址)<br>
shrimp-images 即 ALIYUN_NAME_SPACE(阿里云命名空间)<br>
alpine 即 阿里云中显示的镜像名<br>

### 多架构

需要在images.txt中用 --platform=xxxxx手动指定镜像架构
指定后的架构会以前缀的形式放在镜像名字前面
![](doc/多架构.png)

### 镜像重名

程序自动判断是否存在名称相同, 但是属于不同命名空间的情况。
如果存在，会把命名空间作为前缀加在镜像名称前。
例如:

```
xhofe/alist
xiaoyaliu/alist
```

![](doc/镜像重名.png)

### 定时执行

修改/.github/workflows/docker.yaml文件
添加 schedule即可定时执行(此处cron使用UTC时区)
![](doc/定时执行.png)


## 备注

### 通过API调用后，获取run_id

https://stackoverflow.com/questions/69479400/get-run-id-after-triggering-a-github-workflow-dispatch-event

https://github.com/orgs/community/discussions/17389

## PyPi packaging

twine==6.1.0 版本太新, 导致

```bash
❯ python -m twine check dist/*
Checking dist/dock_worker-0.0.0-py3-none-any.whl: ERROR    InvalidDistribution: Invalid distribution metadata: unrecognized or malformed field 'license-file' 
```

```bash
pip install "twine<6.0" -U
```

降到 5.1.1 好了