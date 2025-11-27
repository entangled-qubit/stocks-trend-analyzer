import google.generativeai as genai
import os

def get_gemini_report(prompt: str, api_key: str) -> str:
    """
    Generates a research report using Google Gemini (Flash Model).
    """
    if not api_key:
        return "⚠️ Error: Please enter a valid Gemini API Key in the sidebar."

    errors = []

    try:
        genai.configure(api_key=api_key)
        
        # 1. Try Gemini 2.5 Pro (Newest High-End)
        try:
            model = genai.GenerativeModel('gemini-2.5-pro')
            response = model.generate_content(prompt)
            return f"**🤖 Analysis by Gemini 2.5 Pro**\n\n{response.text}"
        except Exception as e:
            errors.append(f"Gemini 2.5 Pro failed: {str(e)}")

        # 2. Try Gemini 2.5 Flash (Newest Fast)
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return f"**⚡ Analysis by Gemini 2.5 Flash** (Pro model unavailable)\n\n{response.text}"
        except Exception as e:
            errors.append(f"Gemini 2.5 Flash failed: {str(e)}")

        # 3. Try Gemini 2.0 Flash (Stable Fallback)
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            return f"**⚡ Analysis by Gemini 2.0 Flash**\n\n{response.text}"
        except Exception as e:
            errors.append(f"Gemini 2.0 Flash failed: {str(e)}")

        # If all failed, list available models for debugging
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as list_err:
            available_models = [f"Could not list models: {str(list_err)}"]

        error_msg = "**⚠️ All AI Models Failed.**\n\n"
        error_msg += "**Debug Info:**\n"
        for err in errors:
            error_msg += f"- {err}\n"
        
        error_msg += "\n**Available Models for your Key:**\n"
        for m in available_models:
            error_msg += f"- {m}\n"

        return error_msg

    except Exception as e:
        return f"⚠️ Critical Error: {str(e)}"
