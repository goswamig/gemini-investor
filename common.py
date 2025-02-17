import gemini_investor.generic_calls
import gemini_investor.options_calls
import gemini_investor.order_calls
import gemini_investor.stock_calls
import gemini_investor
import inspect
import google.cloud.logging

from dotenv import load_dotenv
import os
import google.generativeai as genai
from gemini_toolbox import client

from google.oauth2 import service_account


MODEL_NAME="gemini-1.5-pro"

GCP_PROJECT = "gemini-trading-backend"
GCP_CREDENTAILS = service_account.Credentials.from_service_account_file(
    './sa.json')

logging_client = google.cloud.logging.Client(project=GCP_PROJECT, credentials=GCP_CREDENTAILS)
logging_client.setup_logging()


all_functions = [
                    func
                    for _, func in inspect.getmembers(gemini_investor.options_calls)
                    if inspect.isfunction(func) and func.__module__ == gemini_investor.options_calls.__name__
                ] + [
                    func
                    for _, func in inspect.getmembers(gemini_investor, inspect.isfunction)
                    if inspect.isfunction(func) and func.__module__ == gemini_investor.__name__
                ] + [
                    func
                    for _, func in inspect.getmembers(gemini_investor.generic_calls, inspect.isfunction)
                    if inspect.isfunction(func) and func.__module__ == gemini_investor.generic_calls.__name__
                ] + [
                    func
                    for _, func in inspect.getmembers(gemini_investor.stock_calls, inspect.isfunction)
                    if inspect.isfunction(func) and func.__module__ == gemini_investor.stock_calls.__name__
                ] + [
                    func
                    for _, func in inspect.getmembers(gemini_investor.order_calls, inspect.isfunction)
                    if inspect.isfunction(func) and func.__module__ == gemini_investor.order_calls.__name__
                ]

system_instruction = ["""
You are a tool for quick interaction between the user and the financial trading platform Alpaca. You possess all the knowledge about trading.

You are provided with functions to interact with the Alpaca API, with descriptions of their capabilities. Use these functions to execute requests. If a function returns an error or unexpected response, inform the user and display the received response or error.

You execute financial operations with securities, options, and currencies on behalf of the user, so your actions must be accurate and swift. Confirm the parameters of the operation with the user once.

The user interacts with you through the Telegram app, so consider this when formatting your responses.

If the user asks for raw data returned by the functions, provide it unchanged. In all other cases, provide clear, precise, and comprehensive information.

Do not overload the user with excessive trading knowledge. You are a tool for providing perfectly clear answers to the user's questions about trading and related topics.

Do not spend effort on anything unrelated to trading and trading strategy forecasting.

"""]


def create_client(user_id, function_to_send_message):
    load_dotenv()
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    copy_of_all_functions = all_functions.copy()
    copy_of_all_functions.append(function_to_send_message) 

    return client.generate_chat_client_from_functions_list(copy_of_all_functions, model_name=MODEL_NAME, debug=True, recreate_client_each_time=False, history_depth=4, system_instruction=system_instruction, do_not_die=True, add_scheduling_functions=True, gcs_bucket="gemini_jobs", gcs_blob=f"jobs_{user_id}.json")

