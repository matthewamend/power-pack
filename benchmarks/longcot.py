import time
import longcot  #only new implemnetation
from openai import OpenAI #SENDSTO MODEL

from power_pack import Acquisition, NIDaqConfig, RunReader

API_URL = "http://localhost:8080/v1"
API_KEY = "..."
#Ithink the code requires a password?
qnum = 2  # change to 50 after the test run works

#local host talks to itself
# IF PORTS DONT MATCH, code cant find the server ( change it to match llama server


def main():
    questions = longcot.load_questions(domain="logic", difficulty="easy")[:qnum] #loaded from the longcot git
    client = OpenAI(api_key=API_KEY, base_url=API_URL, timeout=3600) #sets up connection to the ai model

    config = NIDaqConfig(2000, 1000, "longcot.hdf5")
    acq = Acquisition("LongCoT Benchmark", config)  #creates the power recorder using those settings

    marks = []  # when each question starts, so it shows as a line on the graph
 # STEP 1: start measuring power
    acq.start()
    start = time.time()
    try:
       # step 2: wait 5 seconds before so the powerpack can boot
        time.sleep(5)  # idle baseline
        for q in questions:

          #STEP 3: ask the AI each question
            marks.append(time.time() - start)
            result = client.chat.completions.create( model="",
              messages=[{"role": "user", "content": q.prompt}], #q sent
                max_tokens=16384,
            )
            answer = result.choices[0].message.content or ""
            tokens = result.usage.completion_tokens
            try:
                correct = longcot.verify(q, answer) #is answer right or wrong
            except Exception:
                correct = "error"
            print(q.question_id, "tokens:", tokens, "correct:", correct)
    finally:
      #STEP 4: stop measuring power 
        acq.stop()
#save all data and make graphs.
    reader = RunReader("longcot.hdf5")
    reader.make_csv_files("longcot-")
    reader.plot_all("longcot-", vertical_asymptotes=marks)


if __name__ == "__main__":
    main()
