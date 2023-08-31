import openai, os

openai.api_key = os.environ["OPENAI_KEY"]

def openai_completion(input, sc_num):
    retries = 3
    retry_cnt = 0
    backoff_time = 3
    while retry_cnt <= retries:
        try:
        #Make your OpenAI API request here
            completions = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=input,
                # top_p=0.5
                temperature=0.7,
                n=sc_num
                # stop=["Q:"]
            )
            return completions
        except openai.error.Timeout as e:
            #Handle timeout error, e.g. retry or log
            print(f"OpenAI API request timed out: {e}")        
        except openai.error.APIError as e:
            #Handle API error, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
        except openai.error.APIConnectionError as e:
            #Handle connection error, e.g. check network or log
            print(f"OpenAI API request failed to connect: {e}")
        except openai.error.InvalidRequestError as e:
            #Handle invalid request error, e.g. validate parameters or log
            print(f"OpenAI API request was invalid: {e}")
        except openai.error.AuthenticationError as e:
            #Handle authentication error, e.g. check credentials or log
            print(f"OpenAI API request was not authorized: {e}")
        except openai.error.PermissionError as e:
            #Handle permission error, e.g. check scope or log
            print(f"OpenAI API request was not permitted: {e}")
        except openai.error.RateLimitError as e:
            #Handle rate limit error, e.g. wait or log
            print(f"OpenAI API request exceeded rate limit: {e}")
        
        print(f"Retrying in {backoff_time} seconds...")
        time.sleep(backoff_time)
        backoff_time *= 1.5

    return None