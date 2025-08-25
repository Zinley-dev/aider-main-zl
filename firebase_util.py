import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FirebaseUtil:
    """
    Utility class for Firebase operations including authentication and Firestore database access.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Firebase connection.
        
        Args:
            credentials_path: Path to Firebase service account JSON file.
                            If None, will automatically try to use 'snowx.json' from root path,
                            then FIREBASE_CREDENTIALS environment variable,
                            or use default application credentials as fallback.
        """
        self.app = None
        self.db = None
        self._initialize_firebase(credentials_path)
    
    def _initialize_firebase(self, credentials_path: Optional[str] = None):
        """
        Initialize Firebase Admin SDK connection.
        
        Args:
            credentials_path: Path to service account credentials file
        """
        try:
            # Check if Firebase app is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
                logger.info("Using existing Firebase app")
            else:
                # Initialize Firebase app
                if credentials_path:
                    cred = credentials.Certificate(credentials_path)
                    self.app = firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase initialized with credentials from {credentials_path}")
                elif os.getenv('FIREBASE_CREDENTIALS'):
                    cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS'))
                    self.app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with credentials from environment variable")
                else:
                    # Try to use snowx.json from root path as default
                    root_path = os.path.dirname(os.path.abspath(__file__))
                    snowx_path = os.path.join(root_path, 'snowx.json')
                    
                    if os.path.exists(snowx_path):
                        cred = credentials.Certificate(snowx_path)
                        self.app = firebase_admin.initialize_app(cred)
                        logger.info(f"Firebase initialized with default snowx.json from {snowx_path}")
                    else:
                        # Use default application credentials as fallback
                        self.app = firebase_admin.initialize_app()
                        logger.info("Firebase initialized with default application credentials")
            
            # Initialize Firestore client
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise Exception(f"Firebase initialization failed: {str(e)}")
    
    def verify_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token and return user information.
        
        Args:
            access_token: Firebase ID token to verify
            
        Returns:
            Dictionary containing user information if token is valid, None otherwise
        """
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(access_token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'auth_time': decoded_token.get('auth_time'),
                'exp': decoded_token.get('exp'),
                'iat': decoded_token.get('iat')
            }
            
            logger.info(f"Access token verified successfully for user: {user_info['uid']}")
            return user_info
            
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid access token: {str(e)}")
            return None
        except auth.ExpiredIdTokenError as e:
            logger.warning(f"Expired access token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying access token: {str(e)}")
            return None
    
    def get_user_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user data from Firestore based on access token.
        
        Args:
            access_token: Firebase ID token
            
        Returns:
            User data from Firestore if found, None otherwise
        """
        try:
            # First verify the token and get user info
            user_info = self.verify_access_token(access_token)
            if not user_info:
                return None
            
            uid = user_info['uid']
            
            # Get user document from Firestore
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['uid'] = uid  # Add UID to the data
                logger.info(f"User data retrieved successfully for UID: {uid}")
                return user_data
            else:
                logger.warning(f"User document not found for UID: {uid}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user from token: {str(e)}")
            return None
    
    def get_user_quota(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user quota information based on access token.
        
        Args:
            access_token: Firebase ID token
            
        Returns:
            Dictionary containing quota information if found, None otherwise
        """
        try:
            # Get user data first
            user_data = self.get_user_from_token(access_token)
            if not user_data:
                return None
            
            # Extract usage information
            usage = user_data.get('usage', {})
            subscription = user_data.get('subscription', {})
            
            # Determine plan based on subscription tier
            tier = subscription.get('tier', 0)
            plan_mapping = {
                0: 'free',
                1: 'plus', 
                2: 'pro'
            }
            plan = plan_mapping.get(tier, 'free')
            
            # Set limits based on plan
            limit_mapping = {
                'free': 5,
                'plus': 250,
                'pro': 500
            }
            limit = limit_mapping.get(plan, 1000)
            
            # Calculate total usage from different usage types
            total_used = (
                usage.get('prompt', 0) + 
                usage.get('deepPrompt', 0) + 
                usage.get('enhancedPrompt', 0) + 
                usage.get('flowsAction', 0)
            )
            
            # Build quota info
            quota_info = {
                'used': total_used,
                'limit': limit,
                'plan': plan,
                'tier': tier,
                'usage_breakdown': {
                    'prompt': usage.get('prompt', 0),
                    'deepPrompt': usage.get('deepPrompt', 0),
                    'enhancedPrompt': usage.get('enhancedPrompt', 0),
                    'flowsAction': usage.get('flowsAction', 0)
                },
                'subscription_status': subscription.get('status', 'inactive'),
                'subscription_expires_at': subscription.get('expiresAt'),
                'uid': user_data.get('uid')
            }
            
            logger.info(f"Quota retrieved successfully for user: {user_data.get('uid')} - Plan: {plan}, Used: {total_used}/{limit}")
            return quota_info
            
        except Exception as e:
            logger.error(f"Error getting user quota: {str(e)}")
            return None
    
    def update_user_usage(self, uid: str, usage_type: str, increment: int = 1) -> bool:
        """
        Update user usage in Firestore by incrementing specific usage type.
        
        Args:
            uid: User ID
            usage_type: Type of usage to increment ('prompt', 'deepPrompt', 'enhancedPrompt', 'flowsAction')
            increment: Amount to increment (default: 1)
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            from firebase_admin import firestore
            
            user_ref = self.db.collection('users').document(uid)
            
            # Use Firestore increment to safely update usage
            update_data = {
                f'usage.{usage_type}': firestore.Increment(increment)
            }
            
            user_ref.update(update_data)
            logger.info(f"Usage updated successfully for user: {uid} - {usage_type} +{increment}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user usage: {str(e)}")
            return False
    
    def update_user_quota(self, uid: str, quota_data: Dict[str, Any]) -> bool:
        """
        Update user quota/usage in Firestore.
        
        Args:
            uid: User ID
            quota_data: Dictionary containing quota/usage information to update
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            user_ref = self.db.collection('users').document(uid)
            
            # Support both old 'quota' format and new 'usage' format
            if 'usage' in quota_data:
                user_ref.update({'usage': quota_data['usage']})
            elif any(key in quota_data for key in ['prompt', 'deepPrompt', 'enhancedPrompt', 'flowsAction']):
                # Direct usage update
                usage_updates = {}
                for usage_type in ['prompt', 'deepPrompt', 'enhancedPrompt', 'flowsAction']:
                    if usage_type in quota_data:
                        usage_updates[f'usage.{usage_type}'] = quota_data[usage_type]
                user_ref.update(usage_updates)
            else:
                # Legacy quota update
                user_ref.update({'quota': quota_data})
            
            logger.info(f"Quota/Usage updated successfully for user: {uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user quota: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if Firebase is properly connected.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            return self.app is not None and self.db is not None
        except Exception:
            return False
    
    def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user data directly by UID.
        
        Args:
            uid: User ID
            
        Returns:
            User data if found, None otherwise
        """
        try:
            user_ref = self.db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['uid'] = uid
                return user_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by UID: {str(e)}")
            return None


# Global instance for easy access
firebase_util = None

def get_firebase_util(credentials_path: Optional[str] = None) -> FirebaseUtil:
    """
    Get or create a global FirebaseUtil instance.
    
    Args:
        credentials_path: Path to Firebase credentials file
        
    Returns:
        FirebaseUtil instance
    """
    global firebase_util
    if firebase_util is None:
        firebase_util = FirebaseUtil(credentials_path)
    return firebase_util
