from firebase_util import get_firebase_util

class SimpleFirebaseTest:
    """
    Simple test class for Firebase utility without unittest framework.
    """
    
    def __init__(self):
        # Thay đổi access token này thành token thật từ Firebase của bạn
        self.ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjkyZTg4M2NjNDY2M2E2MzMyYWRhNmJjMWU0N2YzZmY1ZTRjOGI1ZDciLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoibmdoaWVtIGhvYW5nIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0l0ajFQeTlpQkFSWlVNWmlKUHhaOUVkQTNndjhGd1hpbnMyLU05Q2hRVzVPRW5qM3M9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc25vd3gtMzFjMzMiLCJhdWQiOiJzbm93eC0zMWMzMyIsImF1dGhfdGltZSI6MTc1NjEzNTI2NSwidXNlcl9pZCI6ImFVdVhoQkhtVE9YR0RYSHJtMldsVEJOUk1tejEiLCJzdWIiOiJhVXVYaEJIbVRPWEdEWEhybTJXbFRCTlJNbXoxIiwiaWF0IjoxNzU2MTM1MjY1LCJleHAiOjE3NTYxMzg4NjUsImVtYWlsIjoiaG9hbmdubS5kZXZAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMTY0NTY4MDM0NTI4MDU2MTE2MTYiXSwiZW1haWwiOlsiaG9hbmdubS5kZXZAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.huJgxnbgeVZEBxC2UkeJmDODaBhkRkcEHd9vFXP-K8vRX1M_93CggzvPFvPRSTEJZtJIT0So6OjYfvLaj7tP6Yfmm3dH3sqLxFtm2EAWrEmAhiQQ61ndixb-6B-nv5tzgSS2rtoiCSd37AmByrXqrV7PdOtX9dK7y9lbrXK1bDM1cYxyH2hTkHRoFgzZI5jEBJF_iWvWJ5--96yKeKY0APFHo_t8s6YY6sWEkkfFIKHYG7CCIvzPKeolSEmcC_6zlas7KjeHePEnwFcjbGm4tBZpFEMc_9C0VYkGqWxQU_K_sO-mx6YEeyDdM8cBRx1JJpUNSkKv6ZvAht1g-oTzKg"
        
        self.firebase_util = None
        self.init_firebase()
    
    def init_firebase(self):
        """Khởi tạo Firebase utility."""
        try:
            self.firebase_util = get_firebase_util()
            print("✅ Firebase đã được khởi tạo thành công")
            print(f"✅ Trạng thái kết nối: {self.firebase_util.is_connected()}")
        except Exception as e:
            print(f"❌ Lỗi khởi tạo Firebase: {e}")
            return False
        return True
    
    def test_verify_token(self):
        """Test verify access token."""
        print("\n=== TEST VERIFY ACCESS TOKEN ===")
        
        try:
            user_info = self.firebase_util.verify_access_token(self.ACCESS_TOKEN)
            
            if user_info:
                print("✅ Token hợp lệ!")
                print(f"   - UID: {user_info.get('uid')}")
                print(f"   - Email: {user_info.get('email')}")
                print(f"   - Email verified: {user_info.get('email_verified')}")
                print(f"   - Name: {user_info.get('name')}")
                return user_info
            else:
                print("❌ Token không hợp lệ hoặc đã hết hạn")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi khi verify token: {e}")
            return None
    
    def test_get_user_info(self):
        """Test lấy thông tin user từ token."""
        print("\n=== TEST GET USER INFO ===")
        
        try:
            user_data = self.firebase_util.get_user_from_token(self.ACCESS_TOKEN)
            
            if user_data:
                print("✅ Lấy thông tin user thành công!")
                print(f"   - UID: {user_data.get('uid')}")
                print(f"   - Email: {user_data.get('email')}")
                print(f"   - Name: {user_data.get('name')}")
                
                # In tất cả các field có trong user data
                print("   - Tất cả thông tin user:")
                for key, value in user_data.items():
                    if key != 'uid':  # UID đã in rồi
                        print(f"     {key}: {value}")
                
                return user_data
            else:
                print("❌ Không tìm thấy thông tin user hoặc token không hợp lệ")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin user: {e}")
            return None
    
    def test_get_user_quota(self):
        """Test lấy thông tin quota của user."""
        print("\n=== TEST GET USER QUOTA ===")
        
        try:
            quota_info = self.firebase_util.get_user_quota(self.ACCESS_TOKEN)
            
            if quota_info:
                print("✅ Lấy thông tin quota thành công!")
                print(f"Plan: {quota_info['plan']}")
                print(f"Usage: {quota_info['used']}/{quota_info['limit']}")
                print(f"Breakdown: {quota_info['usage_breakdown']}")
                
                return quota_info
            else:
                print("❌ Không lấy được thông tin quota")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi khi lấy quota: {e}")
            return None
    
    def run_all_tests(self):
        """Chạy tất cả các test."""
        print("🚀 Bắt đầu test Firebase Utility...")
        print("=" * 50)
        
        if not self.firebase_util:
            print("❌ Firebase chưa được khởi tạo, dừng test")
            return
        
        # Test 1: Verify token
        user_info = self.test_verify_token()
        
        # Test 2: Get user info
        user_data = self.test_get_user_info()
        
        # Test 3: Get user quota
        quota_info = self.test_get_user_quota()
        
        print("\n" + "=" * 50)
        print("🏁 Kết thúc test!")
        
        # Tóm tắt kết quả
        results = {
            'verify_token': user_info is not None,
            'get_user_info': user_data is not None,
            'get_user_quota': quota_info is not None
        }
        
        print("\n📊 Tóm tắt kết quả:")
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {test_name}: {status}")


# Chạy test
if __name__ == '__main__':
    print("📱 Firebase Utility Simple Test")
    print("Lưu ý: Thay đổi ACCESS_TOKEN trong class thành token thật của bạn!")
    print()
    
    # Tạo và chạy test
    test = SimpleFirebaseTest()
    test.run_all_tests()
