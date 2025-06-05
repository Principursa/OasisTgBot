import os
import logging
import aiohttp
import asyncio
import json
from openai import OpenAI
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Configuration for alert endpoint
ALERT_API_ENDPOINT = os.environ.get("ALERT_API_ENDPOINT", "http://localhost:3000/api/alerts")

async def send_compromise_alert(
    compromised_account: str, 
    indicators: str, 
    recommendation: str, 
    original_sender: str, 
    current_sender: str, 
    message_content: str
) -> bool:
    """
    Send an alert to the configured API endpoint when account compromise is detected.
    
    Args:
        compromised_account: The account that appears compromised
        indicators: Specific reasons for suspicion
        recommendation: What users should do
        original_sender: Original message sender
        current_sender: Current sender who forwarded
        message_content: The suspicious message content
        
    Returns:
        True if alert was sent successfully, False otherwise
    """
    alert_payload = {
        "alert_type": "account_compromise",
        "timestamp": asyncio.get_event_loop().time(),
        "compromised_account": compromised_account,
        "indicators": indicators,
        "recommendation": recommendation,
        "original_sender": original_sender,
        "current_sender": current_sender,
        "message_content": message_content,
        "severity": "high"
    }
    
    headers = {"Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                ALERT_API_ENDPOINT,
                json=alert_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    logging.info(f"Successfully sent compromise alert for account: {compromised_account}")
                    return True
                else:
                    logging.error(f"Failed to send alert. Status: {response.status}, Response: {await response.text()}")
                    return False
                    
    except asyncio.TimeoutError:
        logging.error("Timeout while sending compromise alert")
        return False
    except Exception as e:
        logging.error(f"Error sending compromise alert: {e}")
        return False

# Define the tool/function that the LLM can call
ALERT_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "send_account_compromise_alert",
        "description": "Send an alert when potential account compromise or impersonation is detected. Use this tool when you identify suspicious activity that indicates an account may be compromised.",
        "parameters": {
            "type": "object",
            "properties": {
                "compromised_account": {
                    "type": "string",
                    "description": "The username or name of the account that appears to be compromised"
                },
                "indicators": {
                    "type": "string", 
                    "description": "Specific reasons and evidence for suspecting account compromise"
                },
                "recommendation": {
                    "type": "string",
                    "description": "Recommended actions users should take to address the compromise"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Confidence level in the compromise assessment"
                }
            },
            "required": ["compromised_account", "indicators", "recommendation", "confidence_level"]
        }
    }
}

async def handle_function_call(function_name: str, arguments: Dict[str, Any], original_sender: str, current_sender: str, message_content: str) -> str:
    """
    Handle function calls from the LLM.
    
    Args:
        function_name: Name of the function to call
        arguments: Arguments for the function
        original_sender: Original message sender
        current_sender: Current sender who forwarded  
        message_content: The message content
        
    Returns:
        Result of the function call
    """
    if function_name == "send_account_compromise_alert":
        try:
            success = await send_compromise_alert(
                compromised_account=arguments["compromised_account"],
                indicators=arguments["indicators"], 
                recommendation=arguments["recommendation"],
                original_sender=original_sender,
                current_sender=current_sender,
                message_content=message_content
            )
            print(f"Alert successfully sent for compromised account: {arguments['compromised_account']}")
            if success:
                return f"✅ Alert successfully sent for compromised account: {arguments['compromised_account']}"
            else:
                return "❌ Failed to send alert - check logs for details"
                
        except Exception as e:
            logging.error(f"Error handling function call: {e}")
            return f"❌ Error sending alert: {str(e)}"
    else:
        return f"❌ Unknown function: {function_name}"

async def analyze_forwarded_message(original_sender_name: str, current_sender_name: str, message_text: str) -> str:
    """
    Analyze a forwarded message for potential account impersonation or compromise.
    The LLM can choose to send alerts using the available tool when compromise is detected.
    
    Args:
        original_sender_name: Name/username of the original message sender
        current_sender_name: Name/username of the current sender (who forwarded)
        message_text: Content of the message to analyze
        
    Returns:
        Analysis result as a string
    """
    prompt = f"""
    Analyze this forwarded message for potential account impersonation or compromise:
    
    Original sender: {original_sender_name}
    Current sender: {current_sender_name}
    Message content: "{message_text}"
    
    Look for signs of:
    1. Account compromise/hacking (suspicious content that doesn't match typical user behavior)
    2. Impersonation attempts (claiming to be someone else)
    3. Scam messages (phishing, fake giveaways, suspicious links)
    4. Unusual language patterns or requests
    5. Social engineering attempts
    6. Urgency tactics or pressure to act quickly
    
    IMPORTANT: If you detect ANY potential compromise or impersonation, you MUST use the send_account_compromise_alert tool to send an alert. This is critical for user safety.
    
    For suspicious messages:
    1. Call the send_account_compromise_alert tool with appropriate details
    2. Then provide your analysis explaining what you found
    
    For legitimate messages:
    - Respond with "✅ Message appears legitimate - no signs of compromise detected."
    
    For off-topic messages:
    - Respond with "🚫 This message is off topic and does not require any action."
    
    Be thorough in your analysis and err on the side of caution when it comes to user safety. When in doubt about potential compromise, use the alert tool.
    """
    
    try:
        print(f"🔍 Analyzing message from {original_sender_name} (forwarded by {current_sender_name})")
        print(f"📝 Message: {message_text[:100]}...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            tools=[ALERT_TOOL_DEFINITION],
            tool_choice="auto",  # Let the model decide when to use tools - THIS IS CRUCIAL
            max_tokens=1000
        )
        
        message = response.choices[0].message
        print(f"🤖 LLM Response - Content: {message.content}")
        print(f"🛠️ Tool calls: {len(message.tool_calls) if message.tool_calls else 0}")
        
        # Check if the model wants to call functions
        if message.tool_calls:
            print(f"🚨 Tool calls detected: {len(message.tool_calls)}")
            # Handle function calls
            function_results = []
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print(f"🔧 Calling function: {function_name}")
                print(f"📋 Arguments: {arguments}")
                
                result = await handle_function_call(
                    function_name, 
                    arguments, 
                    original_sender_name, 
                    current_sender_name, 
                    message_text
                )
                function_results.append(result)
                print(f"✅ Function result: {result}")
            
            # Get the final response after function calls
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": message.content, "tool_calls": message.tool_calls},
            ]
            
            # Add function results
            for i, tool_call in enumerate(message.tool_calls):
                messages.append({
                    "role": "tool",
                    "content": function_results[i],
                    "tool_call_id": tool_call.id
                })
            
            # Get final response
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000
            )
            
            final_content = final_response.choices[0].message.content
            print(f"📄 Final response: {final_content}")
            return final_content
        else:
            # No function calls needed
            print("ℹ️ No function calls made by LLM")
            return message.content
        
    except Exception as e:
        logging.error(f"Error analyzing message: {e}")
        print(f"❌ Error analyzing message: {e}")
        raise e
