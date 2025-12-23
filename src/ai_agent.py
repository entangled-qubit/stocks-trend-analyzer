import google.generativeai as genai
import os

def get_gemini_report(prompt: str, api_key: str) -> str:
    """
    Generates a research report using Google Gemini.
    Uses the `google-generativeai` SDK.
    """
    if not api_key:
        return "⚠️ Error: Please enter a valid Gemini API Key in the sidebar."

    errors = []

    try:
        genai.configure(api_key=api_key)
        
        # 1. Try Gemini 1.5 Flash (Fast & Cost Effective)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return f"**⚡ Analysis by Gemini 1.5 Flash**\n\n{response.text}"
        except Exception as e:
            errors.append(f"Gemini 1.5 Flash failed: {str(e)}")

        # 2. Try Gemini 1.5 Pro (Higher Intelligence)
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            return f"**🤖 Analysis by Gemini 1.5 Pro**\n\n{response.text}"
        except Exception as e:
            errors.append(f"Gemini 1.5 Pro failed: {str(e)}")

        # 3. Try Gemini Pro (Legacy)
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return f"**⚡ Analysis by Gemini Pro**\n\n{response.text}"
        except Exception as e:
            errors.append(f"Gemini Pro failed: {str(e)}")

        error_msg = "**⚠️ All AI Models Failed.**\n\n"
        error_msg += "**Debug Info:**\n"
        for err in errors:
            error_msg += f"- {err}\n"
        
        return error_msg

    except Exception as e:
        return f"⚠️ Critical Error: {str(e)}"
