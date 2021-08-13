# QQBOT

基于deno的qq机器人。

## 使用

### 配置

为了保护隐私和方便使用docker-compose，因此使用环境变量进行配置。

- `es`: elastic search的地址，eg: `http://elastic:password@es:9200/chatlog/`
- `mongo`: mongo地址，eg: `mongodb://root:example@mongo:27017`
- `ws_url`: 支持onebot协议的正向websocket地址，eg: `ws://cq-http:6700?access_token=password`

#### bash

```powershell
$Env:es="http://elastic:password@es:9200/chatlog/"
$Env:mongo="mongodb://root:example@mongo:27017"
$Env:ws_url="ws://cq-http:6700?access_token=coolrc"
```

#### powershell

```bash
export es="http://elastic:passwordrc136@es:9200/chatlog/"
export mongo="mongodb://root:example@mongo:27017"
export ws_url="ws://182.254.226.153:6700?access_token=coolrc"
```

### 运行

```bash
# 直接运行
deno run --allow-all --unstable .\index.ts
# 编译
deno bundle --unstable  .\index.ts .\index.js
```

## 开发

### db

db目录下为数据库相关函数，主要用于存储聊天消息到`elasticsearch`和`mongodb`。

### plugin

plugin目录下为一个个插件函数，插件的格式为：

```js
type Plugin = {
    regex: RegExp //匹配到此正则的插件会被执行
    handler: (msg: CqMessageEvent, command: string) => Promise<QuickReply> //插件函数的主体，目前只能一次回复一条消息
    descripion: string | null //插件的描述，将会被加载到help命令里
}
```

新增一个插件函数后，需要在mod.ts里面import这个插件函数，然后在mod.ts的plugins数组里增加你的插件信息，这样就能加载了。
