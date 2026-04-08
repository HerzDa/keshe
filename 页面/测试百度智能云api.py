import base64
import requests

# ====================== 你的密钥 ======================
API_KEY = "W1aiwKV6XMVSTeRNwHiOcNhl"
SECRET_KEY = "wXVPljdeU29QarH5MHcm0SIc1Ka8FvJZ"


# 1. 获取 access_token
def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    response = requests.post(url, params=params)
    return response.json()["access_token"]


# 2. 读取PDF并base64编码
def get_pdf_base64(pdf_path):
    with open(pdf_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf8')


# 3. 调用增值税发票OCR（支持PDF）
def vat_invoice_recognize(pdf_path):
    access_token = get_access_token()
    request_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token={access_token}"

    pdf_base64 = get_pdf_base64(pdf_path)

    # 关键：这里用 pdf_file 而不是 image！
    params = {
        "pdf_file": pdf_base64,
        "pdf_file_num": "1"  # 识别第一页
    }

    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    return response.json()


# ====================== 测试 ======================
if __name__ == '__main__':
    pdf_path = r"C:/Users/李达/Desktop/code第三版/digital.pdf"
    result = vat_invoice_recognize(pdf_path)

    print("=" * 50)
    print("识别结果：")
    print(result)

    if "error_code" in result:
        print("\n❌ 错误：", result["error_msg"])
    else:
        print("\n✅ PDF发票识别成功！")