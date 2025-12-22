# 使用官方 Node.js 运行时作为基础镜像
FROM docker.io/library/node:18-alpine
# 设置工作目录
WORKDIR /usr/src/app

# 复制 package.json 和 package-lock.json (如果存在)
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 启动应用
CMD [ "node", "server.js" ]
