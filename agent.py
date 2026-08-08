from from caspian import CaspianClient
import requests
import razorpay

# Initialize your developer clients
caspian_client = CaspianClient(api_key="YOUR_CASPIAN_API_KEY")
razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY_ID", "YOUR_RAZORPAY_SECRET"))

# Simulating a basic user database to track payment states
USER_SUBSCRIPTIONS = {
    "user_whatsapp_12345": {"is_premium": False}
}

def check_payment_status(user_id):
    """Verifies if the user is on the premium tier."""
    return USER_SUBSCRIPTIONS.get(user_id, {}).get("is_premium", False)

@caspian_client.on_message(channels=["whatsapp", "email"])
def handle_incoming_agent_request(message):
    user_id = message.user_id
    channel = message.channel
    
    # 1. Enforce the monetization layer check
    if not check_payment_status(user_id):
        # Generate a sandbox payment link via Razorpay API instead of Base44 UI
        payment_link_data = {
            "amount": 49900,  # ₹499.00 INR in paise
            "currency": "INR",
            "description": "LegalEase-AI Premium Monthly Subscription",
            "customer": {"name": "LegalEase User", "contact": user_id if channel == "whatsapp" else ""},
            "notify": {"sms": False, "email": True if channel == "email" else False},
            "reminder_enable": False,
            "callback_url": f"https://{message.app_host}/razorpay-webhook",
            "callback_method": "get"
        }
        
        try:
            order = razorpay_client.payment_link.create(payment_link_data)
            short_url = order.get("short_url")
            
            # Send customized upgrade message through Caspian infrastructure
            message.reply(
                text=f"🔒 *Premium Feature Requested* \n\n"
                     f"Multi-channel automated contract review requires a premium tier account. "
                     f"Please use our Razorpay Sandbox link to activate your access instantly:\n\n"
                     f"👉 {short_url}"
            )
            return
        except Exception as e:
            message.reply(text="Monetization gateway is currently undergoing maintenance. Please try again shortly.")
            return

    # 2. Proceed to Base44 RAG processing for validated premium users
    if message.has_attachments:
        message.reply(text="⏳ Processing your legal document via Base44 Secure Engine...")
        
        document_url = message.attachments.url
        base44_endpoint = "https://base44.app"
        
        response = requests.post(base44_endpoint, json={"document_url": document_url})
        
        if response.status_code == 200:
            analysis_data = response.json()
            message.reply(text=f"📄 *Legal Analysis Report*:\n\n{analysis_data.get('summary')}")
        else:
            message.reply(text="Error extracting insights from the Base44 system layer.")
