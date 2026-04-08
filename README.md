# 中小型企业智能财务报销系统（前后端分离）

## 一、项目结构
- backend/finance_reimbursement: Django4 + DRF 后端
- frontend: Vue3 + Element Plus 前端
- sql/smart_reimbursement.sql: MySQL建表脚本
- docs: 毕业设计文档、流程图、ER图、使用说明

## 二、后端运行
1. 进入后端目录：
   cd backend/finance_reimbursement
2. 复制环境变量：
   将 .env.example 复制为 .env 并填写 MySQL 与百度API参数
3. 安装依赖：
   pip install -r requirements.txt
4. 执行迁移：
   python manage.py makemigrations
   python manage.py migrate
5. 启动服务：
   python manage.py runserver 0.0.0.0:8000

## 三、前端运行
1. 进入前端目录：
   cd frontend
2. 安装依赖：
   npm install
3. 启动开发服务：
   npm run dev
4. 浏览器访问：
   http://127.0.0.1:5173

## 四、接口清单
- POST /api/auth/register/
- POST /api/auth/login/
- POST /api/invoice/upload-verify/
- POST /api/invoice/ocr-by-code/
- POST /api/reimbursement/save/
- GET /api/reimbursement/history/
- GET /api/dashboard/stats/

## 五、百度API接入说明
- 在后端 .env 填写 BAIDU_API_KEY 与 BAIDU_SECRET_KEY
- 验真接口要求前端提交发票基础字段
- 验真成功后才允许OCR与报销提交

## 六、说明
- 本项目为毕业设计可交付最简实现版，仅员工单角色。
- 生产环境建议补充JWT鉴权、上传白名单、安全审计与日志追踪。
