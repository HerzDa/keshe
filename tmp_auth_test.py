import requests
base='http://127.0.0.1:8000/api'
emp='E_TEST_01'
pwd='123456'
reg=requests.post(base+'/auth/register/',json={'employee_no':emp,'name':'测试','phone':'13800000000','password':pwd},timeout=15)
print('register',reg.status_code,reg.text)
login=requests.post(base+'/auth/login/',json={'employee_no':emp,'password':pwd},timeout=15)
print('login',login.status_code,login.text)
